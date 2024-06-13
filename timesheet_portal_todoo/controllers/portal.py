# -*- coding: utf-8 -*-

import math
from collections import OrderedDict
from dateutil.relativedelta import relativedelta
from operator import itemgetter

from odoo import fields, http, _
from odoo.http import request
from datetime import datetime
from odoo.tools import date_utils, groupby as groupbyelem
from odoo.tools import float_round
from odoo.exceptions import ValidationError
from odoo.osv.expression import AND
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.addons.hr_timesheet.controllers.portal import TimesheetCustomerPortal


def time_to_float(hour, minute):
    return float_round(hour + minute / 60, precision_digits=2)


class TimesheetCustomerPortal(TimesheetCustomerPortal):
    def _get_searchbar_sortings(self):
        return {
            'date': {'label': _('Newest'), 'order': 'date desc'},
            'employee': {'label': _('Employee'), 'order': 'employee_id'},
            'project': {'label': _('Project'), 'order': 'project_id'},
            'task': {'label': _('Task'), 'order': 'task_id'},
            'name': {'label': _('Description'), 'order': 'name'},
            'status': {'label': _('Status'), 'order': 'validated_status'},
        }

    @http.route(['/my/timesheets', '/my/timesheets/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_timesheets(self, page=1, sortby=None, filterby=None, search=None, search_in='all', groupby='none',
                             **kw):
        Timesheet = request.env['account.analytic.line']
        domain = Timesheet._timesheet_get_portal_domain()
        if request.env.user.share:
            domain += ([('user_id', '=', request.env.user.id)])
        Timesheet_sudo = Timesheet.sudo()
        values = self._prepare_portal_layout_values()
        _items_per_page = 100

        searchbar_sortings = self._get_searchbar_sortings()

        searchbar_inputs = self._get_searchbar_inputs()

        searchbar_groupby = self._get_searchbar_groupby()

        today = fields.Date.today()
        quarter_start, quarter_end = date_utils.get_quarter(today)
        last_week = today + relativedelta(weeks=-1)
        last_month = today + relativedelta(months=-1)
        last_year = today + relativedelta(years=-1)

        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
            'today': {'label': _('Today'), 'domain': [("date", "=", today)]},
            'week': {'label': _('This week'), 'domain': [('date', '>=', date_utils.start_of(today, "week")),
                                                         ('date', '<=', date_utils.end_of(today, 'week'))]},
            'month': {'label': _('This month'), 'domain': [('date', '>=', date_utils.start_of(today, 'month')),
                                                           ('date', '<=', date_utils.end_of(today, 'month'))]},
            'year': {'label': _('This year'), 'domain': [('date', '>=', date_utils.start_of(today, 'year')),
                                                         ('date', '<=', date_utils.end_of(today, 'year'))]},
            'quarter': {'label': _('This Quarter'),
                        'domain': [('date', '>=', quarter_start), ('date', '<=', quarter_end)]},
            'last_week': {'label': _('Last week'), 'domain': [('date', '>=', date_utils.start_of(last_week, "week")),
                                                              ('date', '<=', date_utils.end_of(last_week, 'week'))]},
            'last_month': {'label': _('Last month'),
                           'domain': [('date', '>=', date_utils.start_of(last_month, 'month')),
                                      ('date', '<=', date_utils.end_of(last_month, 'month'))]},
            'last_year': {'label': _('Last year'), 'domain': [('date', '>=', date_utils.start_of(last_year, 'year')),
                                                              ('date', '<=', date_utils.end_of(last_year, 'year'))]},
            'validated': {'label': _('Status Validated'), 'domain': [('validated', '=', True)]},
            'draft': {'label': _('Satus Draft'), 'domain': [('validated', '=', False)]},
        }
        # default sort by value
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']
        # default filter by value
        if not filterby:
            filterby = 'all'
        domain = AND([domain, searchbar_filters[filterby]['domain']])

        if search and search_in:
            domain += self._get_search_domain(search_in, search)

        timesheet_count = Timesheet_sudo.search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/timesheets",
            url_args={'sortby': sortby, 'search_in': search_in, 'search': search, 'filterby': filterby,
                      'groupby': groupby},
            total=timesheet_count,
            page=page,
            step=_items_per_page
        )

        def get_timesheets():
            groupby_mapping = self._get_groupby_mapping()
            field = groupby_mapping.get(groupby, None)
            orderby = '%s, %s' % (field, order) if field else order
            timesheets = Timesheet_sudo.search(domain, order=orderby, limit=_items_per_page, offset=pager['offset'])
            if field:
                if groupby == 'date':
                    raw_timesheets_group = Timesheet_sudo._read_group(
                        domain, ['date:day'], ['unit_amount:sum', 'id:recordset']
                    )
                    grouped_timesheets = [(records, unit_amount) for __, unit_amount, records in raw_timesheets_group]

                else:
                    time_data = Timesheet_sudo._read_group(domain, [field], ['unit_amount:sum'])
                    mapped_time = {field.id: unit_amount for field, unit_amount in time_data}
                    grouped_timesheets = [(Timesheet_sudo.concat(*g), mapped_time[k.id]) for k, g in
                                          groupbyelem(timesheets, itemgetter(field))]
                return timesheets, grouped_timesheets

            grouped_timesheets = [(
                timesheets,
                sum(Timesheet_sudo.search(domain).mapped('unit_amount'))
            )] if timesheets else []
            return timesheets, grouped_timesheets

        timesheets, grouped_timesheets = get_timesheets()

        values.update({
            'timesheets': timesheets,
            'grouped_timesheets': grouped_timesheets,
            'page_name': 'timesheet',
            'default_url': '/my/timesheets',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'search_in': search_in,
            'search': search,
            'sortby': sortby,
            'groupby': groupby,
            'searchbar_inputs': searchbar_inputs,
            'searchbar_groupby': searchbar_groupby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
            'is_uom_day': request.env['account.analytic.line']._is_timesheet_encode_uom_day(),
        })
        return request.render("hr_timesheet.portal_my_timesheets", values)


