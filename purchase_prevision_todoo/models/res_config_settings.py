# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Defaults
    set_month = fields.Integer("Default month", default=6, config_parameter='purchase.set_month')
    value_multiple = fields.Integer("Default multiple", default=5, config_parameter='purchase.value_multiple')
