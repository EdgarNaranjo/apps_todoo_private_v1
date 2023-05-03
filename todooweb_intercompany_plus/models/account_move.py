# Copyright 2022-TODAY Rapsodoo Iberia S.r.L. (www.rapsodoo.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta


class AccountMove(models.Model):
    _inherit = 'account.move'

    intercompany_count = fields.Integer('Doc. intercompany', compute='get_count_doc_intercompany')
    intercompany_related = fields.Integer('Doc. related', compute='get_count_doc_intercompany')

    def _search_default_journal(self):
        env_company = self.env['res.company']
        env_type = self.env['setting.type.journal']
        res = super(AccountMove, self)._search_default_journal()
        if 'auto_invoice_id' in self:
            if self.auto_invoice_id:
                obj_company = env_company.search([('partner_id', '=', self.auto_invoice_id.partner_id.id)], limit=1)
                obj_type = env_type.search([('company_id', '=', obj_company.id),
                                            ('check_default', '=', True),
                                            ('type_journal', '=', 'Intercompany')])
                if obj_type:
                    if self.is_sale_document(include_receipts=True):
                        journal_sale = obj_type.filtered(lambda e: e.type == 'sale')
                        if journal_sale:
                            res = journal_sale[0].mapped('journal_id')
                    elif self.is_purchase_document(include_receipts=True):
                        journal_purchase = obj_type.filtered(lambda e: e.type == 'purchase')
                        if journal_purchase:
                            res = journal_purchase[0].mapped('journal_id')
        return res

    @api.model_create_multi
    def create(self, vals_list):
        res = super(AccountMove, self).create(vals_list)
        for record in res:
            if 'auto_invoice_id' in self:
                if record.auto_invoice_id:
                    record.ref = record.auto_invoice_id.name
        return res

    def action_open_doc_intercompany(self):
        dic_return = {
            'name': 'Account move',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
        }
        if self.intercompany_count:
            dic_return['domain'] = [('move_type', 'in', ['out_invoice', 'out_refund', 'in_invoice', 'in_refund']),
                                    ('auto_invoice_id', '=', self.id)]
        elif self.intercompany_related:
            dic_return['domain'] = [('move_type', 'in', ['out_invoice', 'out_refund', 'in_invoice', 'in_refund']),
                                    ('id', '=', self.auto_invoice_id.id)]
        return dic_return

    def get_count_doc_intercompany(self):
        env_move = self.env['account.move']
        val_count_intercompany = 0
        val_count_related = 0
        for record in self:
            if 'auto_invoice_id' in self:
                obj_move = env_move.search([('move_type', 'in', ['out_invoice', 'out_refund', 'in_invoice', 'in_refund'])])
                filtered_intercompany = obj_move.filtered(lambda e: e.auto_invoice_id == record)
                val_count_intercompany = len(filtered_intercompany)
                filtered_related = obj_move.filtered(lambda e: e == record.auto_invoice_id)
                val_count_related = len(filtered_related)
            record.intercompany_count = val_count_intercompany
            record.intercompany_related = val_count_related
