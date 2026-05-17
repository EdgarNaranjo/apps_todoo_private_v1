# Copyright 2025-TODAY Todooweb (https://todooweb.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    sale_line_id = fields.Many2one('sale.order.line', 'Order lines', copy=False)
    sale_id = fields.Many2one(related='sale_line_id.order_id', string='Sale Order', copy=False)


class AccountMove(models.Model):
    _inherit = 'account.move'

    sale_invoice_id = fields.Many2one('sale.invoice.union', store=False, readonly=True,
                                      string='Auto-complete', help="Auto-complete from a past invoice / sale order.")
    sale_id = fields.Many2one('sale.order', store=False, readonly=True,
                              string='Sale Order', help="Auto-complete from a past sale order.")
    invoice_sale_order_id = fields.Many2one('account.move', store=False, readonly=True, string='Invoice',
                                            help="Auto-complete from a past invoice.")

    @api.model_create_multi
    def create(self, vals_list):
        """Inherit the function to link the sale order to the invoice in autocomplete process."""
        moves = super().create(vals_list)
        for move in moves:
            if move.reversed_entry_id:
                continue
            sales = move.line_ids.sale_line_id.order_id or move.line_ids.sale_line_ids.mapped('order_id')
            if not sales:
                continue
            refs = [sale._get_html_link() for sale in sales]
            message = _("This customer invoice has been created from: %s") % ','.join(refs)
            move.message_post(body=message)
        return moves

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            if rec.reversed_entry_id:
                continue
            for line in rec.invoice_line_ids:
                sale_line_ids = line.sale_line_ids
                # This condition is for autocomplete account move.
                # The sale_line_ids field takes value when creating account move from the sale order view (wizard).
                if not sale_line_ids:
                    sale_line_ids = line.sale_line_id
                    line.update({'sale_line_ids': sale_line_ids})
                # This condition is for account move created from the sale order view.
                # When account move is created from sale order view the sale_line_id field is not set.
                if not line.sale_id and sale_line_ids:
                    line.sale_line_id = line.sale_line_ids.id
        return res

    @api.onchange('invoice_sale_order_id')
    def _onchange_invoice_sale_order_id(self):
        if self.invoice_sale_order_id:
            # Copy invoice lines.
            for line in self.invoice_sale_order_id.invoice_line_ids:
                copied_vals = line.copy_data()[0]
                self.invoice_line_ids += self.env['account.move.line'].new(copied_vals)
            self.currency_id = self.invoice_sale_order_id.currency_id
            self.fiscal_position_id = self.invoice_sale_order_id.fiscal_position_id
            # Reset
            self.invoice_sale_order_id = False

    @api.onchange('sale_invoice_id', 'sale_id')
    def _onchange_sale_auto_complete(self):
        if self.sale_invoice_id.invoice_id:
            self.invoice_sale_order_id = self.sale_invoice_id.invoice_id
            self._onchange_invoice_sale_order_id()
        elif self.sale_invoice_id.sale_order_id:
            self.sale_id = self.sale_invoice_id.sale_order_id
        self.sale_invoice_id = False
        if not self.sale_id:
            return
        # Copy data from SO
        invoice_vals = self.sale_id.with_company(self.sale_id.company_id)._prepare_invoice()
        invoice_vals['currency_id'] = self.invoice_line_ids and self.currency_id or invoice_vals.get('currency_id')
        del invoice_vals['ref']
        del invoice_vals['company_id']  # avoid recomputing the currency
        self.update(invoice_vals)
        # # Copy sale lines.
        so_lines = self.sale_id.order_line - self.invoice_line_ids.mapped('sale_line_id')
        # this line could be used to filter not invoiced sale lines
        # so_lines.filtered(lambda l: not l.display_type and l.qty_invoiced != l.product_qty)
        for line in so_lines.filtered(lambda l: not l.display_type and l.invoice_status != 'invoiced'):
            so_iteration_element = self.env['account.move.line'].new(
                line._prepare_account_move_line(self)
            )
            self.invoice_line_ids += so_iteration_element
        # Compute invoice_origin.
        origins = set(self.invoice_line_ids.mapped('sale_line_id.order_id.name'))
        self.invoice_origin = ','.join(list(origins))
        # Compute ref.
        refs = self._get_invoice_reference()
        self.ref = ', '.join(refs)
        # Compute payment_reference.
        if len(refs) == 1:
            self.payment_reference = refs[0]
        self.sale_id = False

    def _get_invoice_reference(self):
        self.ensure_one()
        vendor_refs = [ref for ref in set(self.invoice_line_ids.mapped('sale_line_id.order_id.partner_id.name')) if ref]
        if self.ref:
            return [ref for ref in self.ref.split(', ') if ref and ref not in vendor_refs] + vendor_refs
        return vendor_refs
