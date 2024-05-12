# -*- coding: utf-8 -*-
import logging
import pprint

import werkzeug

from odoo import http
from odoo.exceptions import ValidationError
from odoo.http import request

_logger = logging.getLogger(__name__)

try:
    import urllib3

    pool = urllib3.PoolManager()
except:
    pass


class FlowController(http.Controller):
    _accept_url = '/payment/flow/test/accept'
    _decline_url = '/payment/flow/test/decline'
    _exception_url = '/payment/flow/test/exception'
    _cancel_url = '/payment/flow/test/cancel'

    @http.route([
        '/payment/flow/notify/<string:provider_id>',
        '/payment/flow/test/notify',
    ], type='http', auth='public', methods=['GET', 'POST'], csrf=False, save_session=False)
    def flow_validate_data(self, provider_id, **post):
        _logger.info("flow_validate_data ==> Handling redirection from APS with data:\n%s", pprint.pformat(post))

        _logger.info("flow_validate_data ==> Handling redirection from APS with data:\n%s",
                     pprint.pformat(request.session))

        # uid = request.env['res.users'].authenticate(request.db, 'admin', 'admin', {'interactive': False})
        # _logger.info("UID ==> %s", uid)

        tx_data = False
        if post.get('token', False):
            tx_data = request.env['payment.provider'].sudo().flow_getTransaction(provider_id, post)
            _logger.info("flow_validate_data ==> Handling redirection from tx_data:\n%s", pprint.pformat(tx_data))

        if not tx_data:
            raise ValidationError("Transacción no esperada")

        return ''

    @http.route([
        '/payment/flow/return/<string:provider_id>',
        '/payment/flow/test/return',
    ], type='http', auth='public', methods=['GET', 'POST'], csrf=False, save_session=False)
    def flow_form_feedback(self, provider_id, **post):
        if not provider_id:
            return

        tx_data = request.env['payment.provider'].sudo().flow_getTransaction(provider_id, post)
        tx_data._token = post['token']

        _logger.info("flow_form_feedback ==> TX data:\n%s", pprint.pformat(tx_data))
        tx_sudo = request.env['payment.transaction'].sudo()._get_tx_from_notification_data(
            'flow', tx_data
        )
        _logger.info("flow_form_feedback ==> TX Sudo:\n%s", pprint.pformat(tx_sudo))
        tx_sudo._handle_notification_data('flow', tx_data)

        return request.redirect('/payment/status')

    @http.route([
        '/payment/flow/final',
        '/payment/flow/test/final',
    ], type='http', auth='none', csrf=False, website=True)
    def final(self, **post):
        return request.redirect('/payment/status')

    @http.route(['/payment/flow/redirect'], type='http', auth='public', methods=["POST"], csrf=False, website=True)
    def redirect_flow(self, **post):
        _logger.info("Handling redirection from APS with data:\n%s", pprint.pformat(post))
        provider_id = int(post.get('provider_id'))
        acquirer = request.env['payment.provider'].browse(provider_id)
        result = acquirer.flow_initTransaction(post)
        if result.token:
            return werkzeug.utils.redirect(result.url + '?token=' + result.token)
