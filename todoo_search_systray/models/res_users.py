# Copyright 2024-TODAY Todooweb (<http://www.todooweb.com>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, models, fields


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def search_terms(self, term):
        res = []
        LIMIT = 5
        model_ids = self.env.user.groups_id.mapped('model_access').mapped('model_id').filtered(
            lambda l: l.allow_search
        )
        for rec in model_ids:
            model = rec.model
            if model not in self.env:
                continue
            records = self.env[model].name_search(term, limit=LIMIT + 1)
            if records:
                has_more = len(records) > LIMIT
                records = records[:LIMIT]
                res.append({
                    'model': model,
                    'name': rec.name,
                    'records': records,
                    'total_count': len(records),
                    'has_more': has_more,
                })
        return res


class IrModel(models.Model):
    _inherit = 'ir.model'

    allow_search = fields.Boolean(
        string='Allow Search'
    )
