# coding: utf-8
from odoo import fields, models, api
import logging
_logger = logging.getLogger(__name__)


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    def do_create_parent(self, obj_bom_line):
        val_ok = False
        list_quant = []
        list_child = []
        dict_quant = {
            'product_id': False,
            'company_id': False,
            'location_id': False,
            'quantity': 0,
        }
        dict_init = {
            'product_id': False,
            'company_id': False,
            'location_id': False,
            'quantity': 0,
        }
        if obj_bom_line:
            list_bom = [bom.bom_id for bom in obj_bom_line]
        if list_bom:
            for bom in list_bom:
                parent_product = bom.product_tmpl_id
                _logger.info('Parent %s' % str(parent_product))
                list_child = [bom_item.product_id.id for bom_item in bom.bom_line_ids]
                if list_child:
                    obj_quant_ids = self.env['stock.quant'].search([('product_id', 'in', list_child), ('company_id', '!=', False)])
                    if obj_quant_ids:
                        if len(obj_quant_ids) < len(list_child) or any(obj_quant for obj_quant in obj_quant_ids if obj_quant.quantity == 0):
                            val_ok = False
                        else:
                            for obj_quant in obj_quant_ids:
                                _logger.info('Tengo quant %s' % str(obj_quant.product_id.name))
                                val_quant = obj_quant.quantity / [bom_line.product_qty for bom_line in bom.bom_line_ids if bom_line.product_id == obj_quant.product_id][0]
                                if val_quant:
                                    list_quant.append(val_quant)
                                    val_ok = True
                quant_update = 0
                if val_ok and list_quant:
                    quant_update = min(list_quant)
                    if int(quant_update) >= 1:
                        dict_quant['quantity'] = int(quant_update)
                        obj_product_ids = self.env['product.product'].search([('product_tmpl_id', '=', parent_product.id)])
                        if obj_product_ids:
                            for obj_product in obj_product_ids:
                                obj_parent_quant_ids = self.env['stock.quant'].search([('product_id', '=', obj_product.id), ('company_id', '!=', False)])
                                if not obj_parent_quant_ids:
                                    _logger.info('No tengo quant padre')
                                    dict_quant['product_id'] = obj_product.id
                                    dict_quant['company_id'] = self.env.user.company_id.id
                                    obj_locations_ids = self.env['stock.location'].search([('usage', '=', 'internal'), ('company_id', '=', self.env.user.company_id.id)])
                                    if obj_locations_ids:
                                        location = obj_locations_ids[0]
                                        dict_quant['location_id'] = location.id
                                    if len(dict_quant) > 0:
                                        # eliminar los que tengan valor False
                                        dict_quant = dict(filter(lambda x: x[1] != False, dict_quant.items()))
                                        _logger.info('Dict quant %s' % str(dict_quant))
                                        obj_create = self.env['stock.quant'].create(dict_quant)
                                        if obj_create:
                                            _logger.info(
                                                'Creado quant del padre %s' % str(obj_create.product_id.name))
                                    dict_quant.update(dict_init)
                                else:
                                    _logger.info('Escribir en quant del producto %s' % str(obj_parent_quant_ids[0].product_id.name))
                                    obj_parent_quant_ids[0].write({'quantity': int(quant_update)})

    @api.model
    def create(self, vals):
        res = super(StockQuant, self).create(vals)
        if res['product_id'] and res['quantity'] > 0:
            product = res['product_id']
            _logger.info("Comprobar si es producto hijo %s" % product.name)
            obj_bom_line = self.env['mrp.bom.line'].search([('product_id', '=', product.id)])
            if obj_bom_line:
                _logger.info('Soy product hijo de una lista materiales')
                self.do_create_parent(obj_bom_line)
        return res

    def write(self, vals):
        request = super(StockQuant, self).write(vals)
        if self.product_id and self.quantity > 0:
            product = self.product_id
            obj_bom_line = self.env['mrp.bom.line'].search([('product_id', '=', product.id)])
            if obj_bom_line:
                _logger.info('Soy product hijo de una lista materiales')
                self.do_create_parent(obj_bom_line)
        return request
