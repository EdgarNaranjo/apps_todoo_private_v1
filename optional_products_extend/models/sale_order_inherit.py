# Copyright 2024-TODAY Todooweb (www.todooweb.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import models, fields, api, _


class SaleOrderOption(models.Model):
    _inherit = 'sale.order.option'

    margin = fields.Float(
        "Margen", compute='_compute_margin',
        digits='Product Price', store=True, groups="base.group_user", precompute=True)
    margin_percent = fields.Float(
        "Margen (%)", compute='_compute_margin', store=True, groups="base.group_user", precompute=True)
    purchase_price = fields.Float(
        string="Coste",
        digits='Product Price',
        groups="base.group_user")
    currency_id = fields.Many2one(
        related='order_id.currency_id',
        depends=['order_id.currency_id'],
        store=True, precompute=True)
    price_subtotal = fields.Monetary(
        string="Subtotal",
        compute='_compute_amount',
        store=True, precompute=True, currency_field='currency_id')

    @api.onchange('product_id', 'uom_id')
    def _compute_purchase_price(self):
        for line in self:
            if not line.product_id:
                line.purchase_price = 0.0
                continue
            product_cost = line.product_id.standard_price
            line.purchase_price = line.uom_id._compute_price(product_cost, line.product_id.uom_id)

    @api.depends('price_subtotal', 'quantity', 'purchase_price')
    def _compute_margin(self):
        for line in self:
            line.margin = line.price_subtotal - (line.purchase_price * line.quantity)
            line.margin_percent = line.price_subtotal and line.margin / line.price_subtotal

    @api.depends('quantity', 'discount', 'price_unit')
    def _compute_amount(self):
        for line in self:
            discount = (line.quantity * line.price_unit * line.discount) / 100
            line.price_subtotal = line.quantity * line.price_unit - discount
