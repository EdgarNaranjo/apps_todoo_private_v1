# Copyright 2024-TODAY Todooweb (www.todooweb.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class Project(models.Model):
    _inherit = "project.project"

    is_template = fields.Boolean('Template', help='Check if a project is a template', copy=False)


class ProjectTask(models.Model):
    _inherit = 'project.task'

    sequence_name = fields.Char(
        string='Sequence Name',
        copy=False
    )
    contact_id = fields.Many2one(
        comodel_name='res.partner',
        string='Contact'
    )
    ot_material_ids = fields.One2many(
        string='Materials',
        comodel_name='ot.material.line',
        inverse_name='task_id'
    )
    operation_ids = fields.One2many(
        string='Operations',
        comodel_name='operation.line',
        inverse_name='task_id'
    )
    tracking_ids = fields.One2many(
        string='Tracking',
        comodel_name='tracking.line',
        inverse_name='task_id'
    )
    order_id = fields.Many2one(
        string='Sale Order',
        comodel_name='sale.order',
        domain="['|', ('partner_id', '=', False), ('partner_id', '=', partner_id)]"
    )
    purchase_order_filter_ids = fields.Many2many(
        comodel_name='purchase.order',
        compute='_compute_purchase_order_ids'
    )
    purchase_order_id = fields.Many2one(
        string='Purchase Order',
        comodel_name='purchase.order'
    )
    picking_ids = fields.Many2many(
        comodel_name='stock.picking',
        relation='task_picking_rel',
        column1='task_id',
        column2='stock_id',
        string="Pickings",
        check_company=True,
        copy=False,
    )
    picking_count = fields.Integer(
        string='Count Picking',
        compute='_compute_picking_counter'
    )
    is_last = fields.Boolean(related='stage_id.is_last')
    analytic_count = fields.Integer(
        string='Count Analytic',
        compute='_compute_analytic_line'
    )
    type_order = fields.Selection([
        ('insp', 'Inspections'),
        ('mant', 'Maintenance'),
        ('aver', 'Fault'),
        ('march', 'Start-up'),
        ('guard', 'On guard'),
        ('mater', 'Delivery of material'),
        ('docu', 'Delivery of documentation'),
        ('verif', 'Leak check'),
        ('repa', 'Repairs'),
        ('pred', 'Predictive'),
        ('otr', 'Others'),
    ], string='Type order')
    is_impediment = fields.Boolean('An impediment', default=False, tracking=1)
    description_impediment = fields.Text('Motive', tracking=1)
    is_invisible = fields.Boolean('Is invisible', compute='get_invisible_by_group')
    last_order = fields.Many2one(
        string='last Order',
        comodel_name='sale.order',
        copy=False
    )
    tag_order_ids = fields.Many2many(
        comodel_name='crm.tag',
        relation='project_task_order_tag_rel', column1='task_id', column2='tag_id',
        string="Tag Orders")
    is_work_order = fields.Boolean('Work order', help='Determines whether a task is an external service or not.', tracking=1)
    in_observation = fields.Text('In observation', tracking=1)
    other_state = fields.Selection([
        ('rev', 'Reviewed'),
        ('clos', 'Closed')
    ], string='Work order state', help='- Reviewed: Editable for admins\n'
                                       '- Closed: Read only for technicians', tracking=1)
    is_readonly = fields.Boolean('Is readonly', compute='get_readonly')
    is_invisible_technical = fields.Boolean('Invisible technical', compute='_get_invisible_other')
    is_template = fields.Boolean(related='project_id.is_template')
    analytic_plan_id = fields.Many2one(
        string='Plan',
        comodel_name='account.analytic.plan'
    )
    count_doc_sign = fields.Integer('Doc. signed', default=1)

    @api.model
    def create(self, vals):
        env_prod = self.env['product.product']
        env_operation = self.env['operation.line']
        dict_operation = {
            'product_id': False,
            'name': False,
            'task_id': False,
            'product_uom': False,
            'is_billable': False,
        }
        res = super(ProjectTask, self).create(vals)
        if res.is_work_order:
            dict_operation['task_id'] = res.id
            if res.type_order == 'aver':
                dict_operation['is_billable'] = True
            if not res.sequence_name:
                # Assign value to sequence field
                ctx = dict(company_id=res.company_id.id)
                sequence = self.env['ir.sequence'].with_context(ctx).sudo().next_by_code('project.task')
                res.sequence_name = sequence
            obj_product_ids = env_prod.search([('can_movility', '=', True)])
            if obj_product_ids:
                for product in obj_product_ids:
                    dict_operation['product_id'] = product.id
                    dict_operation['name'] = product.name_short if product.name_short else product.name
                    dict_operation['product_uom'] = product.uom_id.id
                    env_operation.create(dict_operation)
        return res

    def write(self, vals):
        res = super(ProjectTask, self).write(vals)
        for rec in self:
            if not rec.sequence_name and rec.is_work_order:
                # Assign value to sequence field
                ctx = dict(company_id=rec.company_id.id)
                sequence = self.env['ir.sequence'].with_context(ctx).sudo().next_by_code('project.task')
                rec.sequence_name = sequence
        return res

    def get_data_purchase(self, line):
        data = {
            'product_id': line.product_id.id,
            'name': line.product_id.name_short if line.product_id.name_short else line.product_id.name,
            'product_uom': line.product_id.uom_id.id,
            'task_id': self.id,
            'purchase_order_id': self.purchase_order_id.id,
            'purchase_line_id': line.id,
            'estimated_qty': line.qty_received,
            'is_billable': True if self.type_order == 'aver' else False
        }
        return data

    @api.onchange('partner_id')
    def onchange_filter(self):
        if self.partner_id:
            return {'domain': {'contact_id': [('id', 'in', self.partner_id.child_ids.ids)]}}

    @api.onchange('project_id')
    def check_sale_order(self):
        if self.project_id:
            self.order_id = self.project_id.sale_order_id.id

    @api.constrains('analytic_account_id')
    def check_analytic_line(self):
        for record in self:
            if record.analytic_account_id:
                record.analytic_plan_id = record.analytic_account_id.plan_id.id

    @api.depends('partner_id')
    def _compute_purchase_order_ids(self):
        purchase_line_env = self.env['purchase.order.line']
        for record in self:
            result = []
            obj_lines = purchase_line_env.search([('task_id', '=', record.id)])
            if obj_lines:
                result = obj_lines.mapped('order_id')
            record.purchase_order_filter_ids = result

    def action_mark_done(self):
        self.ensure_one()
        if self.env.user.has_group('external_services_todoo.group_project_technical_worker'):
            raise UserError(_('You do not have permissions to perform this action.\n '
                              'Contact an administrator.'))
        action = self.env["ir.actions.actions"]._for_xml_id(
            "external_services_todoo.action_material_selection_wizard")
        action.update({
            'context': {'default_task_id': self.id,
                        'mark_done': True,
                        'view_mode': 'form',
                        'create': False}
        })
        return action

    def action_process_materials(self):
        self.ensure_one()
        if self.env.user.has_group('external_services_todoo.group_project_technical_worker'):
            raise UserError(_('You do not have permissions to perform this action.\n '
                              'Contact an administrator.'))
        action = self.env["ir.actions.actions"]._for_xml_id(
            "external_services_todoo.action_material_selection_wizard")
        action.update({
            'context': {'default_task_id': self.id,
                        'view_mode': 'form',
                        'create': False}
        })
        return action

    def action_process_operations(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "external_services_todoo.action_operation_selection_wizard")
        action.update({
            'context': {'default_task_id': self.id,
                        'view_mode': 'form',
                        'create': False}
        })
        return action

    def action_po_add_materials(self):
        """"
        Function to generate the material line coming from PO selected
        """
        material_env = self.env['ot.material.line']
        if self.purchase_order_id:
            for line in self.purchase_order_id.order_line.filtered(lambda e: e.task_id == self):
                if line.qty_received > 0:
                    data = self.get_data_purchase(line)
                    material_env.create(data)
            self.purchase_order_id = False

    @api.depends('picking_ids')
    def _compute_picking_counter(self):
        env_move = self.env['stock.move']
        for rec in self:
            obj_move = set(env_move.search([('origin_returned_move_id', 'in',
                                             rec.picking_ids.mapped('move_ids').ids)]).mapped('picking_id'))
            rec.picking_count = len(rec.picking_ids) + len(obj_move)

    def action_picking_in_task(self):
        self.ensure_one()
        env_move = self.env['stock.move']
        obj_move = env_move.search([('origin_returned_move_id', 'in',
                                         self.picking_ids.mapped('move_ids').ids)]).mapped('picking_id')
        action = self.env["ir.actions.actions"]._for_xml_id("stock.stock_picking_action_picking_type")
        action.update({
            'context': {'default_task_id': self.id, 'create': False},
            'view_mode': 'tree,form',
            'domain': ['|', ('id', 'in', self.picking_ids.ids), ('id', 'in', obj_move.ids)]
        })
        return action

    @api.depends('project_id')
    def _compute_analytic_line(self):
        env_analytic = self.env['account.analytic.line']
        for record in self:
            record.analytic_count = len(env_analytic.search([('task_id', '=', record.id)]))

    def action_analytic_in_task(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("analytic.account_analytic_line_action_entries")
        action.update({
            'context': {'default_task_id': self.id, 'create': False},
            'domain': [('task_id', '=', self.id)]
        })
        return action

    @api.depends('ot_material_ids', 'operation_ids', 'stage_id')
    def get_invisible_by_group(self):
        for record in self:
            record.is_invisible = False
            if self.env.user.has_group('external_services_todoo.group_project_technical_worker'):
                record.is_invisible = True

    @api.onchange('stage_id')
    def check_technical_worker(self):
        show_message = False
        if self.stage_id.is_locked:
            if self.env.user.has_group('external_services_todoo.group_project_technical_worker'):
                show_message = True
        if self.other_state:
            show_message = True
        if show_message:
            raise UserError(_('You do not have permissions to move the task to the stage "{}"')
                            .format(self.stage_id.name))

    def action_view_so(self):
        so_ids = self._get_action_view_so_ids()
        action_window = {
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "name": _("Sales Order"),
            "views": [[False, "tree"], [False, "kanban"], [False, "form"]],
            "context": {"create": False, "show_sale": True},
            "domain": [["id", "in", so_ids]],
        }
        return action_window

    def _get_action_view_so_ids(self):
        list_order = self.sale_order_id.ids
        if self.order_id:
            list_order += [self.order_id.id]
        if self.last_order:
            list_order += [self.order_id.id]
        if self.ot_material_ids:
            list_order += self.ot_material_ids.mapped('sale_line_id').mapped('order_id').ids
        if self.operation_ids:
            list_order += self.operation_ids.mapped('sale_line_id').mapped('order_id').ids
        return list_order

    def _get_action_view_invoice_ids(self):
        list_invoice = []
        if self.ot_material_ids:
            list_invoice += self.ot_material_ids.mapped('sale_line_id').mapped('invoice_lines').mapped('move_id').ids
        if self.operation_ids:
            list_invoice += self.operation_ids.mapped('sale_line_id').mapped('invoice_lines').mapped('move_id').ids
        return list_invoice

    def action_view_invoices(self):
        invoice_ids = self._get_action_view_invoice_ids()
        action_window = {
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "name": _("Invoices"),
            "views": [[False, "tree"], [False, "form"]],
            "context": {"create": False},
            "domain": [["id", "in", invoice_ids]],
        }
        if len(invoice_ids) == 1:
            action_window["views"] = [[False, "form"]]
            action_window["res_id"] = invoice_ids[0]
        return action_window

    @api.depends('stage_id', 'other_state')
    def get_readonly(self):
        for record in self:
            record.is_readonly = False
            if record.other_state and self.env.user.has_group('external_services_todoo.group_project_technical_worker'):
                record.is_readonly = True

    @api.depends('stage_id', 'other_state')
    def _get_invisible_other(self):
        for record in self:
            record.is_invisible_technical = False
            if not record.stage_id.is_last or (not record.other_state and self.env.user.has_group('external_services_todoo.group_project_technical_worker')):
                record.is_invisible_technical = True

    def _is_fsm_report_available(self):
        self.ensure_one()
        return self.comment or (self.ot_material_ids or self.operation_ids)

    @api.depends(
        'allow_worksheets', 'timer_start',
        'display_satisfied_conditions_count', 'display_enabled_conditions_count',
        'fsm_is_sent')
    def _compute_display_send_report_buttons(self):
        for task in self:
            send_p = False
            send_s = True
            task.update({
                'display_send_report_primary': send_p,
                'display_send_report_secondary': send_s,
            })

    def action_services_send(self):
        """ Opens a wizard to compose an email, with relevant mail template loaded by default """
        env_template = self.env['mail.template']
        mail_template = env_template.search([('check_service', '=', 'True')], limit=1)
        ctx = {
            'default_model': 'project.task',
            'default_res_ids': self.ids,
            'default_template_id': mail_template.id if mail_template else None,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            'default_email_layout_xmlid': 'mail.mail_notification_layout_with_responsible_signature',
            'force_email': True
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }
