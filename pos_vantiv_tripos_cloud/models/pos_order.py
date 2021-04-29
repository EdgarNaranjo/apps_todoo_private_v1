# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import fields, models, api, _
from odoo.exceptions import UserError


class PosOrder(models.Model):
    _inherit = 'pos.order'

    lane_id = fields.Many2one('pos_vantiv_tripos_cloud.lane', related='config_id.lane_id', string="POS Lane")

    @api.model
    def _order_fields(self, ui_order):
        order_fields = super(PosOrder, self)._order_fields(ui_order)
        order_fields['lane_id'] = ui_order.get('lane_id', False)
        return order_fields

    @api.model
    def _payment_fields(self, ui_paymentline):
        fields = super(PosOrder, self)._payment_fields(ui_paymentline)

        fields.update({
            'lane_id': ui_paymentline.get('lane_id'),
        })
        return fields
