from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError, ValidationError
from datetime import datetime, timedelta, date
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

import logging
_logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    relation_employee_id = fields.Many2one('relation.employee', 'Relation Employee', track_visibility='onchange')


class RelationEmployee(models.Model):
    _name = 'relation.employee'
    _description = 'Relation Employee'
    _rec_name = 'employee_id'
    _order = 'group_day asc'

    employee_id = fields.Many2one('res.users', 'Employee', track_visibility='onchange', required=True, index=True)
    theoretical_qty = fields.Integer('Theoretical qty')
    real_qty = fields.Integer('Real qty')
    time_working = fields.Selection([
        # ('5', '5 Hrs'),
        # ('6', '6 Hrs'),
        ('7', '7 Hrs'),
        ('8', '8 Hrs'),
        ('9', '9 Hrs'),
        ('10', '10 Hrs'),
    ], string='Working day', index=True, required=True)
    group_day = fields.Selection([
        ('1', '09.00-15.00H'),
        ('2', '09.00-17.30H'),
        ('3', '12.00-20.30H'),
        ('4', '09.00-20.30H'),
        ('5', '11.30-20.30H'),
    ], string='Group', index=True, required=True)
    lead_ids = fields.One2many('crm.lead', 'relation_employee_id', string='Lead')
    lead_count = fields.Integer(compute='_compute_todo_lead')

    def _compute_todo_lead(self):
        for obj_relation in self:
            obj_relation.lead_count = len(obj_relation.lead_ids)

    def action_view_leads(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Leads',
            'res_model': 'crm.lead',
            'view_mode': 'kanban,tree,form',
            'view_type': 'form',
            'domain': [('id', 'in', self.lead_ids.ids)]
        }


