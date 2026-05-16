# -*- coding: utf-'8' "-*-"
import logging
from datetime import datetime

from odoo import models, fields
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

    def _flow_form_validate(self, data):
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
        status = data.status
        res = {
            'provider_reference': data.payment_id,
            'flow_token': data.token,
            'fees': data.payment_data['fee'],
        }
        if status in [2]:
            _logger.info('Validated flow payment for tx %s: set as done' % (self.reference))
            self._set_transaction_done()
            return self.write(res)
        elif status in [1, '-7']:
            _logger.warning('Received notification for flow payment %s: set as pending' % (self.reference))
            self._set_transaction_pending()
            return self.write(res)
        else:  # 3 y 4
            error = 'Received unrecognized status for flow payment %s: %s, set as error' % (
                self.reference, codes[status].decode('utf-8'))
            _logger.warning(error)
            return self.write(res)

    def flow_getTransactionfromCommerceId(self):
        data = {
            'commerceId': self.reference,
        }
        client = self.provider_id.flow_get_client()
        resp = client.payments.get_from_commerce_id(data)
        return self.sudo().form_feedback(resp, 'flow')
