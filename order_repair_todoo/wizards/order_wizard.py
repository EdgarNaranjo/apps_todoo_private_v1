# Copyright 2025-TODAY Todooweb (www.todooweb.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import _, fields, models, api


class RepairOrderWizard(models.TransientModel):
	_name = "repair.order.wizard"
	_description = "Repair Order Wizard"
	_rec_name = 'product_id'

	repair_id = fields.Many2one(
		comodel_name='repair.order',
		string='Repair'
	)
	product_filter_ids = fields.Many2many(
		'product.product',
		compute='_get_product_ids'
	)
	product_id = fields.Many2one(
		comodel_name='product.product',
		string='Product'
	)
	quantity = fields.Float(
		string="Quantity to transfer",
		required=True,
		default=1
	)

	@api.depends('repair_id')
	def _get_product_ids(self):
		env_product = self.env['product.product']
		for record in self:
			record.product_filter_ids = env_product.search([
				('unit', '!=', False),
				('id', '!=', record.repair_id.product_id.id)]
			)

	def action_create_order(self):
		if self.repair_id:
			repair_copy = self.repair_id.copy({
				'product_id': self.product_id.id,
				'product_qty': self.quantity,
				'parent_id': self.repair_id.id
			})
			if repair_copy:
				repair_copy.message_post(
					body=_('This repair has been created from: ') + self.repair_id._get_html_link()
				)
