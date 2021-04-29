# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import uuid
import logging
import requests, json

from odoo import models, fields, api, _
from odoo.tools.float_utils import float_compare

from . import config

_logger = logging.getLogger(__name__)


class PosVantivTriposCloudConfiguration(models.Model):
    _name = 'pos_vantiv_tripos_cloud.configuration'
    _description = 'Point of Sale Vantiv triPOS Cloud Configuration'

    name = fields.Char(required=True, help='Name of the configuration Vantiv Tripos Cloud')
    express_api_credentials_account_id = fields.Char(string='Account ID', required=True, help='Identifier of the Express API Credentials Account')
    express_api_credentials_account_token = fields.Char(string='Account Token', required=True, help='Token of the Express API Credentials Account')
    express_api_credentials_application_id = fields.Char(string='Application ID', required=True, help='Identifier Application of the Express API Credentials Account')
    express_api_credentials_acceptor_id = fields.Char(string='Acceptor ID', required=True, help='Identifier Acceptor of the Express API Credentials Account')
    express_api_credentials_application_name = fields.Char(string='Application Name', required=True, help='Name Application of the Express API Credentials Account')
    express_api_credentials_application_version = fields.Char(string='Application Version', required=True, help='Version Application of the Express API Credentials Account')
    is_production = fields.Boolean(string=_('Is production ?'), default=False)
    is_vantiv = fields.Boolean(string=_('Is Vantiv?'), default=True)


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    pos_vantiv_tripos_cloud_config_id = fields.Many2one('pos_vantiv_tripos_cloud.configuration', string='triPOS Cloud Credentials', help='The configuration of triPOS Cloud used for this journal')


class PosVantivTriposCloudLane(models.Model):
    _name = 'pos_vantiv_tripos_cloud.lane'
    _description = 'Vantiv triPOS Cloud Lane Management'

    name = fields.Char(compute='_compute_get_name')
    # configuration fields
    configuration_id = fields.Many2one(comodel_name='pos_vantiv_tripos_cloud.configuration', string='Vantiv Configuration')
    # lane fields
    lane_id = fields.Integer(string=_('Lane ID'), default=0, help="Identifier Lane Management", required=True)
    terminal_id = fields.Char(string='Terminal ID', required=True, help='Identifier Terminal')
    description = fields.Char(string='Description', required=True, help='Description')
    activation_code = fields.Char(string='Activation Code', required=True, help='Pin Pads Activation Code')
    state = fields.Selection(string=_('State'), selection=[('draft', 'Draft'), ('added', 'Added'), ('del', 'Deleted')], default='draft')
    body = fields.Text()

    @api.one
    @api.depends('lane_id', 'description')
    def _compute_get_name(self):
        self.name = '{} - {}'.format(self.lane_id, self.description)

    @api.constrains('lane_id')
    def _check_lane_id(self):
        pass

    @api.multi
    def add_lane_to_triposcloud(self):
        # TODO Aqui vamos a crear la lineas via API REst
        data = {}

        for rec in self:
            config_obj = rec.configuration_id
            guid = uuid.uuid4()
            print(str(guid))
            headers = {
                'User-agent': 'Mozilla/5.0',
                'accept': 'application/json',
                'content-type': 'application/json',
                'charset': 'utf-8',
                'tp-authorization': 'Version=2.0',
                'tp-application-id':  config_obj.express_api_credentials_application_id,
                'tp-application-name': config_obj.express_api_credentials_application_name,
                'tp-application-version': config_obj.express_api_credentials_application_version,
                'tp-express-acceptor-id': config_obj.express_api_credentials_acceptor_id,
                'tp-express-account-id':  config_obj.express_api_credentials_account_id,
                'tp-express-account-token':  config_obj.express_api_credentials_account_token,
                'tp-request-id': str(guid)
            }
            data = {
                'laneId': int(rec.lane_id),
                'description': str(rec.description),
                'terminalId': str(rec.terminal_id),
                'activationCode': str(rec.activation_code)
            }

            base_url = "https://triposcert.vantiv.com/cloudapi/v1/lanes"
            if config_obj.is_production:
                base_url = "https://tripos.vantiv.com/cloudapi/v1/lanes"

            req = requests.post(base_url, headers=headers, data=json.dumps(data))

            # rec.state = 'added'
            # return True
            print(req.status_code)
            print(req.content)
            rec.body = req.content

            if req.status_code == 200:
                rec.state = 'added'
                rec.body = req.json()
                return True
            else:
                return False

    @api.multi
    def del_lane_to_triposcloud(self):
        # TODO Aqui vamos a crear la lineas via API REst
        data = {}

        for rec in self:
            data['laneId'] = rec.lane_id
            data['description'] = rec.description
            data['terminalId'] = rec.terminal_id
            data['activationCode'] = rec.activation_code

            config_obj = rec.configuration_id
            config.headers[
                'tp-application-id'] = config_obj.express_api_credentials_application_id
            config.headers[
                'tp-application-name'] = config_obj.express_api_credentials_application_name
            config.headers[
                'tp-application-version'] = config_obj.express_api_credentials_application_version
            config.headers[
                'tp-express-acceptor-id'] = config_obj.express_api_credentials_acceptor_id
            config.headers[
                'tp-express-account-id'] = config_obj.express_api_credentials_account_id
            config.headers[
                'tp-express-account-token'] = config_obj.express_api_credentials_account_token
            config.headers['tp-request-id'] = str(uuid.uuid4())

            base_url = "https://triposcert.vantiv.com/cloudapi/v1/lanes/{}".format(rec.lane_id)
            if config_obj.is_production:
                base_url = "https://tripos.vantiv.com/cloudapi/v1/lanes/{}".format(rec.lane_id)

            req = requests.delete(
                '{}'.format(base_url), headers=config.headers, data=data)

            if req.status_code == 200:
                rec.state = 'added'
                return True
            else:
                return False
