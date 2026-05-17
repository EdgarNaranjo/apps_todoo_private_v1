# Copyright 2025-TODAY Todooweb (www.todooweb.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
from odoo import api, models

_logger = logging.getLogger(__name__)


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    def do_create_parent(self, obj_bom_line):
        val_ok = False
        list_quant = []
        dict_quant = {'product_id': False, 'company_id': False, 'location_id': False, 'quantity': 0}
        dict_init = dict(dict_quant)
        if not obj_bom_line:
            return
        list_bom = [bom.bom_id for bom in obj_bom_line]
        for bom in list_bom:
            parent_product = bom.product_tmpl_id
            list_child = [bl.product_id.id for bl in bom.bom_line_ids]
            if not list_child:
                continue
            obj_quant_ids = self.env['stock.quant'].search([
                ('product_id', 'in', list_child),
                ('company_id', '!=', False),
            ])
            if obj_quant_ids:
                if len(obj_quant_ids) < len(list_child) or any(q for q in obj_quant_ids if q.quantity == 0):
                    val_ok = False
                else:
                    for obj_quant in obj_quant_ids:
                        bom_qty = [bl.product_qty for bl in bom.bom_line_ids
                                   if bl.product_id == obj_quant.product_id]
                        if bom_qty:
                            val_quant = obj_quant.quantity / bom_qty[0]
                            if val_quant:
                                list_quant.append(val_quant)
                                val_ok = True
            if val_ok and list_quant:
                quant_update = min(list_quant)
                if int(quant_update) >= 1:
                    dict_quant['quantity'] = int(quant_update)
                    obj_product_ids = self.env['product.product'].search([
                        ('product_tmpl_id', '=', parent_product.id)
                    ])
                    for obj_product in obj_product_ids:
                        obj_parent_quant_ids = self.env['stock.quant'].search([
                            ('product_id', '=', obj_product.id),
                            ('company_id', '!=', False),
                        ])
                        if not obj_parent_quant_ids:
                            dict_quant['product_id'] = obj_product.id
                            dict_quant['company_id'] = self.env.user.company_id.id
                            obj_locations_ids = self.env['stock.location'].search([
                                ('usage', '=', 'internal'),
                                ('company_id', '=', self.env.user.company_id.id),
                            ])
                            if obj_locations_ids:
                                dict_quant['location_id'] = obj_locations_ids[0].id
                            clean = {k: v for k, v in dict_quant.items() if v is not False}
                            self.env['stock.quant'].create(clean)
                        else:
                            obj_parent_quant_ids[0].write({'quantity': int(quant_update)})
                    dict_quant.update(dict_init)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for res in records:
            if res.product_id and res.quantity > 0:
                obj_bom_line = self.env['mrp.bom.line'].search([('product_id', '=', res.product_id.id)])
                if obj_bom_line:
                    self.do_create_parent(obj_bom_line)
        return records

    def write(self, vals):
        result = super().write(vals)
        if self.product_id and self.quantity > 0:
            obj_bom_line = self.env['mrp.bom.line'].search([('product_id', '=', self.product_id.id)])
            if obj_bom_line:
                self.do_create_parent(obj_bom_line)
        return result
