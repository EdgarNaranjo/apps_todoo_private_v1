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

    support_fees = fields.Boolean(
        string="Fees Supported", compute='_compute_feature_support_fields'
    )

    # Fees fields
    fees_active = fields.Boolean(string="Add Extra Fees")
    fees_dom_fixed = fields.Float(string="Fixed domestic fees")
    fees_dom_var = fields.Float(string="Variable domestic fees (in percents)")
    fees_int_fixed = fields.Float(string="Fixed international fees")
    fees_int_var = fields.Float(string="Variable international fees (in percents)")

    def _compute_feature_support_fields(self):
        """ Compute the feature support fields based on the provider.

        Feature support fields are used to specify which additional features are supported by a
        given provider. These fields are as follows:

        - `support_express_checkout`: Whether the "express checkout" feature is supported. `False`
          by default.
        - `support_fees`: Whether the "extra fees" feature is supported. `False` by default.
        - `support_manual_capture`: Whether the "manual capture" feature is supported. `False` by
          default.
        - `support_refund`: Which type of the "refunds" feature is supported: `None`,
          `'full_only'`, or `'partial'`. `None` by default.
        - `support_tokenization`: Whether the "tokenization feature" is supported. `False` by
          default.

        For a provider to specify that it supports additional features, it must override this method
        and set the related feature support fields to the desired value on the appropriate
        `payment.provider` records.

        :return: None
        """
        self.update(dict.fromkeys((
            'support_express_checkout',
            'support_fees',
            'support_manual_capture',
            'support_refund',
            'support_tokenization',
        ), None))

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
            True,
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
        if post.get('data_set', False):
            del (post['data_set'])
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
            'paymentMethod': int(post.get('paymentMethod')),
            'urlConfirmation': base_url + '/payment/flow/notify/' + str(self.id),
            'urlReturn': base_url + '/payment/flow/return/' + str(self.id),
            'currency': currency.name,
            'amount': f"{currency.round(amount)}",
        })

        _logger.info("post %s" % post, self.flow_api_key, self.flow_private_key)
        try:
            client = self.flow_get_client()
            res = client.payments.post(post)
        except Exception as e:
            raise ValidationError("Error al procesar pago: %s" % str(e))
        if hasattr(res, 'payment_url'):
            tx.write({'state': 'pending'})
        return res

    def flow_getTransaction(self, provider_id: str, post):
        _logger.info(
            "flow_getTransaction ==> post {0} ==> key {1} ==> private {2} ==> {3}".format(post, self.flow_api_key,
                                                                                          self.flow_private_key,
                                                                                          provider_id))
        provider_obj = self.env['payment.provider'].browse(int(provider_id))
        client = provider_obj.sudo().flow_get_client()
        return client.payments.get(post['token'])
