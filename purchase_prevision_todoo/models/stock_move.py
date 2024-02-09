# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)


class StockWarehouseOrderpoint(models.Model):
    _inherit = "stock.warehouse.orderpoint"

    @api.onchange('product_id', 'route_id', 'product_min_qty')
    def onchange_route_and_min(self):
        env_line = self.env['sale.order.line']
        env_parameter = self.env['ir.config_parameter']
        month = env_parameter.sudo().get_param('purchase.set_month')
        multiple = env_parameter.sudo().get_param('purchase.value_multiple')
        previous_month = fields.Date.today() + relativedelta(months=-int(month))
        if self.product_id:
            if self.product_id.purchase_ok:
                route = self.product_id.route_ids.filtered(lambda e: not e.sale_selectable)
                self.route_id = route.id if route else False
            obj_lines = env_line.search([('create_date', '>=', previous_month), ('state', 'not in', ['draft', 'cancel']), '|', ('product_template_id', '=', self.product_id.id), ('product_id', '=', self.product_id.product_tmpl_id.id)])
            if obj_lines:
                self.product_min_qty = round((sum(obj_lines.mapped('product_uom_qty')) / len(obj_lines)) * int(multiple), 0)
