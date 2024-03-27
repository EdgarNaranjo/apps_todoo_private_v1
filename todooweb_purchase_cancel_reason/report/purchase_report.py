# Copyright 2023-TODAY Todooweb (www.todooweb.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models, tools


class PurchaseReport(models.Model):
    _inherit = "purchase.report"

    cancel_reason_id = fields.Many2one(
        'purchase.order.cancel.reason', string="Reason for cancellation")

    def _select(self):
        return super(PurchaseReport, self)._select() + ", po.cancel_reason_id as cancel_reason_id"

    def _group_by(self):
        return super(PurchaseReport, self)._group_by() + ", cancel_reason_id"

