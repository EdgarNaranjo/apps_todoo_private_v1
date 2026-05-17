# Copyright 2025-TODAY Todooweb (www.todooweb.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    check_options = fields.Selection([
        ('always', 'Always'),
        ('line', 'Only sale lines'),
    ], string='Applied in', config_parameter='purchase.check_options',
       default='always', required=True)
