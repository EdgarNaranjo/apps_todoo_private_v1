# Copyright 2025-TODAY Todooweb (www.todooweb.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    check_new = fields.Boolean('New Purchase Order')


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _make_po_get_domain(self, company_id, values, partner):
        env_parameter = self.env['ir.config_parameter']
        check_options = env_parameter.sudo().get_param('purchase.check_options')
        check_process = False
        domain = super()._make_po_get_domain(company_id, values, partner)
        if domain:
            if check_options == 'line':
                if values.get('group_id') and values.get('group_id').sale_id:
                    check_process = True
            else:
                check_process = True
            if check_process:
                domain += (('check_new', '=', True),)
        return domain
