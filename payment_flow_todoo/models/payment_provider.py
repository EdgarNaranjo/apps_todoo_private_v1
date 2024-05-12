# -*- coding: utf-'8' "-*-"
import logging
from datetime import datetime

from odoo import api, models, fields
from odoo.addons.payment.models.payment_provider import ValidationError

_logger = logging.getLogger(__name__)

try:
    from payflow.client import Client
except Exception as e:
    _logger.warning("No se puede cargar Flow: %s" % str(e))


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('flow', 'Flow')],
        ondelete={'flow': 'set default'}
    )
    flow_api_key = fields.Char(
        string="Api Key",
    )
    flow_private_key = fields.Char(
        string="Secret Key",
    )
    flow_payment_method = fields.Selection(
        [
            ('1', 'Webpay'),
            ('2', 'Servipag'),
            ('3', 'Multicaja'),
            ('5', 'Onepay'),
            ('8', 'Cryptocompra'),
            ('9', 'Todos los medios'),
        ],
        required=True,
        default='1',
    )

    def _get_feature_support(self):
        res = super()._get_feature_support()
        res['fees'].append('flow')
        return res

    def flow_compute_fees(self, amount, currency_id, country_id):
        """ Compute Flow fees.

            :param float amount: the amount to pay
            :param integer country_id: an ID of a res.country, or None. This is
                                       the customer's country, to be compared to
                                       the acquirer company country.
            :return float fees: computed fees
        """
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
        fees = ((amount + fixed) / (1 - factor))
        return (fees - amount)

    @api.model
    def _get_flow_urls(self, environment):
        base_url = self.env['ir.config_parameter'].sudo().get_param(
            'web.base.url')
        if environment == 'prod':
            return {
                'flow_form_url': base_url + '/payment/flow/redirect',
                'flow_url': "https://www.flow.cl/api",
            }
        else:
            return {
                'flow_form_url': base_url + '/payment/flow/redirect',
                'flow_url': "https://sandbox.flow.cl/api",
            }

    def _flow_get_api_url(self):
        """ Return the API URL according to the provider state.

        Note: self.ensure_one()

        :return: The API URL
        :rtype: str
        """
        self.ensure_one()

        if self.state == 'enabled':
            return "https://www.flow.cl/api"
        else:
            return "https://sandbox.flow.cl/api"

    def flow_form_generate_values(self, values):
        # banks = self.flow_get_banks()#@TODO mostrar listados de bancos
        # _logger.warning("banks %s" %banks)
        if values.get('partner_id', False):
            partner = self.env['res.partner'].browse(values['partner_id'])
            values['partner_email'] = partner.email

        values.update({
            'provider_id': self.id,
            'commerceOrder': values['reference'],
            'subject': '%s: %s' % (self.company_id.name, values['reference']),
            'amount': values['amount'],
            'email': values['partner_email'],
            'paymentMethod': self.flow_payment_method,
            'fees': values.get('fees', 0),
            "api_url": self._flow_get_api_url(),
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

    def flow_get_banks(self):
        client = self.flow_get_client()
        return client.banks.get()

    def flow_initTransaction(self, post):
        base_url = self.env['ir.config_parameter'].sudo().get_param(
            'web.base.url')
        tx = self.env['payment.transaction'].search([
            ('reference', '=', post.get('transaction_id'))])
        del (post['provider_id'])
        del (post['transaction_id'])
        amount = (float(post['amount']) + float(post.get('fees', 0.00)))

        currency = self.env['res.currency'].browse(int(post.get('currency_id', False)))
        if not currency:
            currency = self.env['res.currency'].search([
                ('name', '=', 'CLP'),
            ])
        if self.force_currency and currency != self.force_currency_id:
            post['amount'] = lambda price: currency._convert(
                amount,
                self.force_currency_id,
                self.company_id,
                datetime.now())
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
        # post['uf'] += '/%s' % str(self.id)
        _logger.info("post %s" % post, self.flow_api_key, self.flow_private_key)
        client = self.flow_get_client()
        res = client.payments.post(post)
        if hasattr(res, 'payment_url'):
            tx.write({'state': 'pending'})
        return res

    def flow_getTransaction(self, post):
        client = self.flow_get_client()
        return client.payments.get(post['token'])
