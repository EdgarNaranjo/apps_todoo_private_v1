import logging
import pprint
import uuid
import requests
import json
from requests.exceptions import Timeout
import random

from odoo import _, api, fields, models
from odoo.exceptions import AccessDenied, UserError

_logger = logging.getLogger(__name__)
TIMEOUT = 10


class PoSPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    pos_vantiv_tripos_cloud_config_id = fields.Many2one(
        'pos_vantiv_tripos_cloud.configuration',
        string='triPOS Cloud Credentials',
        help='The configuration of triPOS Cloud used for this journal',
    )

    def _get_payment_terminal_selection(self):
        return super(
            PoSPaymentMethod, self
        )._get_payment_terminal_selection() + [
            ('tripos_vantiv', 'Tripos Vantiv Cloud')
        ]

    @api.onchange('use_payment_terminal')
    def _onchange_use_payment_terminal(self):
        super(PoSPaymentMethod, self)._onchange_use_payment_terminal()
        if self.use_payment_terminal != 'tripos_vantiv':
            self.pos_vantiv_tripos_cloud_config_id = False

    def proxy_tripos_vantiv_request(self, data, operation=False):
        self.ensure_one()
        if not self.env.su and not self.user_has_groups(
            "point_of_sale.group_pos_user"
        ):
            raise AccessDenied()
        if not data:
            raise UserError(_("Invalid Vantiv Tripos Cloud request"))

        if operation == "pay":
            return self._tripos_vantiv_pay(data)
        elif operation == "cancel":
            return self._tripos_vantiv_cancel(data)
        else:
            return {"error": "Invalid requests"}

    def _tripos_vantiv_cancel(self, data):
        return {
            "success": {"message": "cancel"},
        }

    def _tripos_vantiv_pay(self, data):
        print('data ', data)
        lane = self.env['pos_vantiv_tripos_cloud.lane'].search(
            [('id', '=', data.get('lane_id'))], limit=1
        )
        # print('lane', lane)
        if not lane.exists():
            return "not setup"

        if not data.get("amount_total", False):
            return "not amount"

        _logger.info("Vantiv Lane {} ".format(lane.name))
        # Payment request
        transactionAmount = data['amount_total']

        body = {
            'laneId': lane.lane_id,
            'transactionAmount': transactionAmount,
            'ReferenceNumber': random.randint(1, 101) * 5,
            'TicketNumber': random.randint(1, 101) * 5,
            'configuration': {'allowDebit': True},
        }
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
            'tp-request-id': str(guid),
        }

        base_url = "https://triposcert.vantiv.com/api/v1/sale"
        if transactionAmount < 0:
            base_url = "https://triposcert.vantiv.com/api/v1/refund"
            if config_obj.is_production:
                base_url = "https://tripos.vantiv.com/api/v1/refund"

        elif config_obj.is_production:
            base_url = "https://tripos.vantiv.com/api/v1/sale"

        try:
            r = requests.post(
                url=base_url,
                headers=headers,
                data=json.dumps(body),
                timeout=(6, 12),
            )
            r.raise_for_status()
            response = r.json()
            print(response)
            self.create(
                {
                    'order_name': data.get('order_name', ''),
                    'lane_id': lane.id,
                    'description': response,
                    'transaction_amount': response.get('totalAmount', 0),
                    'transaction_id': response.get('transactionId', 0),
                    'transaction_status': response.get('statusCode', ""),
                }
            )

            _logger.info(
                'Vantiv URL {} - Status {} Vantiv status {} Line {}'.format(
                    base_url,
                    r.status_code,
                    response.get('statusCode', 'No status'),
                    lane.name,
                )
            )
        except Timeout:
            response = "timeout"
        return response
