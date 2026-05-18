# Copyright 2025-TODAY Todooweb (www.todooweb.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    intercompany_count = fields.Integer(
        string='Doc. intercompany',
        compute='get_count_doc_intercompany',
    )
    intercompany_related = fields.Integer(
        string='Doc. related',
        compute='get_count_doc_intercompany',
    )

    def _search_default_journal(self):
        env_type = self.env['setting.type.journal']
        res = super()._search_default_journal()
        if hasattr(self, 'auto_invoice_id') and self.auto_invoice_id:
            obj_company = self.env['res.company'].search([
                ('partner_id', '=', self.auto_invoice_id.partner_id.id)
            ], limit=1)
            obj_type = env_type.search([
                ('company_id', '=', obj_company.id),
                ('check_default', '=', True),
                ('type_journal', '=', 'Intercompany'),
            ])
            if obj_type:
                if self.is_sale_document(include_receipts=True):
                    journal_sale = obj_type.filtered(lambda e: e.type == 'sale')
                    if journal_sale:
                        res = journal_sale[0].journal_id
                elif self.is_purchase_document(include_receipts=True):
                    journal_purchase = obj_type.filtered(lambda e: e.type == 'purchase')
                    if journal_purchase:
                        res = journal_purchase[0].journal_id
        return res

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for record in res:
            if hasattr(record, 'auto_invoice_id') and record.auto_invoice_id:
                record.ref = record.auto_invoice_id.name
        return res

    def action_open_doc_intercompany(self):
        domain = []
        if self.intercompany_count:
            domain = [
                ('move_type', 'in', ['out_invoice', 'out_refund', 'in_invoice', 'in_refund']),
                ('auto_invoice_id', '=', self.id),
            ]
        elif self.intercompany_related:
            domain = [
                ('move_type', 'in', ['out_invoice', 'out_refund', 'in_invoice', 'in_refund']),
                ('id', '=', self.auto_invoice_id.id),
            ]
        return {
            'name': _('Account move'),
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'account.move',
            'domain': domain,
        }

    @api.depends('auto_invoice_id')
    def get_count_doc_intercompany(self):
        for record in self:
            if hasattr(record, 'auto_invoice_id'):
                count_intercompany = self.env['account.move'].search_count([
                    ('move_type', 'in', ['out_invoice', 'out_refund', 'in_invoice', 'in_refund']),
                    ('auto_invoice_id', '=', record.id),
                ])
                count_related = 1 if record.auto_invoice_id else 0
                record.intercompany_count = count_intercompany
                record.intercompany_related = count_related
            else:
                record.intercompany_count = 0
                record.intercompany_related = 0
