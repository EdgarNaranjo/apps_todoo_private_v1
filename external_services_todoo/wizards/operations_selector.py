# Copyright 2024-TODAY Todooweb (www.todooweb.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import models, fields, api, _


class OperationSelection(models.TransientModel):
    _name = 'operation.selection.wizard'
    _description = 'Wizard to select the operation to be process'

    operation_filter_ids = fields.Many2many(
        comodel_name='operation.line',
        compute='_compute_operation_ids'
    )
    operation_ids = fields.Many2many(
        comodel_name='operation.line',
        relation='task_operation_selector_rel',
        column1='select_operation_id',
        column2='operation_id',
        string="Operations",
        copy=False
    )
    task_id = fields.Many2one(
        string='OT',
        comodel_name='project.task'
    )

    def action_quotation_sale(self, billable_lines):
        env_order = self.env['sale.order']
        env_order_line = self.env['sale.order.line']
        pricelist = self.task_id.partner_id.property_product_pricelist
        order_vals = {
            'partner_id': self.task_id.partner_id.id,
            'origin': self.task_id.name,
            'date_order': fields.Date.today(),
            'partner_shipping_id': self.task_id.partner_id.id,
            'pricelist_id': pricelist.id if pricelist else False,
            'fiscal_position_id': self.task_id.partner_id.property_account_position_id.id
            if self.task_id.partner_id.property_account_position_id else False,
            'currency_id': self.task_id.currency_id.id,
            'user_id': self.env.uid,
            'company_id': self.task_id.company_id.id,
            'plan_id': self.task_id.analytic_account_id.plan_id.id,
            'analytic_account_id': self.task_id.analytic_account_id.id,
            'tag_ids': self.task_id.tag_order_ids
        }
        sale_order = env_order.create(order_vals)
        if sale_order:
            if not self.task_id.order_id:
                self.task_id.order_id = sale_order.id
            for line in billable_lines:
                line_vals = {
                    'name': line.name,
                    'product_id': line.product_id.id,
                    'price_unit': line.product_id.lst_price,
                    'product_uom': line.product_uom.id,
                    'company_id': self.task_id.company_id.id,
                    'product_uom_qty': line.product_qty,
                    'tax_id': [(6, 0, line.product_id.taxes_id.ids)],
                    'order_id': sale_order.id
                }
                # analytic = self.task_id.analytic_account_id
                # line_vals.update({'analytic_distribution': {analytic.id: 100.0}})
                create_line = env_order_line.create(line_vals)
                if create_line:
                    line.state = 'process'
                    line.sale_line_id = create_line.id
            self.task_id.message_post(body=_('Created sale order "{}" related with the task.')
                                      .format(sale_order._get_html_link()))
            sale_order._recompute_prices()

    def action_select_operations_to_process(self):
        billable_lines = self.operation_ids.filtered(lambda e: e.is_billable)
        not_billable_lines = self.operation_ids.filtered(lambda e: not e.is_billable)
        if billable_lines:
            if self.task_id.order_id:
                for operation in billable_lines:
                    operation._verify_so_line()
            else:
                self.action_quotation_sale(billable_lines)
        if not_billable_lines:
            self.create_analytic(not_billable_lines)

    def create_analytic(self, not_billable_lines):
        analytic_env = self.env['account.analytic.line']
        for item in not_billable_lines:
            dict_analytic = {
                'name': self.task_id.name + ' - ' + item.name,
                'account_id': False,
                'amount': 0,
                'unit_amount': item.product_qty,
                'product_id': item.product_id.id
            }
            if self.task_id.project_id.analytic_account_id:
                analytic = self.task_id.project_id.analytic_account_id
                dict_analytic['account_id'] = analytic.id
                amount = item.product_qty * item.product_id.standard_price
                if amount > 0:
                    amount = - amount
                dict_analytic['amount'] = amount
                create_analytic = analytic_env.create(dict_analytic)
                if create_analytic:
                    create_analytic.amount = dict_analytic['amount']
                    item.analytic_line_id = create_analytic
                    item.state = 'process'

    @api.depends('task_id')
    def _compute_operation_ids(self):
        """
        Allow the "mapped" and "not mapped" filters in the operation list field.
        """
        operation_env = self.env['operation.line']
        for rec in self:
            task_obj = rec.env['project.task'].browse(rec.task_id.id)
            op = operation_env.search([('state', 'not in', ['block', 'process']), ('id', 'in', task_obj.operation_ids.ids)])
            rec.operation_filter_ids = op
