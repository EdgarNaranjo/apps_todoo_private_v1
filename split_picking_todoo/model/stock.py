# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
from odoo.addons.base.models.decimal_precision import dp
from odoo.exceptions import UserError, AccessError, ValidationError

import logging
_logger = logging.getLogger(__name__)


class FirstPickingWizard(models.Model):
    _name = 'first.picking.wizard'
    _description = 'First Picking Wizard'
    _rec_name = 'move_lines'

    move_lines = fields.Many2one('stock.move', string='Stock Move Wizard')
    product_id = fields.Many2one('product.product', string='Linea Albaran')
    quantity = fields.Integer("No. Albaran")
    product_qty = fields.Float("Demanda inicial", digits=dp.get_precision('Product Unit of Measure'))
    reserved_available = fields.Float("Reservado", digits=dp.get_precision('Product Unit of Measure'))

    @api.onchange('move_lines')
    def onchange_move_lines(self):
        if self.move_lines:
            if self.move_lines.product_qty:
                self.product_qty = self.move_lines.product_qty
                self.reserved_available = self.move_lines.reserved_availability


class PartPickingWizard(models.TransientModel):
    _name = 'part.picking.wizard'
    _description = 'Part Picking Wizard'

    picking_ids = fields.Many2many('stock.picking', 'part_wizard_picking_rel', 'part_id', 'picking_id','Stock Model Wizard')
    first_part_ids = fields.Many2many('first.picking.wizard', 'firs_wizard_picking_rel', 'firs_id', 'picking_id', 'First Parts')
    quantity_all = fields.Integer("Partin en")

    @api.depends('picking_ids')
    @api.onchange('picking_ids')
    def onchange_default_picking(self):
        list_first = []
        dict_first = {
            'move_lines': False,
            'product_id': False,
            'quantity': 0,
        }
        dict_init = {
            'move_lines': False,
            'product_id': False,
            'quantity': 0,
        }
        if self.env.context.get('move'):
            move_ids = self.env.context.get('move')
            if move_ids:
                obj_mov = self.env['stock.move'].search([('id', 'in', move_ids)])
                if obj_mov:
                    for mov in obj_mov:
                        dict_first['move_lines'] = mov.id
                        dict_first['product_id'] = mov.product_id.id
                        dict_first['product_qty'] = mov.product_qty
                        dict_first['reserved_available'] = mov.reserved_availability
                        if len(dict_first) > 0:
                            # eliminar los que tengan valor False
                            dict_first = dict(filter(lambda x: x[1] != False, dict_first.items()))
                            create_first = self.env['first.picking.wizard'].create(dict_first)
                            if create_first:
                                if create_first.id not in list_first:
                                    list_first.append(create_first.id)
                        dict_first.update(dict_init)
        if list_first:
            self.first_part_ids = list_first

    def action_part_picking(self):
        list_1 = []
        list_2 = []
        list_3 = []
        list_4 = []
        list_5 = []
        list_6 = []
        list_fault = []
        if self.picking_ids:
            picking = self.picking_ids[0]
        if self.first_part_ids:
            if len(self.first_part_ids) >= self.quantity_all:
                raise ValidationError("La cantidad de lineas debe ser menor a la cantidad del Albaran original.")
            for first in self.first_part_ids:
                if first.quantity == 1:
                    if first not in list_1:
                        list_1.append(first)
                elif first.quantity == 2:
                    if first not in list_2:
                        list_2.append(first)
                elif first.quantity == 3:
                    if first not in list_3:
                        list_3.append(first)
                elif first.quantity == 4:
                    if first not in list_4:
                        list_4.append(first)
                elif first.quantity == 5:
                    if first not in list_5:
                        list_5.append(first)
                elif first.quantity == 6:
                    if first not in list_6:
                        list_6.append(first)
                else:
                    list_fault.append(first)
        if list_fault:
            raise ValidationError(
                "Con el actual sistema puedes partir hasta en 6 Albaranes. Especifique el No. Albaran por cada linea.")
        else:
            if picking:
                if list_1:
                    obj_create_picking = self.create_picking(picking, list_1)
                    if obj_create_picking:
                        _logger.info('Creado picking "%s"' % obj_create_picking.name)
                        obj_assigned_picking = self.assigned_picking(obj_create_picking, list_1)
                        if obj_assigned_picking:
                            _logger.info('Asignado picking a Movement')
                if list_2:
                    obj_create_picking = self.create_picking(picking, list_2)
                    if obj_create_picking:
                        _logger.info('Creado picking "%s"' % obj_create_picking.name)
                        obj_assigned_picking = self.assigned_picking(obj_create_picking, list_2)
                        if obj_assigned_picking:
                            _logger.info('Asignado picking a Movement')
                if list_3:
                    obj_create_picking = self.create_picking(picking, list_3)
                    if obj_create_picking:
                        _logger.info('Creado picking "%s"' % obj_create_picking.name)
                        obj_assigned_picking = self.assigned_picking(obj_create_picking, list_3)
                        if obj_assigned_picking:
                            _logger.info('Asignado picking a Movement')
                if list_4:
                    obj_create_picking = self.create_picking(picking, list_4)
                    if obj_create_picking:
                        _logger.info('Creado picking "%s"' % obj_create_picking.name)
                        obj_assigned_picking = self.assigned_picking(obj_create_picking, list_4)
                        if obj_assigned_picking:
                            _logger.info('Asignado picking a Movement')
                if list_5:
                    obj_create_picking = self.create_picking(picking, list_5)
                    if obj_create_picking:
                        _logger.info('Creado picking "%s"' % obj_create_picking.name)
                        obj_assigned_picking = self.assigned_picking(obj_create_picking, list_5)
                        if obj_assigned_picking:
                            _logger.info('Asignado picking a Movement')
                if list_6:
                    obj_create_picking = self.create_picking(picking, list_6)
                    if obj_create_picking:
                        _logger.info('Creado picking "%s"' % obj_create_picking.name)
                        obj_assigned_picking = self.assigned_picking(obj_create_picking, list_6)
                        if obj_assigned_picking:
                            _logger.info('Asignado picking a Movement')
            _logger.info('Picking "%s" partido' % picking.name)

    def create_picking(self, picking, list_q):
        val_q = 0
        if picking:
            if list_q:
                for qua in list_q:
                    if qua.quantity == 1:
                        val_q = 1
                    if qua.quantity == 2:
                        val_q = 2
                    if qua.quantity == 3:
                        val_q = 3
                    if qua.quantity == 4:
                        val_q = 4
                    if qua.quantity == 5:
                        val_q = 5
                    if qua.quantity == 6:
                        val_q = 6
            pick = {
                'picking_type_id': picking.picking_type_id.id,
                'partner_id': picking.partner_id.id,
                'origin': picking.origin,
                'location_dest_id': picking.location_dest_id.id,
                'location_id': picking.location_id.id,
                'state': picking.state,
                'quantity': val_q

            }
            create_picking = self.env['stock.picking'].create(pick)
        return create_picking

    def assigned_picking(self, obj_create_picking, list_first):
        if list_first:
            for first in list_first:
                if first.quantity == obj_create_picking.quantity:
                    first.move_lines.write({'picking_id': obj_create_picking.id})
                    first.move_lines.move_line_ids.write({'picking_id': obj_create_picking.id})
        return True


class Stock(models.Model):
    _inherit = "stock.picking"

    quantity = fields.Integer("Albaran Partido")

    def action_part_picking(self):
        list_move = []
        for picking in self:
            if len(picking.move_line_ids) < 2:
                raise ValidationError('Para partir un albaran se necesita minimo 2 lineas')
            if not picking.picking_type_id.code == 'outgoing':
                raise ValidationError('No puede partir un albaran de tipo "IN"')
            else:
                for line in picking.move_line_ids:
                    if line.id not in list_move:
                        list_move.append(line.id)
                context = ({'default_picking_ids': picking.ids, 'move': list_move, 'default_quantity_all': len(picking.move_line_ids)})
                view = self.env.ref('split_picking_todoo.part_picking_wizard_form2')
                return {
                    'view_type': 'form',
                    'view_mode': 'form',
                    'target': 'new',
                    'res_model': 'part.picking.wizard',
                    'view_id': view.id,
                    'views': [(view.id, 'form')],
                    'type': 'ir.actions.act_window',
                    'context': context,
                }