class DistributionLead(models.Model):
    _name = 'distribution.lead'
    _inherit = ['mail.activity.mixin', 'mail.thread']
    _description = 'Distribution Lead'
    _order = 'create_date desc'

    name = fields.Char('Document Name', default="New Distribution", copy=False)
    employee_ids = fields.Many2many('relation.employee', 'distribution_employee_rel', 'distribution_id', 'employee_id', 'Relation Employee', track_visibility='onchange')
    lead_ids = fields.Many2many('crm.lead', 'distribution_lead_rel', 'distribution_id', 'lead_id', 'Crm Lead', track_visibility='onchange')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('error', 'Error'),
        ('cancel', 'Cancel'),
    ], string='Status', index=True)

    def desmark_employee(self):
        setting_employee_ids = self.env['setting.employee'].search([('available', '=', True)])
        if setting_employee_ids:
            obj_list_employee = self._repart_rest(setting_employee_ids)
            if obj_list_employee:
                setting_employee_assigned = [employee for employee in obj_list_employee if employee.assigned]
                if setting_employee_assigned:
                    _logger.info('Comerciales a liberar %s' % str(len(setting_employee_assigned)))
                    setting_employee_assigned_fil = [filtered for filtered in setting_employee_assigned if filtered in obj_list_employee]
                    if len(obj_list_employee) == len(setting_employee_assigned_fil):
                        for emp_assig in obj_list_employee:
                            emp_assig.write({'assigned': False})
                            _logger.info('Comercial %s disponibles nuevamente' % emp_assig.employee_id.user_id.name)
                            if not emp_assig.employee_id.user_id.active:
                                emp_assig.write({'available': False})
                                _logger.info('Comercial %s desactivado' % emp_assig.employee_id.user_id.name)
                setting_employee_assigned_saturday = [employee for employee in obj_list_employee if employee.assigned and employee.hour_sat]
                setting_employee_saturday = [employee for employee in obj_list_employee if employee.hour_sat]
                if setting_employee_assigned_saturday:
                    _logger.info('Comerciales a liberar %s el Sabado' % str(len(setting_employee_assigned_saturday)))
                    if len(setting_employee_saturday) == len(setting_employee_assigned_saturday):
                        for emp_assig in setting_employee_assigned_saturday:
                            emp_assig.write({'assigned': False})
                            _logger.info('Comercial el sabado %s disponibles nuevamente' % emp_assig.employee_id.user_id.name)
            else:
                _logger.info('No es necesario liberar comerciales')
        return False

    def prepare_process_distribution(self):
        setting_employee_ids = self.env['setting.employee'].search([('available', '=', True)])
        employee_not_assigned = setting_employee_ids.filtered(lambda e: not e.assigned)
        day_now = datetime.today().weekday()
        hour_now = datetime.today().hour + 2
        list_relation_all = []
        list_relation = []
        dict_relation = {
            'employee_id': False,
            'theoretical_qty': 0,
            'real_qty': 0,
            'time_working': '',
            'group_day': '',
        }
        ok_process = False
        create_distribution = self.env['distribution.lead']
        create_relation = self.env['relation.employee']
        if not setting_employee_ids:
            raise UserError("No existe una configuración de Comerciales.")
            _logger.info("No existe una configuración de Comerciales.")
        else:
            if hour_now >= 8:
                if day_now in [0, 1, 2, 3, 4]:
                    ok_process = True
                if day_now == 5 and hour_now <= 15:
                    ok_process = True
            if employee_not_assigned and ok_process:
                obj_lead_ids = self.env['crm.lead'].search([('active', '=', True), ('stage_id.name', 'like', 'LEAD'), '|', ('user_id', '=', False), ('user_id.name', '=', 'Administrator')])
                if obj_lead_ids:
                    obj_list_rest = self._repart_rest(employee_not_assigned)
                    if obj_list_rest:
                        if day_now == 5:
                            obj_list_rest = [list_res for list_res in obj_list_rest if list_res.hour_sat]
                        obj_dist = create_distribution.create({'lead_ids': [(6, 0, obj_lead_ids.ids)]})
                        if obj_dist:
                            _logger.info('Creados leads en distributions: %s' % len(obj_lead_ids))
                            for employee in obj_list_rest[:len(obj_lead_ids)]:
                                dict_relation['employee_id'] = employee.employee_id.user_id.id
                                dict_relation['time_working'] = employee.time_working
                                dict_relation['group_day'] = employee.group_day
                                dict_relation['theoretical_qty'] = len(obj_lead_ids)
                                ob_create_relation = create_relation.create(dict_relation)
                                if ob_create_relation:
                                    _logger.info('Creado comercial: %s' % str(ob_create_relation.employee_id.name))
                                    if ob_create_relation.id not in list_relation:
                                        list_relation_all.append(ob_create_relation)
                                        list_relation.append(ob_create_relation.id)
                                obj_real = self._calc_quantity_real(obj_list_rest, obj_lead_ids)
                                val_diff_qty = 0
                                cant_diff = 0
                                if obj_real:
                                    val_real_qty = obj_real[0]['real_qty']
                                    real_diff_qty = obj_real[1]
                                    if real_diff_qty:
                                        cant_diff = divmod(real_diff_qty, len(obj_list_rest[:real_diff_qty]))
                                    if cant_diff:
                                        list_sorter = sorted(obj_list_rest, key=lambda x: x.time_working)
                                        if employee in list_sorter[:real_diff_qty]:
                                            val_diff_qty += cant_diff[0]
                                    val_real_qty += val_diff_qty
                                ob_create_relation.write({'real_qty': val_real_qty})
                                _logger.info('Cantidad asignada: %s' % str(val_real_qty))
                                if obj_real[0]['assigned']:
                                    employee.assigned = True
                        if list_relation:
                            obj_dist.write({'employee_ids': [(6, 0, list_relation)]})
            else:
                _logger.info('No comerciales disponibles, todos estan ocupados')
    #     # self.action_process_distribution()
        return False

    def _calc_quantity_real(self, employee_rest, obj_lead_ids):
        dict_qty = {
            'real_qty': 0,
            'assigned': False,
        }
        count_diff = 0
        if employee_rest and obj_lead_ids:
            count_total = len(obj_lead_ids)
            if count_total >= len(employee_rest):
                val_div = divmod(count_total, len(employee_rest))
                count_me = val_div[0]
                count_diff = val_div[1]
            else:
                count_me = int(len(obj_lead_ids) / len(employee_rest[:len(obj_lead_ids)]))
            if count_me:
                dict_qty['real_qty'] = int(count_me)
                dict_qty['assigned'] = True
        return dict_qty, count_diff

    def _repart_rest(self, employee_not_assigned):
        list_hour = ['1', '2', '3', '4', '5']
        hour_now = datetime.today().hour + 2
        if 15 < hour_now < 22:
            list_hour.remove('1')
        if 17 < hour_now < 22:
            list_hour.remove('2')
        if hour_now < 12:
            list_hour.remove('3')
        if hour_now < 11:
            list_hour.remove('5')
        list_work_now = [w_now for w_now in employee_not_assigned if w_now.group_day in list_hour]
        return list_work_now

    def action_process_distribution(self):
        obj_distribution = self.env['distribution.lead'].search([('state', '=', 'draft')])
        if obj_distribution:
            count_total = 0
            for distribution in obj_distribution:
                for employee in distribution.employee_ids:
                    count_limit = employee.real_qty
                    obj_leads = self.env['crm.lead'].search([('id', 'in', distribution.lead_ids.ids), ('relation_employee_id', '=', False)], limit=count_limit)
                    _logger.info('Se le asignan: %s lead al empleado %s' % (str(len(obj_leads)), str(employee.employee_id.name)))
                    if obj_leads:
                        for lead in obj_leads:
                            lead.relation_employee_id = employee.id
                            lead.user_id = employee.employee_id.id
                        count_total += count_limit
                if count_total == len(distribution.lead_ids):
                    distribution.state = 'done'
                    _logger.info('Todo OK')
                else:
                    distribution.state = 'error'
                    _logger.info('Algo va mal. Cantidades incorrectas')
        return False

    @api.model
    def create(self, vals):
        request = super(DistributionLead, self).create(vals)
        if request.name == "New Distribution":
            sequence_name = self.env['ir.sequence'].next_by_code('distribution.lead') or "New Distribution"
            request.name = sequence_name
            request.state = 'draft'
            return request

    def check_cancel(self):
        for distribution in self:
            distribution.state = 'cancel'

    def check_draft(self):
        for distribution in self:
            distribution.state = 'draft'


