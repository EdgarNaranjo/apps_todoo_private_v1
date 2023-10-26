# Copyright 2023-TODAY Todooweb (www.todooweb.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    cancel_reason_id = fields.Many2one(
        'purchase.order.cancel.reason',
        string="Reason for cancellation",
        readonly=True,
        ondelete="restrict")

    def button_draft(self):
        for po in self:
            po.write({'cancel_reason_id': False})
        return super(PurchaseOrder, self).button_draft()

    def button_cancel(self):
        for record in self:
            if record.cancel_reason_id:
                record.message_post(
                    body=_('Order \"%s\" canceled with reason: \"%s\"') % (
                        record.name,
                        record.cancel_reason_id.name))
        return super(PurchaseOrder, self).button_cancel()


class PurchaseOrderCancelReason(models.Model):
    _name = 'purchase.order.cancel.reason'
    _description = 'Purchase Order Cancel Reason'

    name = fields.Char('Reason', required=True, translate=True)
    active = fields.Boolean(default=True)
