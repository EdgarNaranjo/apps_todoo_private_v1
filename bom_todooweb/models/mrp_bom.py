# Copyright 2025-TODAY Todooweb (www.todooweb.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    count_lines = fields.Integer(
        string="Count Lines",
        compute='_giveme_count',
        store=True,
    )

    @api.depends('bom_line_ids')
    def _giveme_count(self):
        for record in self:
            record.count_lines = len(record.bom_line_ids)
