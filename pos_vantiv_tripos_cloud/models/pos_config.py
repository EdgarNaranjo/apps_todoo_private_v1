# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class PosConfig(models.Model):
    _inherit = 'pos.config'

    lane_id = fields.Many2one(comodel_name='pos_vantiv_tripos_cloud.lane', string=_('Lane'), required=True)