class SettingEmployee(models.Model):
    _name = 'setting.employee'
    _description = 'Setting Employee'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one('hr.employee', 'Employee', track_visibility='onchange', required=True, index=True)
    time_working = fields.Selection([
        # ('5', '5 Hrs'),
        # ('6', '6 Hrs'),
        ('7', '7 Hrs'),
        ('8', '8 Hrs'),
        ('9', '9 Hrs'),
        ('10', '10 Hrs'),
    ], string='Working day', index=True, required=True)
    available = fields.Boolean('Available', default=True)
    group_day = fields.Selection([
        ('1', '09.00-15.00H'),
        ('2', '09.00-17.30H'),
        ('3', '12.00-20.30H'),
        ('4', '09.00-20.30H'),
        ('5', '11.30-20.30H'),
    ], string='Group', index=True, required=True)
    assigned = fields.Boolean('Assigned')
    hour_sat = fields.Boolean('SÁBADO')

    @api.model
    def create(self, vals):
        obj_employee_ids = self.env['setting.employee'].search([('available', '=', True)])
        request = super(SettingEmployee, self).create(vals)
        if any(obj_employee for obj_employee in obj_employee_ids if obj_employee_ids and obj_employee.employee_id.id == request.employee_id.id):
            raise UserError('Ya existe una configuración para este comercial.')
            _logger.info("Ya existe una configuración para este comercial.")
        if not request.employee_id.user_id:
            raise UserError('El empleado no tiene un usuario relacionado.')
            _logger.info("El empleado no tiene un usuario relacionado.")
        return request


