# Copyright 2025-TODAY Todooweb (www.todooweb.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    set_month = fields.Integer(
        string="Default month",
        default=6,
        config_parameter='purchase.set_month',
    )
    value_multiple = fields.Integer(
        string="Default multiple",
        default=5,
        config_parameter='purchase.value_multiple',
    )
