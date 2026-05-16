# Copyright 2024-TODAY Todooweb (www.todooweb.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import models, fields, api, _


class MaterialSelection(models.TransientModel):
    _name = 'material.selection.wizard'
    _description = 'Wizard to select the materials to be process'

    material_filter_ids = fields.Many2many(
        comodel_name='ot.material.line',
        compute='_compute_material_ids'
    )
    material_ids = fields.Many2many(
        comodel_name='ot.material.line',
        relation='task_material_selector_rel',
        column1='select_material_id',
        column2='material_id',
        string="Materials",
        copy=False
    )
    task_id = fields.Many2one(
        string='OT',
        comodel_name='project.task'
    )

    def action_quotation_sale(self, line):
        env_order = self.env['sale.order']
        env_order_line = self.env['sale.order.line']
        pricelist = self.task_id.partner_id.property_product_pricelist
        order_vals = {
            'partner_id': line.task_id.partner_id.id,
            'origin': line.task_id.name,
            'date_order': fields.Date.today(),
            'partner_shipping_id': line.task_id.partner_id.id,
            'pricelist_id': pricelist.id if pricelist else False,
            'fiscal_position_id': line.task_id.partner_id.property_account_position_id.id
            if line.task_id.partner_id.property_account_position_id else False,
            'currency_id': line.task_id.currency_id.id,
            'user_id': line.env.uid,
            'company_id': line.task_id.company_id.id,
            'analytic_account_id': line.task_id.analytic_account_id.id,
            'tag_ids': line.task_id.tag_order_ids.ids,
        }
        sale_order = env_order.create(order_vals)
        if sale_order:
            if not self.task_id.order_id:
                self.task_id.order_id = sale_order.id
            line_vals = {
                'name': line.name,
                'product_id': line.product_id.id,
                'price_unit': line.product_id.lst_price,
                'product_uom': line.product_uom.id,
                'company_id': line.task_id.company_id.id,
                'product_uom_qty': line.product_qty,
                'material_id': line.id,
                'tax_id': [(6, 0, line.product_id.taxes_id.ids)],
                'order_id': sale_order.id
            }
            # analytic = self.task_id.analytic_account_id
            # line_vals.update({'analytic_distribution': {analytic.id: 100.0}})
            create_line = env_order_line.create(line_vals)
            if create_line:
                line.state = 'process'
                line.sale_line_id = create_line.id
            sale_msg = _('Created sale order %s related with the task.', sale_order._get_html_link())
            self.task_id.message_post(body=sale_msg)
            sale_order._recompute_prices()

    def action_select_materials_to_process(self):
        lines_bill = self.material_ids.filtered(lambda e: e.is_billable)
        picking_lines = self.material_ids.filtered(lambda e: not e.is_billable)
        if lines_bill:
            if self._context.get('mark_done'):
                lines_bill.state = 'done'
            else:
                for line in lines_bill:
                    if self.task_id.order_id:
                        line._verify_so_line()
                    else:
                        self.action_quotation_sale(line)
        if picking_lines:
            if self._context.get('mark_done'):
                picking_lines.state = 'done'
            else:
                self.create_picking(picking_lines)

    def create_picking(self, picking_lines):
        picking_by_origin = self._group_picking_by_origin(picking_lines)
        if picking_by_origin:
            for origin_key, origin_value in picking_by_origin.items():
                picking_by_destination = self._group_picking_by_destination(origin_value)
                if picking_by_destination:
                    for destination_key, destination_value in picking_by_destination.items():
                        self.action_create_picking(origin_key, destination_key, destination_value)

    def _group_picking_by_origin(self, picking_lines):
        """"
        Function to group the line by origin
        """
        picking_by_origin = {}
        for record in picking_lines:
            origin = record.location_id
            if origin not in picking_by_origin:
                picking_by_origin[origin] = [record]
            else:
                picking_by_origin[origin].append(record)
        return picking_by_origin

    def _group_picking_by_destination(self, origin_value):
        """"
        Function to group the line by destination
        """
        picking_by_destination = {}
        for record in origin_value:
            destination = record.location_dest_id
            if destination not in picking_by_destination:
                picking_by_destination[destination] = [record]
            else:
                picking_by_destination[destination].append(record)
        return picking_by_destination

    def action_create_picking(self, origin, destination, picking_lines):
        picking_env = self.env['stock.picking']
        move_env = self.env['stock.move']
        analytic_env = self.env['account.analytic.line']
        obj_picking_type = self.env['stock.picking.type'].search([('code', '=', 'outgoing'),
                                                                  ('company_id', '=', self.env.company.id)], limit=1)
        pick = {
            'picking_type_id': obj_picking_type.id if obj_picking_type else False,
            'partner_id': self.task_id.partner_id.id,
            'origin': self.task_id.sequence_name,
            'location_dest_id': destination.id,
            'location_id': origin.id,
            'state': 'draft',
            'task_id': self.task_id.id
        }
        create_picking = picking_env.create(pick)
        if create_picking:
            self.task_id.picking_ids += create_picking
            for item in picking_lines:
                line_vals = {
                    'picking_id': create_picking.id,
                    'product_id': item.product_id.id,
                    'name': item.product_id.name,
                    'product_uom': item.product_uom.id,
                    'product_uom_qty': item.product_qty,
                    'location_dest_id': create_picking.location_dest_id.id,
                    'location_id': create_picking.location_id.id
                }
                obj_move = move_env.create(line_vals)
                if obj_move:
                    item.state = 'process'
                    item.move_line_id = obj_move.id
                    dict_analytic = {
                        'name': self.task_id.name + ' - ' + obj_move.name,
                        'account_id': False,
                        'amount': 0,
                        'unit_amount': 0,
                        'product_id': item.product_id.id
                    }
                    check_process = False
                    if self.task_id.project_id.analytic_account_id:
                        analytic = self.task_id.project_id.analytic_account_id
                        dict_analytic['account_id'] = analytic.id
                        amount = item.product_id.standard_price
                        unit_amount = item.estimated_qty
                        if not item.purchase_order_id:
                            check_process = True
                            amount = - item.estimated_qty * amount
                        else:
                            if item.estimated_qty > item.product_qty:
                                check_process = True
                                amount = (item.estimated_qty - item.product_qty) * amount
                                unit_amount = item.estimated_qty - item.product_qty
                        dict_analytic['amount'] = amount
                        dict_analytic['unit_amount'] = unit_amount
                        if check_process:
                            create_analytic = analytic_env.create(dict_analytic)
                            if create_analytic:
                                create_analytic.amount = dict_analytic['amount']
                                item.analytic_line_id = create_analytic
            if not [line for line in picking_lines if line.lot_id]:
                create_picking.action_confirm()
                create_picking.action_assign()
                if create_picking.state == 'assigned':
                    create_picking._action_done()
                    for line in create_picking.move_ids_without_package:
                        line.quantity = line.product_uom_qty
                    create_picking.button_validate()

    @api.depends('task_id')
    def _compute_material_ids(self):
        """
        Allow the "mapped" and "not mapped" filters in the material list field.
        """
        material_env = self.env['ot.material.line']
        for rec in self:
            task_obj = rec.env['project.task'].browse(rec.task_id.id)
            mat = material_env.search([('state', 'not in', ['block', 'process', 'done']), ('id', 'in', task_obj.ot_material_ids.ids)])
            rec.material_filter_ids = mat
