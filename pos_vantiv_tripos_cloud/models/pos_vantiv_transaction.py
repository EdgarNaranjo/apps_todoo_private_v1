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
