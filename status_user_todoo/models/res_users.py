from odoo import api, fields, models, _
from datetime import datetime, timedelta
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

    @api.model
    def action_check_status(self):
        now = fields.Datetime.now()
        users = self.search([('active', '=', True), ('share', '=', False)])
        tracked_models = [
            'crm.lead',
            'res.partner',
            'hr.attendance',
            'res.users.log',
            'sale.order',
            'purchase.order',
        ]
        for user in users:
            user.status = user.im_status or 'offline'
            latest_write = self._get_latest_write_date(user.id, tracked_models)
            if not latest_write:
                user.status_inactive = '-'
                user.time_inactive = '00:00:00'
                continue
            delta = now - latest_write
            user.time_inactive = str(delta).split('.')[0]
            user.status_inactive = 'inactive' if delta >= timedelta(minutes=30) else 'active'
        return True

    def _get_latest_write_date(self, user_id, model_names):
        latest = None
        for model_name in model_names:
            model = self.env[model_name]
            record = model.search([('write_uid', '=', user_id)], order='write_date desc', limit=1)
            if record and record.write_date:
                if not latest or record.write_date > latest:
                    latest = record.write_date
        return latest
