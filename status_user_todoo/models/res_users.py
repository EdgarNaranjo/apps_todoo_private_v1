from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    status = fields.Selection([
        ('online', 'Online'),
        ('offline', 'Offline'),
    ], string='Status', index=True)
    status_inactive = fields.Selection([
        ('-', '-'),
        ('inactive', 'Inactive'),
        ('active', 'Active'),
    ], string='Activity', index=True)
    time_inactive = fields.Char('Time Inactive')

    def action_check_status(self):
        obj_user_ids = self.env['res.users'].search([('active', '=', True), ('share', '=', False)])
        if obj_user_ids:
            for obj_user in obj_user_ids:
                obj_check = self._check_status_user(obj_user)
                if obj_check == 'online':
                    obj_user.status = 'online'
                else:
                    obj_user.status = 'offline'
                obj_activity = self._status_activity(obj_user)
                if obj_activity:
                    obj_user.time_inactive = obj_activity[0]
                    obj_user.status_inactive = obj_activity[1]
        return False

    def _check_status_user(self, user):
        if user and user.im_status:
            return user.im_status

    def _status_activity(self, user):
        list_model = ['res.partner', 'account.invoice', 'hr.attendance', 'res.users.log', 'sale.order', 'purchase.order']
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
