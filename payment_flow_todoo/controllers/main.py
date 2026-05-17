# Copyright 2025-TODAY Todooweb (www.todooweb.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
import werkzeug

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class FlowController(http.Controller):

    @http.route([
        '/payment/flow/notify/<model("payment.provider"):provider_id>',
    ], type='http', auth='none', methods=['POST'], csrf=False)
    def flow_validate_data(self, provider_id=None, **post):
        tx_data = request.env['payment.provider'].sudo().flow_getTransaction(post)
        request.env['payment.transaction'].sudo()._process('flow', tx_data)
        return ''

    @http.route([
        '/payment/flow/return/<model("payment.provider"):provider_id>',
    ], type='http', auth='public', csrf=False, website=True)
    def flow_form_feedback(self, provider_id=None, **post):
        if not provider_id:
            return werkzeug.utils.redirect('/payment/status')
        tx_data = provider_id.flow_getTransaction(post)
        request.env['payment.transaction'].sudo()._process('flow', tx_data)
        return werkzeug.utils.redirect('/payment/status')

    @http.route(['/payment/flow/redirect'], type='http', auth='public', methods=['POST'], csrf=False, website=True)
    def redirect_flow(self, **post):
        provider_id = int(post.get('provider_id'))
        acquirer = request.env['payment.provider'].browse(provider_id)
        result = acquirer.flow_initTransaction(post)
        if result.token:
            return werkzeug.utils.redirect(result.url + '?token=' + result.token)
        return werkzeug.utils.redirect('/payment/status')
