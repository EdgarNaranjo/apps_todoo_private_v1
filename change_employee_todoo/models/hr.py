# Copyright 2024-TODAY Todooweb (www.todooweb.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import models, fields, tools, api, _
from odoo.exceptions import UserError

from datetime import date
import random


class ApplyChangeWizard(models.TransientModel):
    _name = 'apply.change.wizard'
    _description = 'Apply Change Wizard'
    _rec_name = 'effective_date'

    effective_date = fields.Date('Effective date', default=lambda self: fields.Date.today())
    list_action_ids = fields.Many2many('list.action.change', 'rel_wizard_action', 'change_id', 'list_id', string='Changes')

    def action_create_records(self):
        for planning_id in self.env['employee.change.planning'].search([('state', '=', 'not_processed')]):
            planning_id.update_list_action()


class EmployeeHistory(models.Model):
    _name = "employee.history"
    _description = "Employee History"
    _rec_name = 'employee_id'

    employee_id = fields.Many2one('hr.employee', 'Employee', index=True)
    value_before = fields.Char('Value before')
    value_actual = fields.Char('Value now')
    type_action = fields.Char('Action', required=True, help="Type action to update in Employee History")
    type_model = fields.Selection([
        ('employee', 'Employee'),
    ], string='Model', default='employee', required=True,
        help="Type model to update in Employee History")


class FieldValueRelation(models.Model):
    _name = "field.value.relation"
    _description = "Field Value Relation"

    name = fields.Char('Name', required=True, index=True)
    res_id = fields.Integer('Res id', required=True)
    model_id = fields.Integer('Model id')
    model = fields.Char('Model', required=True)


