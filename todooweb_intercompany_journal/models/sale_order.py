# Copyright 2025-TODAY Todooweb (www.todooweb.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _get_default_type(self):
        return self.env['setting.type.journal'].search([
            ('company_id', '=', self.env.company.id),
            ('check_default', '=', True),
            ('type', '=', 'sale'),
            ('type_journal', '=', 'Convencional'),
        ], limit=1)

    type_journal_id = fields.Many2one(
        'setting.type.journal',
        string='Type journal',
        check_company=True,
        default=_get_default_type,
    )

    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()
        if self.type_journal_id:
            invoice_vals['journal_id'] = self.type_journal_id.journal_id.id
        return invoice_vals
