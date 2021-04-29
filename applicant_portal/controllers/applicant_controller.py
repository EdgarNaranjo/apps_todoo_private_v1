# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, http, _
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.addons.payment.controllers.portal import PaymentProcessing
from odoo.addons.portal.controllers.mail import _message_post_helper
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager
from odoo.osv import expression


class CustomerPortal(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super(CustomerPortal, self)._prepare_portal_layout_values()

        HRApplicant = request.env['hr.applicant']
        applicant_count = HRApplicant.search_count([
            ('email_from', '=', request.env.user.login)
        ])
        values.update({
            'applicant_count': applicant_count,
        })
        return values

    @http.route(['/my/application', '/my/application/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_applicant(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        HRApplicant = request.env['hr.applicant']

        domain = [
            ('email_from', '=', request.env.user.login)
        ]

        searchbar_sortings = {
            'date': {'label': _('Create Date'), 'order': 'create_date desc'},
            'name': {'label': _('Reference'), 'order': 'name'},
            'stage': {'label': _('Stage'), 'order': 'stage_id'},
        }

        # default sortby order
        if not sortby:
            sortby = 'date'
        sort_order = searchbar_sortings[sortby]['order']

        archive_groups = self._get_archive_groups('hr.applicant', domain)
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # count for pager
        applicant_count = HRApplicant.search_count(domain)
        # make pager
        pager = portal_pager(
            url="/my/application",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=applicant_count,
            page=page,
            step=self._items_per_page
        )
        # search the count to display, according to the pager data
        applications = HRApplicant.search(domain, order=sort_order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_applications_history'] = applications.ids[:100]

        values.update({
            'date': date_begin,
            'applications': applications.sudo(),
            'page_name': 'application',
            'pager': pager,
            'archive_groups': archive_groups,
            'default_url': '/my/application',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render("applicant_portal.portal_my_applications", values)

    @http.route(['/my/application/<int:application>'], type='http', auth="user", website=True)
    def portal_my_applicant_details(self, application=None):
        application = request.env['hr.applicant'].browse([application])
        try:
            application.check_access_rights('read')
            application.check_access_rule('read')
        except AccessError:
            return request.website.render("website.403")

        return request.render("applicant_portal.portal_my_application_details", {
            'application': application.sudo(),
        })