class SessionUsers(models.Model):
    _name = 'session.users'
    _description = 'Session Users'
    _rec_name = 'user_id'

    user_id = fields.Many2one('res.users', 'User', track_visibility='onchange', required=True, index=True)
    status = fields.Selection([
        ('online', 'Online'),
        ('offline', 'Offline'),
    ], string='Status', index=True)
    status_inactive = fields.Selection([
        ('-', '-'),
        ('inactive', 'Inactive'),
        ('active', 'Active'),
    ], string='Activity', index=True)
    login = fields.Char(related='user_id.login', help="Used to log into the system")
    login_date = fields.Datetime(related='user_id.login_date', string='Latest connection')
    session_duration = fields.Char('Session Duration')
    time_inactive = fields.Char('Time Inactive')

    @api.model
    def create(self, vals):
        obj_session_ids = self.env['session.users'].search([('user_id', '!=', False)])
        request = super(SessionUsers, self).create(vals)
        if any(obj_user for obj_user in obj_session_ids if obj_session_ids and obj_user.user_id.id == request.user_id.id):
            raise UserError('Ya existe una sesión para este usuario.')
            _logger.info("Ya existe una sesión para este usuario.")
        return request

    def action_check_status(self):
        str_user = ''
        obj_session_ids = self.env['session.users'].search([('user_id', '!=', False)])
        if obj_session_ids:
            for obj_session in obj_session_ids:
                if obj_session.user_id:
                    user = obj_session.user_id
                    obj_check = self._check_status_user(user)
                    if obj_check == 'online':
                        obj_session.status = 'online'
                    else:
                        obj_session.status = 'offline'
                    obj_valid = self.validate_sessions(obj_session)
                    if obj_valid:
                        obj_session.session_duration = obj_valid
                    obj_activity = self._status_activity(user)
                    if obj_activity:
                        obj_session.time_inactive = obj_activity[0]
                        obj_session.status_inactive = obj_activity[1]
                    if obj_session.status_inactive != 'active':
                        str_user += obj_session.user_id.name + ', '
        if str_user:
            obj_connect_ids = self.env['setting.users.gm'].search([('outgoing_mail_id', '!=', False)], limit=1)
            if obj_connect_ids:
                self.send_email(obj_connect_ids[0], str_user)
        return False

    def _check_status_user(self, user):
        obj_user_ids = self.env['res.users'].search([('id', '=', user.id)])
        if obj_user_ids:
            obj_user = obj_user_ids[0]
            if obj_user.im_status:
                return obj_user.im_status

    def validate_sessions(self, obj_session):
        now = fields.Datetime.from_string(fields.Datetime.now())
        session_duration = '00:00:00'
        if obj_session.login_date:
            session_duration = str(now - fields.Datetime.from_string(obj_session.login_date)).split('.')[0]
        return session_duration

    def _status_activity(self, user):
        list_model = ['res.partner', 'account.invoice', 'hr.attendance', 'res.users.log']
        now = fields.Datetime.from_string(fields.Datetime.now())
        time_inactive = '00:00:00'
        status_inactive = '-'
        time_pivote = ''
        time_limit = '0:30'
        ok_compare = False
        obj_reference_ids = self.env['crm.lead'].search([('write_uid', '=', user.id)], order='write_date desc', limit=1)
        if obj_reference_ids:
            time_pivote = obj_reference_ids[0].write_date
            ok_compare = True
        if ok_compare and time_pivote:
            for model in list_model:
                obj_model_ids = self.env[model].search([('write_uid', '=', user.id)], order='write_date desc', limit=1)
                if obj_model_ids:
                    time_tmp = obj_model_ids[0].write_date
                    if time_tmp > time_pivote:
                        time_pivote = time_tmp
            time_inactive = str(now - fields.Datetime.from_string(time_pivote)).split('.')[0]
            if time_inactive >= time_limit:
                status_inactive = 'inactive'
            else:
                status_inactive = 'active'
        return time_inactive, status_inactive

    def send_email(self, obj_connect, str_user):
        obj_partner_id = self.env['res.partner'].search([('name', 'like', 'Administra')])[0]
        email_from = obj_connect.email_from
        email_to = obj_connect.email_to
        if obj_partner_id:
            author = obj_partner_id.id
            mail_data = {
                'email_to': email_to,
                'email_from': email_from,
                'subject': 'Usuarios inactivos',
                'body_html': 'Los usuarios: %s están inactivos en el CRM.<br/> Gracias,<br/>Admin GM' % str_user,
                'state': 'outgoing',
                'message_type': 'email',
                'author_id': author,
                'auto_delete': True,
            }
        obj_mail = self.env['mail.mail'].sudo().create(mail_data)
        if obj_mail:
            logging.info("Email created sucessful!")


class SettingUsersGM(models.Model):
    _name = 'setting.users.gm'
    _description = 'Setting Users'
    _rec_name = 'outgoing_mail_id'

    outgoing_mail_id = fields.Many2one('ir.mail_server', "Outgoing mail server", index=True, required=True)
    email_to = fields.Char('Email to')
    email_from = fields.Char('Email from', related='outgoing_mail_id.smtp_user')
