# Copyright 2025-TODAY Todooweb (www.todooweb.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    repair_type_id = fields.Many2one(
        "repair.type",
        string="Repair Type",
        config_parameter="order_repair_todoo.repair_type_id"
    )
    reason_id = fields.Many2one(
        "repair.reason",
        string="Repair reason",
        config_parameter="order_repair_todoo.reason_id"
    )
    invoice_method = fields.Selection([
        ("none", "No Invoice"),
        ("b4repair", "Before Repair"),
        ("after_repair", "After Repair")], default='after_repair', string="Invoice Method",
        help='Selecting \'Before Repair\' or \'After Repair\' will allow you to generate invoice before or '
             'after the repair is done respectively. \'No invoice\' means you don\'t want to generate invoice '
             'for this repair order.',
        config_parameter="order_repair_todoo.invoice_method"
    )
    location_id = fields.Many2one(
        'stock.location', 'Location',
        check_company=True,
        config_parameter="order_repair_todoo.location_id"
    )
    check_demo = fields.Boolean(
        string='Request demo'
    )
    mobile_invite_email = fields.Char(
        string='Email invitation',
        default='devtodoo@gmail.com'
    )

    def set_values(self):
        super().set_values()
        config_params = self.env['ir.config_parameter'].sudo()
        config_params.set_param('order_repair_todoo.check_demo', '1' if self.check_demo else '0')
        if self.check_demo:
            email_to = config_params.get_param('order_repair_todoo.mobile_invite_email') or 'devtodoo@gmail.com'
            template = self.env.ref('order_repair_todoo.email_template_mobile_invite')
            template.sudo().send_mail(
                res_id=False,
                force_send=True,
                email_values={
                    'email_to': email_to,
                    'email_from': f'noreply@example.com ({self.company_name})'
                }
            )
