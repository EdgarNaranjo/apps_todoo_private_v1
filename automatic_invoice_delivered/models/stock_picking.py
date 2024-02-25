# Copyright 2024-TODAY Todooweb (www.todooweb.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import models, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        """
        Inherit the standard function to create and post invoices after delivery.
        It determines if an invoice should be automatically created and posted according to the predefined settings.

        :return: result derived from executing the button_validate function in the parent class.
        """
        res = super().button_validate()
        auto_validate_invoice = self.env['ir.config_parameter'].sudo().get_param(
            'automatic_invoice_delivered.is_create_automatic_invoice')
        for pick in self:
            if auto_validate_invoice:
                if any(rec.product_id.invoice_policy == 'delivery' for rec in
                       pick.move_ids) or not pick.sale_id.invoice_ids:
                    # Execute the _create_invoices function on the linked sale to generate the invoice
                    invoice_created = pick.sale_id._create_invoices(pick.sale_id) if pick.sale_id else False
                    # Post the created invoice
                    if invoice_created:
                        invoice_created.action_post()
                        invoice_created.update({'invoice_date': pick.date_done})
                        invoice_created.message_post(body=_('Automatic invoice created from picking {}') .format(pick._get_html_link()))
                        pick.sale_id.message_post(body=_('Automatic invoice created from picking {}') .format(pick._get_html_link()))
        return res
