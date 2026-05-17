# Copyright 2025-TODAY Todooweb (www.todooweb.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    past_inventory_date = fields.Datetime(
        string="Past Inventory Date",
        help="Set a past date to calculate inventory as it was on that date. "
             "Leave empty for a standard real-time adjustment.",
    )
    past_inventory_quantity = fields.Float(
        string="Past Inventory Quantity",
        help="Quantity that existed on the selected past inventory date.",
    )

    @api.constrains('past_inventory_date')
    def _check_past_inventory_date(self):
        for rec in self:
            if rec.past_inventory_date and rec.past_inventory_date > fields.Datetime.now():
                raise ValidationError(
                    _("Past Inventory Date cannot be in the future. "
                      "Please select a date in the past.")
                )

    @api.model
    def _get_inventory_fields_write(self):
        res = super()._get_inventory_fields_write()
        res += ['past_inventory_date', 'past_inventory_quantity']
        return res

    @api.model
    def _get_inventory_fields_create(self):
        res = super()._get_inventory_fields_create()
        res += ['past_inventory_date', 'past_inventory_quantity']
        return res

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        stock_line_env = self.env['stock.move.line']
        for quant, vals in zip(res, vals_list):
            if vals.get('past_inventory_date') and vals.get('past_inventory_quantity'):
                past_date = vals['past_inventory_date']
                past_quantity = vals['past_inventory_quantity']
                stock_lines = stock_line_env.search([
                    ('date', '>=', past_date),
                    ('product_id', '=', vals['product_id']),
                    ('state', '=', 'done'),
                ])
                stock_to_rest = sum(
                    stock_lines.filtered(
                        lambda l: l.location_dest_id.id == vals['location_id']
                    ).mapped('quantity')
                )
                stock_to_add = sum(
                    stock_lines.filtered(
                        lambda l: l.location_id.id == vals['location_id']
                    ).mapped('quantity')
                )
                quant_qty = quant.quantity + stock_to_add - stock_to_rest
                quant.inventory_quantity = quant.quantity + (past_quantity - quant_qty)
        return res

    def write(self, vals):
        stock_line_env = self.env['stock.move.line']
        if vals.get('past_inventory_date') and vals.get('past_inventory_quantity'):
            past_date = vals['past_inventory_date']
            past_quantity = vals['past_inventory_quantity']
            for rec in self:
                stock_lines = stock_line_env.search([
                    ('date', '>=', past_date),
                    ('product_id', '=', rec.product_id.id),
                    ('state', '=', 'done'),
                ])
                stock_to_rest = sum(
                    stock_lines.filtered(lambda l: l.location_dest_id == rec.location_id).mapped('quantity')
                )
                stock_to_add = sum(
                    stock_lines.filtered(lambda l: l.location_id == rec.location_id).mapped('quantity')
                )
                quant_qty = rec.quantity + stock_to_add - stock_to_rest
                rec.inventory_quantity = rec.quantity + (past_quantity - quant_qty)
                vals['inventory_quantity'] = rec.inventory_quantity
        return super().write(vals)

    def _get_inventory_move_values(self, qty, location_id, location_dest_id,
                                   package_id=False, package_dest_id=False):
        res = super()._get_inventory_move_values(
            qty, location_id, location_dest_id,
            package_id=package_id, package_dest_id=package_dest_id,
        )
        if self.past_inventory_date and self.past_inventory_quantity:
            if res.get('move_line_ids') and res['move_line_ids'][0]:
                res['move_line_ids'][0][2].update({
                    'past_inventory_date': self.past_inventory_date,
                    'past_inventory_quantity': self.past_inventory_quantity,
                })
        return res

    def _apply_inventory(self, date=None):
        res = super()._apply_inventory(date)
        self.write({'past_inventory_date': False, 'past_inventory_quantity': 0})
        return res

    def action_set_inventory_quantity_zero(self):
        super().action_set_inventory_quantity_zero()
        self.past_inventory_date = False
        self.past_inventory_quantity = 0


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    past_inventory_date = fields.Datetime(
        string="Past Inventory Date",
        help="Date of the past inventory",
    )
    past_inventory_quantity = fields.Float(string="Past Inventory Quantity")


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _action_done(self, cancel_backorder=False):
        res = super()._action_done(cancel_backorder)
        if res:
            past_dates = self.move_line_ids.mapped('past_inventory_date')
            if past_dates and past_dates[0]:
                self.date = past_dates[0]
                self.move_line_ids.date = past_dates[0]
        return res
