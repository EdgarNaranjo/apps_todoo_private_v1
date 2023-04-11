from odoo import api, fields, models, _
from datetime import datetime, timedelta, date

import logging

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class SessionUsersLog(models.Model):
    _name = 'session.users.log'
    _description = 'Session Users'
    _inherit = ['mail.activity.mixin', 'mail.thread']
    _rec_name = 'user_id'

    user_id = fields.Many2one('res.users', 'User', track_visibility='onchange', required=True, index=True)
    status_inactive = fields.Selection(related='user_id.status_inactive')
    time_inactive = fields.Char(related='user_id.time_inactive')

    @api.model
    def create(self, vals):
        obj_session_ids = self.env['session.users.log'].search([('user_id', '!=', False)])
        request = super(SessionUsersLog, self).create(vals)
        if any(obj_user for obj_user in obj_session_ids if obj_session_ids and obj_user.user_id.id == request.user_id.id):
            raise UserError('A session already exists for this user.')
            _logger.info("A session already exists for this user.")
        return request

    def activity_update_inactive(self):
        inactivity_group = self.env.ref('status_user_advance_todoo.group_notification_inactivity').users
        inactivity_filters_to = inactivity_group.filtered(lambda e: e.active)
        for user_to in inactivity_filters_to:
            create_activity = self.env['mail.activity']
            for inactive in self:
                note = "User %s inactive, time: %s" % (inactive.user_id.name, str(inactive.time_inactive))
                date_deadline = datetime.now() + timedelta(days=1)
                data = {
                    'res_id': inactive.id,
                    'res_model_id': self.env['ir.model'].search([('model', '=', 'session.users.log')]).id,
                    'user_id': user_to.id,
                    'summary': 'User Inactivity',
                    'note': note,
                    'activity_type_id': self.env.ref('status_user_advance_todoo.mail_act_sessions_user_advance').id,
                    'date_deadline': date_deadline
                }
                obj_create = create_activity.create(data)
                if obj_create:
                    _logger.info("Notification created at %s " % str(user_to.name))


class ResUsers(models.Model):
    _inherit = 'res.users'

    sessions_count = fields.Integer(compute='_compute_todo_sessions')

    def _compute_todo_sessions(self):
        for obj_user in self:
            obj_sessions = self.env['session.users.log'].search([('user_id', '=', obj_user.id)])
            if obj_sessions:
                obj_user.sessions_count = len(obj_sessions)
            else:
                obj_user.sessions_count = 0

    def action_view_sessions(self):
        for obj_user in self:
            obj_sessions = self.env['session.users.log'].search([('user_id', '=', obj_user.id)])
            if obj_sessions:
                return {
                    'type': 'ir.actions.act_window',
                    'name': 'Sessions',
                    'res_model': 'session.users.log',
                    'view_mode': 'tree,form',
                    'view_type': 'form',
                    'domain': [('id', 'in', obj_sessions.ids)]
                }

    def action_check_status(self):
        res = super(ResUsers, self).action_check_status()
        inactivity_group = self.env.ref('status_user_advance_todoo.group_notification_inactivity').users
        if inactivity_group:
            inactivity_filters_to = inactivity_group.filtered(lambda e: e.active)
            obj_user_ids = self.env['res.users'].search([('active', '=', True), ('share', '=', False)])
            obj_session_log_ids = self.env['session.users.log'].search([('status_inactive', '=', 'inactive')])
            create_sessions = self.env['session.users.log']
            if obj_user_ids:
                for user in obj_user_ids.filtered(lambda e: not e.sessions_count):
                    create_sessions.create({'user_id': user.id})
            if obj_session_log_ids:
                for session in obj_session_log_ids.filtered(lambda e: e.user_id.id not in inactivity_filters_to.ids):
                    session.activity_update_inactive()
        return res

