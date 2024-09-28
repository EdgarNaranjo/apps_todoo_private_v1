import uuid
import logging
import requests
import json
from requests.exceptions import Timeout
import random

from odoo import fields, models, api, _

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


class BarcodeRule(models.Model):
    _inherit = 'barcode.rule'

    type = fields.Selection(
        selection_add=[('credit', 'Credit Card')],
        ondelete={'credit': 'set default'},
    )


class PosVantivTransaction(models.Model):
    _name = 'pos_vantiv_tripos_cloud.transaction'

    name = fields.Char(compute="_compute_get_name", string=_('Name'))
    lane_id = fields.Many2one(
        comodel_name='pos_vantiv_tripos_cloud.lane', string=_('Lane')
    )
    transaction_amount = fields.Float()
    transaction_id = fields.Integer()
    transaction_status = fields.Char()
    order_name = fields.Char()
    description = fields.Text(string=_('Description'))

    @api.depends('lane_id', 'transaction_amount')
    def _compute_get_name(self):
        for rec in self:
            rec.name = "{} - {}".format(
                rec.lane_id.name, rec.transaction_amount
            )

    # @api.model
    # def do_refund(self, data):
    #     print('data ', data)
    #     lane = self.env['pos_vantiv_tripos_cloud.lane'].search(
    #         [('id', '=', data.get('lane_id'))], limit=1)
    #     # print('lane', lane)
    #     if not lane.exists():
    #         return "not setup"
    #
    #     _logger.info("Vantiv Lane {} ".format(lane.name))
    #     # Payment request
    #     body = {}
    #     body['laneId'] = lane.lane_id
    #     body['transactionAmount'] = data.get('amount_total')
    #     body['ReferenceNumber'] = random.randint(1, 101) * 5
    #     body['TicketNumber'] = random.randint(1, 101) * 5
    #
    #     # print(body)
    #     guid = uuid.uuid4()
    #
    #     config_obj = lane.configuration_id
    #
    #     headers = {
    #         'User-agent': 'Mozilla/5.0',
    #         'accept': 'application/json',
    #         'content-type': 'application/json',
    #         'charset': 'utf-8',
    #         'tp-authorization': 'Version=2.0',
    #         'tp-application-id': config_obj.express_api_credentials_application_id,
    #         'tp-application-name': config_obj.express_api_credentials_application_name,
    #         'tp-application-version': config_obj.express_api_credentials_application_version,
    #         'tp-express-acceptor-id': config_obj.express_api_credentials_acceptor_id,
    #         'tp-express-account-id': config_obj.express_api_credentials_account_id,
    #         'tp-express-account-token': config_obj.express_api_credentials_account_token,
    #         'tp-request-id': str(guid)
    #     }
    #
    #     base_url = "https://triposcert.vantiv.com/api/v1/refund"
    #     if config_obj.is_production:
    #         base_url = "https://tripos.vantiv.com/api/v1/refund"
    #
    #     try:
    #         r = requests.post(url=base_url, headers=headers, data=json.dumps(body), timeout=100)
    #         r.raise_for_status()
    #         response = r.json()
    #         print(response)
    #         res = self.create({
    #             'lane_id': lane.id,
    #             'transaction_amount': data.get('amount_total'),
    #             'description': response,
    #             'transaction_amount': response.get('totalAmount', 0),
    #             'transaction_id': response.get('transactionId', 0),
    #             'transaction_status': response.get('statusCode', ""),
    #         })
    #
    #         _logger.info('Vantiv URL {} - Status {} Vantiv status {}'.format(base_url, r.status_code,
    #                                                                          response.get('statusCode', 'No status')))
    #
    #     except Exception:
    #         response = "timeout"
    #     return response

    # @api.model
    # def do_transaction(self, data):
    #     print('data ', data)
    #     lane = self.env['pos_vantiv_tripos_cloud.lane'].search(
    #         [('id', '=', data.get('lane_id'))], limit=1
    #     )
    #     # print('lane', lane)
    #     if not lane.exists():
    #         return "not setup"

    #     _logger.info("Vantiv Lane {} ".format(lane.name))
    #     # Payment request
    #     body = {
    #         'laneId': lane.lane_id,
    #         'transactionAmount': data.get('amount_total'),
    #         'ReferenceNumber': random.randint(1, 101) * 5,
    #         'TicketNumber': random.randint(1, 101) * 5,
    #         'configuration': {'allowDebit': True},
    #     }
    #     # print(body)
    #     guid = uuid.uuid4()

    #     config_obj = lane.configuration_id

    #     headers = {
    #         'User-agent': 'Mozilla/5.0',
    #         'accept': 'application/json',
    #         'content-type': 'application/json',
    #         'charset': 'utf-8',
    #         'tp-authorization': 'Version=2.0',
    #         'tp-application-id': config_obj.express_api_credentials_application_id,
    #         'tp-application-name': config_obj.express_api_credentials_application_name,
    #         'tp-application-version': config_obj.express_api_credentials_application_version,
    #         'tp-express-acceptor-id': config_obj.express_api_credentials_acceptor_id,
    #         'tp-express-account-id': config_obj.express_api_credentials_account_id,
    #         'tp-express-account-token': config_obj.express_api_credentials_account_token,
    #         'tp-request-id': str(guid),
    #     }

    #     base_url = "https://triposcert.vantiv.com/api/v1/sale"
    #     if config_obj.is_production:
    #         base_url = "https://tripos.vantiv.com/api/v1/sale"

    #     try:
    #         r = requests.post(
    #             url=base_url,
    #             headers=headers,
    #             data=json.dumps(body),
    #             timeout=(6, 12),
    #         )
    #         r.raise_for_status()
    #         response = r.json()
    #         print(response)
    #         self.create(
    #             {
    #                 'order_name': data.get('order_name', ''),
    #                 'lane_id': lane.id,
    #                 'description': response,
    #                 'transaction_amount': response.get('totalAmount', 0),
    #                 'transaction_id': response.get('transactionId', 0),
    #                 'transaction_status': response.get('statusCode', ""),
    #             }
    #         )

    #         _logger.info(
    #             'Vantiv URL {} - Status {} Vantiv status {} Line {}'.format(
    #                 base_url,
    #                 r.status_code,
    #                 response.get('statusCode', 'No status'),
    #                 lane.name,
    #             )
    #         )
    #     except Timeout:
    #         response = "timeout"
    #     return response
