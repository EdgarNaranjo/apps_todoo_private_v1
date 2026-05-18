# Copyright 2025-TODAY Todooweb (www.todooweb.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

try:
    from payflow.client import Client
except Exception as e:
    _logger.warning("No se puede cargar Flow: %s" % str(e))


class PaymentTxFlow(models.Model):
    _inherit = 'payment.transaction'

    flow_token = fields.Char(string="Flow Token Transaction")

    def _get_specific_rendering_values(self, processing_values):
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'flow':
            return res
        return self.provider_id.flow_form_generate_values(processing_values)

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != 'flow' or len(tx) == 1:
            return tx
        reference = (notification_data.get('transaction_id')
                     if isinstance(notification_data, dict)
                     else getattr(notification_data, 'transaction_id', None))
        if not reference:
            raise ValidationError("Flow: missing reference in notification data")
        tx = self.search([('reference', '=', reference), ('provider_code', '=', 'flow')])
        if not tx:
            raise ValidationError(_("Flow: no transaction found for reference %s") % reference)
        return tx

    def _process_notification_data(self, notification_data):
        super()._process_notification_data(notification_data)
        if self.provider_code != 'flow':
            return
        status = (notification_data.get('status')
                  if isinstance(notification_data, dict)
                  else getattr(notification_data, 'status', None))
        res = {
            'provider_reference': getattr(notification_data, 'payment_id', False),
            'flow_token': getattr(notification_data, 'token', False),
        }
        self.write(res)
        if status == 2:
            self._set_done()
        elif status == 1:
            self._set_pending()
        else:
            self._set_error(_("Flow payment error, status: %s") % status)
