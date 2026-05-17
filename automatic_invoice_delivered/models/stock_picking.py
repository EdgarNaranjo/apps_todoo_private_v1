# Copyright 2025-TODAY Todooweb (www.todooweb.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    auto_invoice_count = fields.Integer(
        string='Auto Invoices',
        compute='_compute_auto_invoice_count',
        help='Invoices created automatically by this module',
    )
    auto_invoice_enabled = fields.Boolean(
        string='Auto Invoice Active',
        compute='_compute_auto_invoice_enabled',
        help='Indicates if automatic invoicing is enabled in settings',
    )

    def _compute_auto_invoice_count(self):
        for pick in self:
            if pick.sale_id:
                pick.auto_invoice_count = len(
                    pick.sale_id.invoice_ids.filtered(
                        lambda i: i.state == 'posted'
                    )
                )
            else:
                pick.auto_invoice_count = 0

    def _compute_auto_invoice_enabled(self):
        enabled = self.env['ir.config_parameter'].sudo().get_param(
            'automatic_invoice_delivered.is_create_automatic_invoice'
        )
        for pick in self:
            pick.auto_invoice_enabled = bool(enabled)

    def action_view_auto_invoices(self):
        """Open invoices linked to the sale order of this picking."""
        self.ensure_one()
        return {
            'name': _('Invoices'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.sale_id.invoice_ids.ids)],
        }

    def button_validate(self):
        """
        Inherit the standard function to create and post invoices after delivery.
        It determines if an invoice should be automatically created and posted
        according to the predefined settings.
        """
        res = super().button_validate()
        auto_validate_invoice = self.env['ir.config_parameter'].sudo().get_param(
            'automatic_invoice_delivered.is_create_automatic_invoice')
        for pick in self:
            if auto_validate_invoice:
                if any(rec.product_id.invoice_policy == 'delivery' for rec in
                       pick.move_ids) or not pick.sale_id.invoice_ids:
                    invoice_created = pick.sale_id._create_invoices(pick.sale_id) if pick.sale_id else False
                    if invoice_created:
                        # Set invoice_date before posting (cannot modify after)
                        invoice_created.invoice_date = pick.date_done
                        invoice_created.action_post()
                        invoice_created.message_post(
                            body=_('Automatic invoice created from picking {}').format(
                                pick._get_html_link()
                            )
                        )
                        pick.sale_id.message_post(
                            body=_('Automatic invoice created from picking {}').format(
                                pick._get_html_link()
                            )
                        )
        return res
