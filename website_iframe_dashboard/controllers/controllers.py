# # -*- coding: utf-8 -*-
#
from odoo import http, _
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.exceptions import AccessError
from odoo.http import request
from odoo.tools import consteq


class WebsiteAccount(CustomerPortal):

    def _prepare_portal_layout_values(self):
        response = super(WebsiteAccount, self)._prepare_portal_layout_values()
        portal_dashboard = request.env['portal.dashboard']
        dashboard_count = portal_dashboard.search_count([('active', '=', True)])
        # dashboard
        portal_dashboard = portal_dashboard.search([('active', '=', True)])
        response.update({
            'dashboard_count': dashboard_count,
            'portal_dashboard': portal_dashboard,
        })
        return response

    @http.route(['/my/dashboard', '/my/dashboard/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_dashboard(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        PortalDashboard = request.env['portal.dashboard']
        dashbs = ''
        # dashboard
        dashboard_partner = PortalDashboard.search([
            ('message_partner_ids', 'child_of', [partner.commercial_partner_id.id])
        ])
        pager = ''
        if dashboard_partner:
            for dash in dashboard_partner:
                active = dash.active
            domain = [('active', '=', active)]
            dashboard_count = PortalDashboard.search_count(domain)
            # make pager
            pager = request.website.pager(
                url="/my/dashboard",
                url_args={'date_begin': date_begin, 'date_end': date_end},
                total=dashboard_count,
                page=page,
                step=self._items_per_page
            )
            # search the count to display, according to the pager data
            dashbs = PortalDashboard.search(domain, limit=self._items_per_page, offset=pager['offset'])
        if date_begin and date_end:
            domain += [('create_date', '>=', date_begin), ('create_date', '<=', date_end)]
        values.update({
            'date': date_begin,
            'date_end': date_end,
            'dashbs': dashbs,
            'pager': pager,
            'default_url': '/my/dashboard',
        })
        return request.render("website_iframe_dashboard.portal_my_dashboard", values)
