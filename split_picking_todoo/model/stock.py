# -*- coding: utf-8 -*-
from collections import defaultdict

from odoo import api, models, fields, _
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
    product_qty = fields.Float("Demanda inicial")
    reserved_available = fields.Float("Reservado")

    @api.onchange('move_lines')
    def onchange_move_lines(self):
        if self.move_lines:
            if self.move_lines.product_qty:
                self.product_qty = self.move_lines.product_qty
                self.reserved_available = self.move_lines.reserved_availability


class PartPickingWizard(models.TransientModel):
    _name = 'part.picking.wizard'
    _description = 'Part Picking Wizard'

    picking_ids = fields.Many2many('stock.picking', 'part_wizard_picking_rel', 'part_id', 'picking_id', 'Stock Model Wizard')
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
                        dict_first['reserved_available'] = mov.forecast_availability
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
        if not self.picking_ids:
            return
        picking = self.picking_ids[0]
        quantity_lists = defaultdict(list)
        list_fault = []
        for first in self.first_part_ids:
            if first.quantity in range(1, 7):
                quantity_lists[first.quantity].append(first)
            else:
                list_fault.append(first)
        if list_fault:
            raise ValidationError(
                "With the current system you can start with up to 6 Delivery Notes. Specify the Delivery Note No. for each line.")
        for quantity, items in quantity_lists.items():
            obj_create_picking = self.create_picking(picking, items)
            if obj_create_picking:
                _logger.info('Creado picking "%s"' % obj_create_picking.name)
                obj_assigned_picking = self.assigned_picking(obj_create_picking, items)
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
        if len(self.move_ids) < 2:
            raise ValidationError('To split a delivery note you need a minimum of 2 lines')
        if self.picking_type_id.code != 'outgoing':
            raise ValidationError('You cannot split a delivery note of type "IN"')
        move_ids = self.move_ids.ids
        context = {
            'default_picking_ids': self.ids,
            'move': move_ids,
            'default_quantity_all': len(move_ids)
        }
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
