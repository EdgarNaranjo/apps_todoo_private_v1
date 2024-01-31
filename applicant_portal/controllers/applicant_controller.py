# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import datetime
import werkzeug.urls

from collections import OrderedDict
from werkzeug.exceptions import NotFound

from odoo import fields
from odoo import http
from odoo.addons.http_routing.models.ir_http import slug, unslug
from odoo.addons.website.models.ir_http import sitemap_qs2dom
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.website_partner.controllers.main import WebsitePartnerPage
from odoo.exceptions import ValidationError, AccessError, MissingError, UserError, AccessDenied
from odoo.http import content_disposition, Controller, request, route

from odoo.tools.translate import _


class WebsiteAccount(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super()._prepare_portal_layout_values()
        HRApplicant = request.env['hr.applicant']
        applicant_count = HRApplicant.search_count([
            ('email_from', '=', request.env.user.login)
        ])
        values.update({
            'applicant_count': applicant_count,
        })
        return values

    @route(['/my/application'], type='http', auth='user', website=True)
    def portal_my_applicant(self, redirect=None, page=1, date_begin=None, date_end=None, sortby=None, **post):
        values = self._prepare_portal_layout_values()
        HRApplicant = request.env['hr.applicant']
        domain = [
            ('email_from', '=', request.env.user.login)
        ]
        searchbar_sortings = {
            'date': {'label': _('Create Date'), 'order': 'create_date desc'},
            'name': {'label': _('Reference'), 'order': 'name'},
            'stage': {'label': _('Stage'), 'order': 'stage_id'},
            'department': {'label': _('Department'), 'order': 'department_id'},
            'user': {'label': _('User'), 'order': 'user_id'},
        }

        # default sortby order
        if not sortby:
            sortby = 'date'
        sort_order = searchbar_sortings[sortby]['order']

        # archive_groups = self._get_archive_groups('hr.applicant', domain)
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # count for pager
        applicant_count = HRApplicant.search_count(domain)
        # search the count to display, according to the pager data
        applications = HRApplicant.search(domain, order=sort_order, limit=self._items_per_page)
        request.session['my_applications_history'] = applications.ids[:100]

        values.update({
            'date': date_begin,
            'applications': applications.sudo(),
            'page_name': 'application',
            'default_url': '/my/application',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })

        response = request.render("applicant_portal.portal_my_applications", values)
        return response

    @route(['/my/application/<int:application>'], type='http', auth="user", website=True)
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
