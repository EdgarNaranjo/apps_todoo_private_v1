# coding: utf-8
from odoo import fields, models, api


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    count_lines = fields.Integer("Count Lines", compute='_giveme_count', store=True)

    @api.depends('bom_line_ids')
    def _giveme_count(self):
        for record in self:
            record.count_lines = len(record.bom_line_ids)

