# -*- coding: utf-8 -*-

import uuid
import logging
import requests, json
import random

from odoo import models, api

headers = {
    'content-type': 'application/json',
    'charset': 'utf-8',
    'tp-authorization': 'Version=2.0',
    'tp-application-id': '',
    'tp-application-name': '',
    'tp-application-version': '',
    'tp-express-acceptor-id': '',
    'tp-express-account-id': '',
    'tp-express-account-token': '',
    'tp-request-id': '',
}

_logger = logging.getLogger(__name__)


class PosVantivTransaction(models.Model):
    _inherit = 'pos_vantiv_tripos_cloud.transaction'

    @api.model
    def do_refund(self, data):
        print('data ', data)
        lane = self.env['pos_vantiv_tripos_cloud.lane'].search(
            [('id', '=', data.get('lane_id'))], limit=1)
        # print('lane', lane)
        if not lane.exists():
            return "not setup"

        _logger.info("Vantiv Lane {} ".format(lane.name))
        # Payment request
        body = {}
        body['laneId'] = lane.lane_id
        body['transactionAmount'] = data.get('amount_total')
        body['ReferenceNumber'] = random.randint(1, 101) * 5
        body['TicketNumber'] = random.randint(1, 101) * 5

        # print(body)
        guid = uuid.uuid4()

        config_obj = lane.configuration_id

        headers = {
            'User-agent': 'Mozilla/5.0',
            'accept': 'application/json',
            'content-type': 'application/json',
            'charset': 'utf-8',
            'tp-authorization': 'Version=2.0',
            'tp-application-id': config_obj.express_api_credentials_application_id,
            'tp-application-name': config_obj.express_api_credentials_application_name,
            'tp-application-version': config_obj.express_api_credentials_application_version,
            'tp-express-acceptor-id': config_obj.express_api_credentials_acceptor_id,
            'tp-express-account-id': config_obj.express_api_credentials_account_id,
            'tp-express-account-token': config_obj.express_api_credentials_account_token,
            'tp-request-id': str(guid)
        }

        base_url = "https://triposcert.vantiv.com/api/v1/refund"
        if config_obj.is_production:
            base_url = "https://tripos.vantiv.com/api/v1/refund"

        try:
            r = requests.post(url=base_url, headers=headers, data=json.dumps(body), timeout=100)
            r.raise_for_status()
            response = r.json()
            print(response)
            res = self.create({
                'lane_id': lane.id,
                'description': response,
                'transaction_amount': response.get('totalAmount', 0),
                'transaction_id': response.get('transactionId', 0),
                'transaction_status': response.get('statusCode', ""),
            })

            _logger.info('Vantiv URL {} - Status {} Vantiv status {}'.format(base_url, r.status_code,
                                                                             response.get('statusCode', 'No status')))

        except Exception:
            response = "timeout"
        return response
