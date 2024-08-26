# Copyright 2024-TODAY Todooweb (www.todooweb.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    is_return_picking = fields.Boolean('Picking return', help='Have a return picking', compute='_get_picking_return')
    task_id = fields.Many2one('project.task', 'Work order')
    sequence_name = fields.Char(related='task_id.sequence_name')
    check_service = fields.Boolean('External service')

    @api.depends('picking_ids')
    def _get_picking_return(self):
        for record in self:
            record.is_return_picking = False
            pickings = record.picking_ids.filtered(lambda e: e.picking_type_id.code == 'outgoing')
            if record.picking_ids and pickings:
                if any(pickings.mapped('move_ids').mapped('origin_returned_move_id')):
                    record.is_return_picking = True

    @api.constrains('task_id')
    def check_task_id(self):
        for record in self:
            if record.task_id:
                if record.order_line:
                    record.order_line.task_id = record.task_id.id


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    task_id = fields.Many2one('project.task', 'Work order')
    code_partner = fields.Char('Ref.', compute='_get_code_by_purchase_product')

    @api.depends('product_id', 'product_id.seller_ids', 'partner_id')
    def _get_code_by_purchase_product(self):
        env_suppl = self.env['product.supplierinfo']
        for record in self:
            record.code_partner = ''
            if record.product_id:
                tmp_by_product = record.product_id.product_tmpl_id
                obj_suppl = env_suppl.search([('partner_id', '=', record.partner_id.id),
                                              '|', ('product_id', '=', record.product_id.id),
                                              '|', ('product_tmpl_id', '=', record.product_id.id),
                                              ('product_tmpl_id', '=', tmp_by_product.id)], limit=1)
                if obj_suppl:
                    record.code_partner = obj_suppl.product_code if obj_suppl.product_code else ''


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _make_po_get_domain(self, company_id, values, partner):
        domain = super(StockRule, self)._make_po_get_domain(company_id, values, partner)
        domain += (('check_service', '=', True),)
        return domain
