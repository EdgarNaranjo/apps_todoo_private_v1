# Copyright 2024-TODAY Todooweb (www.todooweb.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class MaterialLine(models.Model):
    _name = 'ot.material.line'
    _description = 'Materials used to complete a task'
    _rec_name = 'product_id'
    _order = 'id asc'

    def _get_default_location(self):
        env_location = self.env['stock.location']
        return env_location.search([('is_material', '=', True)], limit=1)

    product_id = fields.Many2one(
        string='Product',
        comodel_name='product.product'
    )
    name = fields.Char(
        string='Description'
    )
    location_id = fields.Many2one(
        string='Origin Location',
        comodel_name='stock.location'
    )
    location_dest_id = fields.Many2one(
        string='Final Location',
        comodel_name='stock.location',
        default=_get_default_location
    )
    warehouse_id = fields.Many2one(
        related='location_id.warehouse_id',
        string='Warehouse'
    )
    product_qty = fields.Float(
        string='Quantity'
    )
    estimated_qty = fields.Float(
        string='Estimated Qty'
    )
    product_uom = fields.Many2one(
        string='UdM',
        comodel_name='uom.uom'
    )
    price_unit = fields.Float(
        string='Price Unit'
    )
    task_id = fields.Many2one(
        string='OT',
        comodel_name='project.task'
    )
    sequence_name = fields.Char(related='task_id.sequence_name')
    company_id = fields.Many2one(related="task_id.company_id")
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        compute='_get_company_currency',
        readonly=True,
        string="Currency"
    )
    is_billable = fields.Boolean(
        string='Is billable'
    )
    sale_line_id = fields.Many2one(
        string='Order Line',
        comodel_name='sale.order.line'
    )
    purchase_order_id = fields.Many2one(
        string='Purchase Order',
        comodel_name='purchase.order',
        help='This field will is an auxiliar to generate automatically lines in this Task Materials,'
             ' if is set to False all the lines not process related will be deleted'
    )
    purchase_line_id = fields.Many2one(
        string='Purchase Line',
        comodel_name='purchase.order.line'
    )
    state = fields.Selection(
        selection=[('new', 'New'),
                   ('process', 'Process'),
                   ('done', 'Done'),
                   ('block', 'Cancelled')],
        string='State',
        default='new'
    )
    move_line_id = fields.Many2one(
        string='Stock Move',
        comodel_name='stock.move'
    )
    is_invisible = fields.Boolean('Is invisible', compute='compute_is_invisible')
    is_readonly = fields.Boolean(related='task_id.is_readonly')
    analytic_line_id = fields.Many2one(
        string='Analytic line',
        comodel_name='account.analytic.line'
    )
    sequence = fields.Integer('No.')
    management_stock = fields.Boolean('Management Stock')
    check_process = fields.Boolean('Signed', help='Indicates that it was processed after being signed by the client')
    check_send = fields.Boolean('Enviado', help='Indicates that it was send after being signed by the client')
    lot_id = fields.Many2one(
        string='Lote',
        comodel_name='stock.lot'
    )
    required_lot = fields.Boolean('Requited lot', compute='_compute_requited_lot')

    @api.model
    def create(self, vals_list):
        env_material = self.env['ot.material.line']
        res = super(MaterialLine, self).create(vals_list)
        for record in res:
            obj_material = env_material.search([('id', '!=', record.id), ('task_id', '=', record.task_id.id)], order='id asc')
            if not obj_material:
                count = 0
            else:
                count = max(obj_material.mapped('sequence'))
            record.sequence = count + 1
        return res

    def _get_company_currency(self):
        for rec in self:
            if rec.company_id:
                rec.currency_id = rec.sudo().company_id.currency_id
            else:
                rec.currency_id = self.env.company.currency_id

    def get_so_line_data(self):
        """"
        This function @Return the data to generate a SO Line from the actual Material
        """
        val_order = self.task_id.order_id
        if self.task_id.last_order and self.task_id.last_order.state == 'draft':
            val_order = self.task_id.last_order
        data = {
            'name': self.product_id.name,
            'product_id': self.product_id.id,
            'order_id': val_order.id,
            'price_unit': self.product_id.lst_price,
            'product_uom': self.product_uom.id,
            'company_id': self.company_id.id,
            'product_uom_qty': self.product_qty,
            'material_id': self.id,
        }
        return data

    def _verify_so_line(self):
        """"
        This function its used to verify if its necessary to create a new line in the SO
        coming from the materials process
        """
        so_line_env = self.env['sale.order.line']
        analytic_env = self.env['account.analytic.line']
        data = self.get_so_line_data()
        if self.task_id.order_id.state == 'cancel':
            raise UserError(_("Sale order {} is in 'Canceled' status.") .format(self.task_id.order_id.name))
        if data:
            dict_analytic = {
                'name': self.task_id.name + ' - ' + data['name'],
                'account_id': False,
                'amount': 0,
                'unit_amount': 0,
                'product_id': self.product_id.id
            }
            check_process = False
            if self.task_id.analytic_account_id:
                analytic = self.task_id.analytic_account_id
                # data.update({'analytic_distribution': {analytic.id: 100.0}})
                dict_analytic['account_id'] = analytic.id
                amount = self.product_id.standard_price
                unit_amount = self.estimated_qty
                if not self.purchase_order_id:
                    check_process = True
                    amount = - self.estimated_qty * amount
                else:
                    if self.estimated_qty > self.product_qty:
                        check_process = True
                        amount = (self.estimated_qty - self.product_qty) * amount
                        unit_amount = self.estimated_qty - self.product_qty
                dict_analytic['amount'] = amount
                dict_analytic['unit_amount'] = unit_amount
                if check_process:
                    create_analytic = analytic_env.create(dict_analytic)
                    if create_analytic:
                        create_analytic.amount = dict_analytic['amount']
                        self.analytic_line_id = create_analytic
            new_line = so_line_env.create(data)
            if new_line:
                self.sale_line_id = new_line.id
                self.state = 'process'
                new_line.order_id._recompute_prices()
                sale_msg = _('Created sale line related with the SO: %s.', new_line.order_id._get_html_link())
                self.task_id.message_post(body=sale_msg)

    def unlink(self):
        for record in self:
            if record.state in ['process', 'done']:
                raise UserError(_('You cannot delete a line in "Processed" status.'))
        return super().unlink()

    def action_deprocess(self):
        for record in self:
            if record.sale_line_id:
                if record.state == 'process':
                    if record.sale_line_id.qty_invoiced == 0:
                        record.sale_line_id.product_uom_qty = 0
                        record.sale_line_id.material_id = False
                        record.sale_line_id = False
                        record.analytic_line_id.unlink()
                        record.state = 'new'
                    else:
                        raise UserError(_('The sales order line has been invoiced.'))
            else:
                if record.state == 'done':
                    record.state = 'new'

    @api.depends('state', 'is_billable')
    def compute_is_invisible(self):
        for record in self:
            record.is_invisible = True
            if record.state in ['process', 'done'] and record.is_billable:
                record.is_invisible = False

    @api.onchange('product_id', 'product_qty')
    def onchange_check_related_product(self):
        if self.product_id:
            if self.product_id.name_short:
                self.name = self.product_id.name_short
            else:
                self.name = self.product_id.name
            self.product_uom = self.product_id.uom_id.id
            if self.task_id:
                if self.task_id.type_order == 'aver':
                    self.is_billable = True
                else:
                    self.is_billable = False
        if self.product_qty and self.product_qty > self.estimated_qty:
            raise UserError(_("The quantity cannot be greater than the estimated quantity."))

    @api.depends('product_id', 'lot_id')
    def _compute_requited_lot(self):
        env_lot = self.env['stock.lot']
        for record in self:
            record.required_lot = False
            if record.product_id.tracking == 'lot':
                obj_lot = env_lot.search([('product_id', '=', record.product_id.id)])
                if obj_lot:
                    record.required_lot = True