class ListActionChange(models.Model):
    _name = 'list.action.change'
    _description = 'List Action Change'
    _rec_name = 'planning_id'

    def _default_sequence_number(self):
        return random.randint(1, 1000000)

    planning_id = fields.Many2one('employee.change.planning', 'Employee Change', ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', related='planning_id.employee_id', string='Employee')
    effective_date = fields.Date('Effective date', states={'not_processed': [('readonly', False)],
                                                           'processed': [('readonly', True)]}, default=fields.Date.today())
    last_date = fields.Date('Last date')
    type_model = fields.Selection([
        ('employee', 'Employee')
    ], string='Model', default='employee', required=True,
        help="Type model to update in Contract or Employee History", states={'not_processed': [('readonly', False)],
                                                                             'processed': [('readonly', True)]})
    state = fields.Selection([
        ('not_processed', 'Not processed'),
        ('processed', 'Processed'),
    ], string='Status', default='not_processed', required=True)
    type_action = fields.Char('Action', required=True, help="Type action to update in Contract or Employee History")
    field_id = fields.Many2one('ir.model.fields', ondelete='cascade', string='Field',
                               domain='[("model", "=", "hr.employee"), ("name", "!=", "id"), '
                                      '("ttype", "=", "many2one"), ("readonly", "=", False), ("store", "=", True)]')
    field_name = fields.Char('Field Key', required=True)
    actual_value = fields.Char('Actual Value')
    field_value = fields.Many2many('field.value.relation', 'rel_list_action_value', 'action_id', 'value_id',
                                   string='Change Value')
    check_error = fields.Boolean('Error', compute='get_error_lines')
    field_value_filters = fields.Many2many('field.value.relation', compute='get_value_filters', string='Change Filters')
    sequence = fields.Integer('Sequence', default=_default_sequence_number)
    model_id = fields.Integer('Model id')

    @api.constrains('state', 'planning_id', 'planning_id.list_ids')
    def onchange_state_planning(self):
        for record in self:
            if record.state == 'processed':
                if not any(item for item in record.planning_id.list_ids if item.state == 'not_processed'):
                    record.planning_id.state = 'processed'

    @api.onchange('field_id')
    def _onchange_field_id(self):
        if self.field_id:
            self.field_name = self.field_id.name
            actual_value = self.employee_id.export_data([self.field_name]).get('datas', [])
            self.actual_value = actual_value[-1][-1] if actual_value else ''
            obj_values = self.env[self.field_id.relation].search([(self.env[self.field_id.relation]._rec_name, '!=', self.actual_value)])
            list_item = [{'name': item.mapped(item._rec_name)[0], 'res_id': self.sequence, 'model': self.field_id.relation} for item in obj_values]
            create_values = self.env['field.value.relation'].create(list_item)
            self.field_value += create_values
            self.type_action = self.field_id.field_description

    @api.depends('field_id')
    def get_error_lines(self):
        for record in self:
            record.check_error = False
            if len(record.field_value) > 1 or len(record.field_value) < 1:
                record.check_error = True

    @api.depends('field_id')
    def get_value_filters(self):
        for record in self:
            record.field_value_filters = False
            if record.field_id:
                obj_values = self.env[record.field_id.relation].search([(self.env[record.field_id.relation]._rec_name, '!=', record.actual_value)])
                if obj_values:
                    rec_name = obj_values._rec_name
                    filter_value = obj_values.mapped(rec_name)
                    obj_valuation = self.env['field.value.relation'].search([('name', 'in', filter_value),
                                                                             ('res_id', '=', record.sequence),
                                                                             ('model', '=', record.field_id.relation)])
                    record.field_value_filters = obj_valuation.mapped('name') if obj_valuation else False

    @api.constrains('field_value')
    def check_unique_value(self):
        env_relation = self.env['field.value.relation']
        for record in self:
            env_model = self.env[record.field_id.relation]
            if not record.field_value:
                raise UserError(_('At least one value is required in the column "Change Value".'))
            else:
                if len(record.field_value) > 1:
                    raise UserError(_('To save the records you must have a single value in the column "Change Value".'))
                else:
                    model_id = env_model.search([(self.env[record.field_id.relation]._rec_name, '=', record.field_value[0].name)], limit=1)
                    record.model_id = model_id.id
                    record.field_value.write({'model_id': model_id.id})
                    env_relation.search([('model_id', '=', False)]).unlink()


class EmployeeChangePlanning(models.Model):
    _name = "employee.change.planning"
    _description = "Employee Change"
    _rec_name = 'employee_id'

    employee_id = fields.Many2one('hr.employee', 'Employee', index=True, required=True, ondelete='restrict')
    department_id = fields.Many2one(related='employee_id.department_id')
    parent_id = fields.Many2one(related='employee_id.parent_id')
    company_id = fields.Many2one(related='employee_id.company_id')
    state = fields.Selection([
        ('not_processed', 'Not processed'),
        ('processed', 'Processed'),
    ], string='Status', default='not_processed', required=True)
    list_ids = fields.One2many('list.action.change', 'planning_id', 'List Action')
    list_data = fields.Text('Data')
    check_notification = fields.Boolean('Notification', help='Check this option if you want to notify the Manager.')

    def action_open_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Apply changes for {}' .format(self.employee_id.name),
            'res_model': 'apply.change.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {'origin_view': 'wizard_filter',
                        'default_list_action_ids': self.list_ids.filtered(lambda e: e.state != 'processed').ids}
        }

    def unlink(self):
        for record in self:
            if any(item for item in record.list_ids if item.state == 'processed'):
                raise UserError(_('This record cannot be deleted, there are elements that have already been processed.'))
        res = super(EmployeeChangePlanning, self).unlink()
        return res

    def update_dates(self, planning, list_actions):
        if self.env.context.get('origin_view') and self.env.context.get('origin_view') == 'wizard_filter':
            for item in list_actions:
                item.last_date = item.effective_date
                item.effective_date = date.today()
        else:
            list_actions = [item for item in planning.list_ids if item.state == 'not_processed' and
                            item.effective_date <= date.today()]
        return list_actions

    def write_values(self, item, dict_write):
        dict_write[item.field_name] = item.model_id
        item.employee_id.write(dict_write)
        item.state = 'processed'

    @api.model
    def update_list_action(self):
        planning_ids = self.search([('state', '=', 'not_processed')])
        for planning in planning_ids:
            dict_write = {}
            dict_init = {}
            list_actions = [item for item in planning.list_ids if item.state == 'not_processed']
            if list_actions:
                val_data = ''
                obj_update = self.update_dates(planning, list_actions)
                for item in obj_update:
                    dict_write[item.field_name] = item.model_id
                    planning.employee_id.write(dict_write)
                    val_data += item.field_id.field_description + ': ' + item.field_value[0].name + '\n'
                    dict_write.update(dict_init)
                    item.state = 'processed'
            planning.list_data = val_data
            if planning.check_notification:
                mail_template = self.env.ref('change_employee_todoo.notification_email_change_employee', raise_if_not_found=False)
                mail_template.send_mail(planning.id, force_send=True)
        return False
#
#     def prepare_email(self):
#         mail_template = self.env['ir.model.data']._xmlid_to_res_id('elogia_hr.notification_email_change_employee')
#         self._create_mail_begin(mail_template)
#
#     def compose_email_message(self):
#         obj_partner_id = self.env['res.partner'].search([('name', 'like', 'Admin')], limit=1)
#         email_from = obj_partner_id.email if obj_partner_id else 'admin@email.com'
#         parent = self.employee_id.parent_id
#         email_to = parent.user_id.email_formatted if parent.user_id else 'user@email.com'
#         mail_data = {
#             'email_from': email_from,
#             'email_to': email_to,
#             'res_id': self.id,
#         }
#         return mail_data
#
#     def _create_mail_begin(self, template):
#         template_browse = self.env['mail.template'].browse(template)
#         data_compose = self.compose_email_message()
#         if template_browse and data_compose:
#             values = template_browse.generate_email(self.id,
#                                                     ['subject', 'body_html', 'email_from', 'email_to',
#                                                      'partner_to', 'reply_to'])
#             values['email_to'] = data_compose['email_to']
#             values['email_from'] = data_compose['email_from']
#             values['reply_to'] = data_compose['email_from']
#             values['res_id'] = data_compose['res_id']
#             msg_id = self.env['mail.mail'].sudo().create(values)
#             if msg_id:
#                 msg_id.send()


class Employee(models.Model):
    _inherit = "hr.employee"

    history_ids = fields.One2many('employee.history', 'employee_id', string='Employee History')
    change_ids = fields.One2many('employee.change.planning', 'employee_id', string='Employee Change')
    count_changes = fields.Integer('Changes', compute='_calc_count_changes')

    def _calc_count_changes(self):
        for obj_employee in self:
            obj_employee.count_changes = len(obj_employee.change_ids) if obj_employee.change_ids else 0

    def write(self, vals):
        history_env = self.env['employee.history']
        obj_fields = self.env['ir.model.fields'].search([('model', '=', 'hr.employee'),
                                                         ('ttype', '=', 'many2one'),
                                                         ('readonly', '=', False), ('store', '=', True)])
        list_field = []
        if obj_fields:
            for rec in self:
                for key in vals.keys():
                    value_before = rec.export_data([key]).get('datas', [])[-1][-1] if rec.export_data([key]).get('datas', []) else ''
                    value_action = obj_fields.filtered(lambda e: e.name == key)
                    value_actual = self.env[value_action.relation].browse(vals.get(key)) if key in vals and value_action else ''
                    if value_action:
                        list_field.append({
                            'value_before': value_before,
                            'value_actual': value_actual.name if value_actual else '',
                            'type_action': value_action.field_description,
                            'employee_id': rec.id
                        })
            if list_field:
                history_env.create(list_field)
        return super(Employee, self).write(vals)

    def action_view_history(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'History',
            'res_model': 'employee.history',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'target': 'new',
            'domain': [('employee_id', '=', self.id)]
        }

    def action_view_changes(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Changes',
            'res_model': 'employee.change.planning',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'domain': [('employee_id', '=', self.id)],
            'context': {'default_employee_id': self.id},
        }
