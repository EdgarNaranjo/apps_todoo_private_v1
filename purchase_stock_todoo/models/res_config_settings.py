# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Defaults
    check_options = fields.Selection([
        ('always', 'Always'),
        ('line', 'Only sale lines')], string='Applied in', config_parameter='purchase.check_options', default='always', required=True)
