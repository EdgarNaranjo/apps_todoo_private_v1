# Copyright 2024-TODAY Todooweb (<http://www.todooweb.com>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, models, fields


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def search_terms(self, term):
        res = []
        model_ids = self.env.user.groups_id.mapped('model_access').mapped('model_id').filtered(lambda l: l.allow_search)
        for rec in model_ids:
            model = rec.model
            records = self.env[model].name_search(term)
            if records:
                res.append({'model': model, 'name': rec.name, 'records': records})
        return res


class IrModel(models.Model):
    _inherit = 'ir.model'

    allow_search = fields.Boolean(
        string='Allow Search'
    )
