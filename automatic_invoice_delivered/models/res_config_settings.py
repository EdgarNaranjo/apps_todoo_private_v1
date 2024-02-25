# Copyright 2024-TODAY Todooweb (www.todooweb.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    is_automatic_invoice_delivered = fields.Boolean(
        string="Automatic Invoice Delivered",
        config_parameter='automatic_invoice_delivered.is_create_automatic_invoice'
    )
