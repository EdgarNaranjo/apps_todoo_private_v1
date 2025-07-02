# Copyright 2025-TODAY Todooweb (www.todooweb.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models, tools
from odoo.tools import SQL


class PurchaseReport(models.Model):
    _inherit = "purchase.report"

    cancel_reason_id = fields.Many2one(
        'purchase.order.cancel.reason', string="Reason for cancellation")

    def _select(self):
        base_sql = super()._select()
        return SQL("%s, po.cancel_reason_id AS cancel_reason_id", base_sql)

    def _group_by(self):
        base_group = super()._group_by()
        return SQL("%s, po.cancel_reason_id", base_group)
