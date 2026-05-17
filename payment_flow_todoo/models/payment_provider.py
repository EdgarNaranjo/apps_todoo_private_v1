# Copyright 2025-TODAY Todooweb (www.todooweb.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
from datetime import datetime

from odoo import api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

try:
    from payflow.client import Client
except Exception as e:
    _logger.warning("No se puede cargar Flow: %s" % str(e))


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('flow', 'Flow')],
        ondelete={'flow': 'set default'},
    )
    flow_api_key = fields.Char(string="Api Key")
    flow_private_key = fields.Char(string="Secret Key")
    flow_payment_method = fields.Selection([
        ('1', 'Webpay'),
        ('2', 'Servipag'),
        ('3', 'Multicaja'),
        ('5', 'Onepay'),
        ('8', 'Cryptocompra'),
        ('9', 'Todos los medios'),
    ], required=True, default='1')

    def flow_compute_fees(self, amount, currency_id, country_id):
        if not self.fees_active:
            return 0.0
        country = self.env['res.country'].browse(country_id)
        if country and self.company_id.country_id.id == country.id:
            percentage = self.fees_dom_var
            fixed = self.fees_dom_fixed
        else:
            percentage = self.fees_int_var
            fixed = self.fees_int_fixed
        factor = (percentage / 100.0) + (0.19 * (percentage / 100.0))
        return ((amount + fixed) / (1 - factor)) - amount

    @api.model
    def _get_flow_urls(self, environment):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        if environment == 'prod':
            return {
                'flow_form_url': base_url + '/payment/flow/redirect',
                'flow_url': "https://www.flow.cl/api",
            }
        return {
            'flow_form_url': base_url + '/payment/flow/redirect',
            'flow_url': "https://sandbox.flow.cl/api",
        }

    def _flow_get_api_url(self):
        self.ensure_one()
        return "https://www.flow.cl/api" if self.state == 'enabled' else "https://sandbox.flow.cl/api"

    def flow_form_generate_values(self, values):
        if values.get('partner_id'):
            partner = self.env['res.partner'].browse(values['partner_id'])
            values['partner_email'] = partner.email
        values.update({
            'provider_id': self.id,
            'commerceOrder': values['reference'],
            'subject': '%s: %s' % (self.company_id.name, values['reference']),
            'amount': values['amount'],
            'email': values.get('partner_email'),
            'paymentMethod': self.flow_payment_method,
            'fees': values.get('fees', 0),
            'api_url': self._flow_get_api_url(),
        })
        return values

    def flow_get_form_action_url(self):
        environment = 'prod' if self.state == 'enabled' else 'test'
        return self._get_flow_urls(environment)['flow_form_url']

    def flow_get_client(self):
        environment = 'prod' if self.state == 'enabled' else 'test'
        return Client(
            self.flow_api_key,
            self.flow_private_key,
            self._get_flow_urls(environment)['flow_url'],
            (environment == 'test'),
        )

    def flow_getTransaction(self, post):
        client = self.flow_get_client()
        return client.payments.get(post['token'])

    def flow_initTransaction(self, post):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        tx = self.env['payment.transaction'].search([
            ('reference', '=', post.get('transaction_id'))
        ])
        post.pop('provider_id', None)
        post.pop('transaction_id', None)
        amount = float(post['amount']) + float(post.get('fees', 0.0))
        currency = self.env['res.currency'].browse(int(post.get('currency_id') or 0))
        if not currency:
            currency = self.env['res.currency'].search([('name', '=', 'CLP')], limit=1)
        if self.force_currency and currency != self.force_currency_id:
            amount = currency._convert(amount, self.force_currency_id, self.company_id, datetime.now())
            currency = self.force_currency_id
        if amount < 350:
            raise ValidationError("Monto total no debe ser menor a $350")
        post.update({
            'paymentMethod': str(post.get('paymentMethod')),
            'urlConfirmation': base_url + '/payment/flow/notify/%s' % str(self.id),
            'urlReturn': base_url + '/payment/flow/return/%s' % str(self.id),
            'currency': currency.name,
            'amount': str(currency.round(amount)),
        })
        client = self.flow_get_client()
        res = client.payments.post(post)
        if hasattr(res, 'payment_url'):
            tx.write({'state': 'pending'})
        return res
