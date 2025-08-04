# Copyright 2025-TODAY Todooweb (<http://www.todooweb.com>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, models, fields


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def search_terms(self, term):
        res = []
        model_ids = self.env['ir.model'].search([('allow_search', '=', True)])
        for rec in model_ids:
            model = rec.model
            records = self.env[model].name_search(term)
            action = self.env['ir.actions.act_window'].sudo().search([
                ('res_model', '=', model),
                ('path', '!=', False),
            ], limit=1)
            if records:
                res.append({'model': model, 'name': rec.name, 'records': records, 'path': action.path if action else ''})
        return res


class IrModel(models.Model):
    _inherit = 'ir.model'

    allow_search = fields.Boolean(
        string='Allow Search'
    )