class WebsiteTimesheet(http.Controller):

    @http.route(['/timesheet/form'], type='http', auth="user", website=True)
    def timesheet_create(self, **kw):
        project_id = False
        if kw.get('project'):
            project_id = request.env['project.project'].search([('id', '=', kw.get('project'))])

        task_id = False
        if kw.get('task_id'):
            task_id = request.env['project.task'].search([('id', '=', int(kw.get('task_id')))])

        date_str = kw.get('date')

        try:
            formatted_date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError as e:
            print(f"Error parsing date: {e}")
            formatted_date = False
        try:
            fractional, time = math.modf(float(kw.get('duration').replace(":", ".")))
            float_time = time_to_float(time, int(float_round(fractional, 2) * (10**2)))
            vals = {
                'user_id': request.env.user.id,
                'project_id': project_id.id if project_id else task_id.project_id.id,
                'task_id': task_id.id if task_id else False,
                'date': formatted_date if 'formatted_date' in locals() else False,
                'unit_amount': float_time,
                'name': kw.get('description')
            }
            request.env['account.analytic.line'].sudo().create(vals)
            return request.redirect('/my/timesheets?groupby=none')
        except:
            raise ValidationError(_('Timesheet is not created.'))

    @http.route(['/timesheet/form/project'], type='json', auth="public", methods=['POST'], website=True, csrf=False)
    def project_infos(self, **kw):
        project_id = kw.get('project_id')
        Task = http.request.env['project.task']
        tasks = False
        if project_id:
            tasks = Task.search([('project_id', '=', int(project_id))])

        values = {}
        values['datas'] = request.env['ir.ui.view']._render_template(
            "timesheet_portal_todoo.md_portal_task", {
                'tasks': tasks,
            })
        values['datas1'] = request.env['ir.ui.view']._render_template(
            "timesheet_portal_todoo.md_portal_task_inline", {
                'tasks': tasks,
            })
        return values

    @http.route(['/my/delete_timesheet'], type='http', auth="user", website=True)
    def timesheet_delete(self, **kw):
        try:
            request.env['account.analytic.line'].sudo().search([('id', '=', kw.get('timesheet_delete'))]).unlink()
            return request.redirect('/my/timesheets?groupby=none')
        except:
            raise ValidationError(_('Timesheet is not deleted.'))

    @http.route(['/my/edit_timesheet'], type='http', auth="user", website=True)
    def timesheet_edit(self, **kw):
        t_date = datetime.strptime(kw.get('date'), "%Y-%m-%d")
        timesheet_date = fields.Date.to_string(t_date)
        try:
            fractional, time = math.modf(float(kw.get('duration').replace(":", ".")))
            float_time = time_to_float(time, int(float_round(fractional, 2) * (10**2)))
            vals = {
                'date': timesheet_date,
                'unit_amount': float_time,
                'name': kw.get('description')
            }
            request.env['account.analytic.line'].sudo().search([('id', '=', int(kw.get('timesheet_edit')))]).write(vals)
            return request.redirect('/my/timesheets?groupby=none')
        except:
            raise ValidationError(_('Timesheet is not edited.'))
