# Copyright 2025-TODAY Todooweb (www.todooweb.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import _, fields, models, api
from odoo.exceptions import UserError


class StockPickingWizard(models.TransientModel):
	_name = "stock.picking.wizard"
	_description = "Stock Picking Wizard"
	_rec_name = 'repair_id'

	repair_id = fields.Many2one(
		comodel_name='repair.order',
		string='Repair')
	partner_id = fields.Many2one(
		comodel_name='res.partner',
		string='Partner')
	product_id = fields.Many2one(
		comodel_name='product.product',
		string='Product')
	check_in = fields.Boolean(related='repair_id.check_in')
	check_out = fields.Boolean(related='repair_id.check_out')
	location_id = fields.Many2one(
		comodel_name='stock.location',
		string='Location')
	location_dest_id = fields.Many2one(
		comodel_name="stock.location",
		string="Destination location"
	)
	quantity = fields.Float(
		string="Quantity to transfer",
		required=True, default=1
	)

	@api.onchange('repair_id', 'location_id')
	def onchange_repair_id(self):
		if not self.repair_id and self._context.get('active_id'):
			self.repair_id = self._context['active_id']
		if self.repair_id:
			supplier_location = self.env['stock.location'].search([('usage', '=', 'supplier')], limit=1)
			obj_repair = self.repair_id
			self.partner_id = obj_repair.partner_id.id
			self.product_id = obj_repair.product_id.id
			if not self.check_in:
				self.location_dest_id = obj_repair.location_id.id
				self.location_id = supplier_location.id if supplier_location else False
			elif not self.check_out:
				self.location_id = obj_repair.location_id.id
				self.location_dest_id = supplier_location.id if supplier_location else False

	def _get_picking_type(self):
		self.ensure_one()
		if not self.check_in:
			return self.location_dest_id.warehouse_id.in_type_id
		if not self.check_out:
			return self.location_id.warehouse_id.out_type_id

	def _prepare_picking_vals(self):
		return {
			"partner_id": self.partner_id.id,
			"user_id": False,
			"picking_type_id": self._get_picking_type().id,
			"move_type": "direct",
			"location_id": self.location_id.id,
			"location_dest_id": self.location_dest_id.id,
			"origin": self.repair_id.name
		}

	def _prepare_stock_move_vals(self, picking):
		self.ensure_one()
		return {
			"name": self.product_id.name,
			"product_id": self.product_id.id,
			"location_id": self.location_id.id,
			"location_dest_id": self.location_dest_id.id,
			"picking_id": picking.id,
			"state": "draft",
			"company_id": picking.company_id.id,
			"picking_type_id": self._get_picking_type().id,
			"product_uom_qty": self.quantity,
			"product_uom": self.product_id.uom_id.id
		}

	def action_create_picking_in(self):
		self.ensure_one()
		return self.action_create_picking()

	def action_create_picking_out(self):
		self.ensure_one()
		return self.action_create_picking()

	def action_create_picking(self):
		if self.quantity <= 0:
			raise UserError(_("Quantity to transfer must be greater than 0."))
		picking = self.env["stock.picking"].create(self._prepare_picking_vals())
		self.env["stock.move"].create(self._prepare_stock_move_vals(picking))
		picking.action_assign()
		self.repair_id.write({"picking_ids": [(4, picking.id)]})
		if self.repair_id.state == 'draft':
			self.repair_id.write({'state': 'pick'})
		return {
			'name': picking.name,
			'type': 'ir.actions.act_window',
			'view_mode': 'form',
			'res_model': 'stock.picking',
			'view_id': self.env.ref('stock.view_picking_form').id,
			'res_id': picking.id,
			'target': 'current',
		}

