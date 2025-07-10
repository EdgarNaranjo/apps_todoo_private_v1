from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
from datetime import timedelta

_logger = logging.getLogger(__name__)


class SessionUsersLog(models.Model):
    _name = 'session.users.log'
    _description = 'Session Users'
    _inherit = ['mail.activity.mixin', 'mail.thread']
    _rec_name = 'user_id'

    user_id = fields.Many2one('res.users', string='User', required=True, index=True, tracking=True)
    status_inactive = fields.Selection(related='user_id.status_inactive', store=True)
    time_inactive = fields.Char(related='user_id.time_inactive', store=True)

    @api.model
    def create(self, vals):
        if self.search_count([('user_id', '=', vals.get('user_id'))]):
            _logger.warning("A session already exists for user ID %s", vals.get('user_id'))
            raise UserError(_('A session already exists for this user.'))
        return super().create(vals)

    def activity_update_inactive(self):
        inactivity_group = self.env.ref('status_user_advance_todoo.group_notification_inactivity').users
        active_notifiers = inactivity_group.filtered('active')
        model_id = self.env['ir.model']._get_id('session.users.log')
        activity_type_id = self.env.ref('status_user_advance_todoo.mail_act_sessions_user_advance').id
        for user_to in active_notifiers:
            for session in self:
                note = _("User %s inactive, time: %s") % (session.user_id.name, session.time_inactive or 'N/A')
                self.env['mail.activity'].create({
                    'res_id': session.id,
                    'res_model_id': model_id,
                    'user_id': user_to.id,
                    'summary': _('User Inactivity'),
                    'note': note,
                    'activity_type_id': activity_type_id,
                    'date_deadline': fields.Datetime.now() + timedelta(days=1),
                })
                _logger.info("Inactivity notification created for %s", user_to.name)


class ResUsers(models.Model):
    _inherit = 'res.users'

    sessions_count = fields.Integer(string='Sessions', compute='_compute_todo_sessions', store=False)

    def _compute_todo_sessions(self):
        session_model = self.env['session.users.log']
        for user in self:
            user.sessions_count = session_model.search_count([('user_id', '=', user.id)])

    def action_view_sessions(self):
        self.ensure_one()
        action = self.env.ref('status_user_advance_todoo.action_session_users_log').read()[0]
        action['domain'] = [('user_id', '=', self.id)]
        action['context'] = {
            'default_user_id': self.id,
            'from_user_view': True
        }
        return action

    def action_check_status(self):
        res = super().action_check_status()
        inactivity_group = self.env.ref('status_user_advance_todoo.group_notification_inactivity').users
        active_notifiers = inactivity_group.filtered('active')
        all_users = self.search([('active', '=', True), ('share', '=', False)])
        session_model = self.env['session.users.log']
        for user in all_users:
            if not session_model.search_count([('user_id', '=', user.id)]):
                session_model.create({'user_id': user.id})
        inactive_sessions = session_model.search([('status_inactive', '=', 'inactive')])
        to_notify = inactive_sessions.filtered(lambda s: s.user_id.id not in active_notifiers.ids)
        to_notify.activity_update_inactive()
        return res
