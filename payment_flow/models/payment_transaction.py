# -*- coding: utf-'8' "-*-"
import logging
from datetime import datetime

from odoo import models, fields, api
from odoo.addons.payment.models.payment_provider import ValidationError
from odoo.tools.translate import _

_logger = logging.getLogger(__name__)

try:
    from payflow.client import Client
except Exception as e:
    _logger.warning("No se puede cargar Flow: %s" % str(e))


class PaymentTxFlow(models.Model):
    _inherit = 'payment.transaction'

    flow_token = fields.Char(
        string="Flow Token Transaction",
    )
    fees = fields.Monetary(
        string="Fees", currency_field='currency_id',
        help="The fees amount; set by the system as it depends on the provider", readonly=True)

    @api.model_create_multi
    def create(self, values_list):
        # Compute fees. For validation transactions, fees are zero.
        for values in values_list:
            provider = self.env['payment.provider'].browse(values['provider_id'])
            partner = self.env['res.partner'].browse(values['partner_id'])

            if values.get('operation') == 'validation':
                values['fees'] = 0
            else:
                currency = self.env['res.currency'].browse(values.get('currency_id')).exists()
                values['fees'] = provider.flow_compute_fees(
                    values.get('amount', 0), currency, partner.country_id,
                )

        return super().create(values_list)

    def _flow_form_get_invalid_parameters(self, data):
        invalid_parameters = []

        if data.subject != '%s: %s' % (self.provider_id.company_id.name, self.reference):
            invalid_parameters.append(('reference', data.subject,
                                       '%s: %s' % (self.provider_id.company_id.name, self.reference)))
        if data.transaction_id != self.reference:
            invalid_parameters.append(('reference', data.transaction_id, self.reference))
        # check what is buyed
        amount = (self.amount + self.provider_id.compute_fees(self.amount, self.currency_id.id,
                                                              self.partner_country_id.id))
        currency = self.currency_id
        if self.provider_id.force_currency and currency != self.provider_id.force_currency_id:
            amount = lambda price: currency._convert(
                amount,
                self.provider_id.force_currency_id,
                self.provider_id.company_id,
                datetime.now())
            currency = self.provider_id.force_currency_id
        amount = currency.round(amount)
        if float(data.amount) != amount:
            invalid_parameters.append(('amount', data.amount, amount))

        return invalid_parameters

    def _get_specific_rendering_values(self, processing_values):
        """ Override of payment to return Payulatam-specific rendering values.

        Note: self.ensure_one() from `_get_processing_values`

        :param dict processing_values: The generic and specific processing values of the transaction
        :return: The dict of provider-specific processing values
        :rtype: dict
        """
        res = super()._get_specific_rendering_values(processing_values)

        if self.provider_code != "flow":
            return res

        values = self.provider_id.flow_form_generate_values(processing_values)
        return values

    def _flow_form_get_tx_from_data(self, data):
        reference, txn_id = data.transaction_id, data.payment_id
        if not reference or not txn_id:
            error_msg = _('Flow: received data with missing reference (%s) or txn_id (%s)') % (reference, txn_id)
            _logger.warning(error_msg)
            raise ValidationError(error_msg)

        # find tx -> @TDENOTE use txn_id ?
        txs = self.env['payment.transaction'].search([
            ('reference', '=', reference),
            ('provider_code', '=', 'flow')])
        if not txs or len(txs) > 1:
            error_msg = 'Flow: received data for reference %s' % (reference)
            if not txs:
                error_msg += '; no order found'
            else:
                error_msg += '; multiple order found'
            _logger.info(error_msg)
            raise ValidationError(error_msg)
        return txs[0]

    def _get_tx_from_notification_data(self, provider_code, data):
        """ Override of payment to find the transaction based on Paypal data.

        :param str provider_code: The code of the provider that handled the transaction
        :param dict notification_data: The notification data sent by the provider
        :return: The transaction if found
        :rtype: recordset of `payment.transaction`
        :raise: ValidationError if the data match no transaction
        """
        tx = super()._get_tx_from_notification_data(provider_code, data)
        if provider_code != 'flow' or len(tx) == 1:
            return tx

        codes = {
            '0': 'Transacción aprobada.',
            '-1': 'Rechazo de transacción.',
            '-2': 'Transacción debe reintentarse.',
            '-3': 'Error en transacción.',
            '-4': 'Rechazo de transacción.',
            '-5': 'Rechazo por error de tasa.',
            '-6': 'Excede cupo máximo mensual.',
            '-7': 'Excede límite diario por transacción.',
            '-8': 'Rubro no autorizado.',
        }

        reference = data.transaction_id
        _logger.info("_get_tx_from_notification_data ==> Finding tx with reference %s" % reference)

        tx = self.search([('reference', '=', reference), ('provider_code', '=', 'flow')])
        _logger.info("_get_tx_from_notification_data ==> Finding tx:\n%s" % tx)

        if not tx:
            raise ValidationError(
                "Flow: " + _("No transaction found matching reference %s.", reference)
            )

        status = data.status
        res = {
            'provider_reference': data.payment_id,
            'flow_token': data.token,
            'fees': data.payment_data['fee'],
        }
        if status == 2:
            _logger.info('Validated flow payment for tx %s: set as done' % (reference))
            tx._set_done()
            tx.write(res)
        elif status in (1, '-7'):
            _logger.warning('Received notification for flow payment %s: set as pending' % (reference))
            tx._set_pending()
            tx.write(res)
        else:  # 3 y 4
            error = 'Received unrecognized status for flow payment %s: %s, set as error' % (
                reference, codes[status].decode('utf-8'))
            _logger.warning(error)
            tx.write(res)

        tx._finalize_post_processing()
        return tx

    def flow_getTransactionfromCommerceId(self):
        self.ensure_one()

        data = {
            'commerceId': self.reference,
        }
        client = self.provider_id.flow_get_client()
        response = client.payments.get_from_commerce_id(data)
        return self.sudo()._get_tx_from_notification_data('flow', response)
