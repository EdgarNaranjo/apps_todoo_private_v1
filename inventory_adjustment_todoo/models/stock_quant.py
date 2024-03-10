# Copyright 2024-TODAY Todooweb (<http://www.todooweb.com>).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, models, tools, _, fields


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    past_inventory_date = fields.Datetime(
        string="Past Inventory Date",
        help="Date of the past inventory"
    )
    past_inventory_quantity = fields.Float(
        string="Past Inventory Quantity"
    )

    @api.model
    def _get_inventory_fields_write(self):
        """
        Inherit the standard function to add past_inventory_date and past_inventory_quantity to the dictionary of
        fields the user can edit when he wants to edit a stock.quant.
        """
        res = super()._get_inventory_fields_write()
        res += ['past_inventory_date', 'past_inventory_quantity']
        return res

    @api.model
    def _get_inventory_fields_create(self):
        """ Returns a list of fields user can edit when he want to create a quant in `inventory_mode`.
        """
        res = super()._get_inventory_fields_create()
        res += ['past_inventory_date', 'past_inventory_quantity']
        return res

    @api.model_create_multi
    def create(self, vals):
        res = super(StockQuant, self).create(vals)
        if res:
            stock_line_env = self.env['stock.move.line']
            for val in vals:
                if all(key in val for key in ['past_inventory_date', 'past_inventory_quantity']):
                    if val['past_inventory_date'] and val['past_inventory_quantity']:
                        past_date = val['past_inventory_date']
                        past_quantity = val['past_inventory_quantity']
                        stock_lines = stock_line_env.search([('date', '>=', past_date),
                                                             ('product_id', '=', val['product_id']),
                                                             ('state', '=', 'done')])
                        stock_to_rest = sum(
                            stock_lines.filtered(lambda l: l.location_dest_id.id == val['location_id']).mapped('qty_done'))
                        stock_to_add = sum(
                            stock_lines.filtered(lambda l: l.location_id.id == val['location_id']).mapped('qty_done'))
                        quant = res.quantity + stock_to_add - stock_to_rest
                        difference = past_quantity - quant
                        res.inventory_quantity = res.quantity + difference
        return res

    def write(self, vals):
        stock_line_env = self.env['stock.move.line']
        if all(key in vals for key in ['past_inventory_date', 'past_inventory_quantity']):
            if vals['past_inventory_date'] and vals['past_inventory_quantity']:
                past_date = vals['past_inventory_date']
                past_quantity = vals['past_inventory_quantity']
                for rec in self:
                    stock_lines = stock_line_env.search([('date', '>=', past_date),
                                                         ('product_id', '=', rec.product_id.id),
                                                         ('state', '=', 'done')])
                    stock_to_rest = sum(
                        stock_lines.filtered(lambda l: l.location_dest_id == rec.location_id).mapped('qty_done'))
                    stock_to_add = sum(
                        stock_lines.filtered(lambda l: l.location_id == rec.location_id).mapped('qty_done'))
                    quant = rec.quantity + stock_to_add - stock_to_rest
                    difference = past_quantity - quant
                    rec.inventory_quantity = rec.quantity + difference
                    vals['inventory_quantity'] = rec.inventory_quantity
        res = super(StockQuant, self).write(vals)
        return res

    def _get_inventory_move_values(self, qty, location_id, location_dest_id, out=False):
        """
        Inherit the standard function to add past_inventory_date and past_inventory_quantity to the corresponding
        stock.move.line when user set a new quantity (stock.quant).
        """
        res = super(StockQuant, self)._get_inventory_move_values(qty, location_id, location_dest_id, out=False)
        if self.past_inventory_date and self.past_inventory_quantity:
            if res['move_line_ids'] and res['move_line_ids'][0]:
                res['move_line_ids'][0][2].update({
                    'past_inventory_date': self.past_inventory_date,
                    'past_inventory_quantity': self.past_inventory_quantity
                })
        return res

    def _apply_inventory(self):
        """
        Inherit the standard function to reset past_inventory_date and past_inventory_quantity after the stock.quant be
        applied.
        """
        res = super(StockQuant, self)._apply_inventory()
        self.write({'past_inventory_date': False, 'past_inventory_quantity': 0})
        return res

    def action_set_inventory_quantity_to_zero(self):
        super(StockQuant, self).action_set_inventory_quantity_to_zero()
        self.past_inventory_date = False
        self.past_inventory_quantity = 0


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    past_inventory_date = fields.Datetime(
        string="Past Inventory Date",
        help="Date of the past inventory"
    )
    past_inventory_quantity = fields.Float(
        string="Past Inventory Quantity"
    )


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _action_done(self, cancel_backorder=False):
        res = super(StockMove, self)._action_done(cancel_backorder)
        if res:
            if self.move_line_ids.mapped('past_inventory_date')[0]:
                self.date = self.move_line_ids.mapped('past_inventory_date')[0]
                self.move_line_ids.date = self.move_line_ids.mapped('past_inventory_date')[0]
        return res