class OperationLine(models.Model):
    _name = 'operation.line'
    _description = 'Operation line'
    _rec_name = 'product_id'

    product_id = fields.Many2one(
        string='Product',
        comodel_name='product.product'
    )
    name = fields.Char(
        string='Description'
    )
    task_id = fields.Many2one(
        string='OT',
        comodel_name='project.task'
    )
    sequence_name = fields.Char(related='task_id.sequence_name')
    state = fields.Selection(
        selection=[('new', 'New'),
                   ('process', 'Process'),
                   ('block', 'Cancelled')],
        string='State',
        default='new'
    )
    product_qty = fields.Float(
        string='Quantity'
    )
    product_uom = fields.Many2one(
        string='UdM',
        comodel_name='uom.uom'
    )
    is_billable = fields.Boolean(
        string='Is billable'
    )
    company_id = fields.Many2one(related="task_id.company_id")
    sale_line_id = fields.Many2one(
        string='Order Line',
        comodel_name='sale.order.line'
    )
    analytic_line_id = fields.Many2one(
        string='Analytic line',
        comodel_name='account.analytic.line'
    )
    is_readonly = fields.Boolean(related='task_id.is_readonly')
    date_now = fields.Date('Date', default=fields.Date.today())
    technical_id = fields.Many2one('res.users', 'Technical', default=lambda self: self.env.context.get('user_id', self.env.user.id))
    check_process = fields.Boolean('Signed', help='Indicates that it was processed after being signed by the client')
    check_send = fields.Boolean('Enviado', help='Indicates that it was send after being signed by the client')

    @api.onchange('product_id')
    def onchange_check_related_product(self):
        if self.product_id:
            if self.product_id.name_short:
                self.name = self.product_id.name_short
            else:
                self.name = self.product_id.name
            self.product_uom = self.product_id.uom_id.id
            if self.task_id:
                if self.task_id.type_order == 'aver':
                    self.is_billable = True
                else:
                    self.is_billable = False

    def _verify_so_line(self):
        """"
        This function its used to verify if its necessary to create a new line in the SO
        coming from the operations process
        """
        so_line_env = self.env['sale.order.line']
        analytic_env = self.env['account.analytic.line']
        data = self.get_so_line_data()
        if self.task_id.order_id.state == 'cancel':
            raise UserError(_("Sale order {} is in 'Canceled' status.") .format(self.task_id.order_id.name))
        if data:
            dict_analytic = {
                'name': self.task_id.name + ' - ' + data['name'],
                'account_id': False,
                'amount': 0,
                'unit_amount': self.product_qty,
                'product_id': self.product_id.id
            }
            if self.task_id.analytic_account_id:
                analytic = self.task_id.analytic_account_id
                # data.update({'analytic_distribution': {analytic.id: 100.0}})
                dict_analytic['account_id'] = analytic.id
                amount = self.product_qty * self.product_id.standard_price
                if amount > 0:
                    amount = - amount
                dict_analytic['amount'] = amount
                create_analytic = analytic_env.create(dict_analytic)
                if create_analytic:
                    create_analytic.amount = dict_analytic['amount']
                    self.analytic_line_id = create_analytic
                    self.state = 'process'
            new_line = so_line_env.create(data)
            if new_line:
                self.sale_line_id = new_line.id
                self.state = 'process'
                new_line.order_id._recompute_prices()
                sale_msg = _('Created sale line related with the SO: %s.', new_line.order_id._get_html_link())
                self.task_id.message_post(body=sale_msg)

    def get_so_line_data(self):
        """"
        This function @Return the data to generate a SO Line from the actual operation
        """
        val_order = self.task_id.order_id
        if self.task_id.last_order and self.task_id.last_order.state == 'draft':
            val_order = self.task_id.last_order
        data = {
            'name': self.product_id.name,
            'product_id': self.product_id.id,
            'order_id': val_order.id,
            'price_unit': self.product_id.lst_price,
            'product_uom': self.product_uom.id,
            'company_id': self.company_id.id,
            'product_uom_qty': self.product_qty,
        }
        return data

    def action_deprocess(self):
        for record in self:
            if record.state == 'process':
                if record.sale_line_id:
                    if record.sale_line_id.qty_invoiced == 0:
                        record.sale_line_id.product_uom_qty = 0
                        record.sale_line_id = False
                        record.analytic_line_id.unlink()
                        record.state = 'new'
                    else:
                        raise UserError(_('The sales order line has been invoiced.'))
                else:
                    record.analytic_line_id.unlink()
                    record.state = 'new'


class TrackingLine(models.Model):
    _name = 'tracking.line'
    _description = 'Tracking line'
    _rec_name = 'product_id'
    _order = 'id asc'

    line_id = fields.Many2one(string='Materials', comodel_name='ot.material.line')
    product_id = fields.Many2one(related='line_id.product_id', string='Product')
    sequence = fields.Integer(related='line_id.sequence', string='Line')
    picking_id = fields.Many2one(string='Stock Picking', comodel_name='stock.picking')
    picking_return_id = fields.Many2one(string='Picking Return', comodel_name='stock.picking')
    product_origin_qty = fields.Float('Quantity (P)')
    product_dest_qty = fields.Float('Quantity (R)')
    product_uom = fields.Many2one(related='line_id.product_uom', string='UdM')
    is_readonly = fields.Boolean(related='line_id.is_readonly')
    task_id = fields.Many2one(string='OT', comodel_name='project.task')
    state = fields.Selection(
        selection=[('draft', 'Draft'),
                   ('partial', 'Partial'),
                   ('full', 'Full')],
        string='State',
        default='draft'
    )
