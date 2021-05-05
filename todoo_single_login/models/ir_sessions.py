# uncompyle6 version 3.5.0
# Python bytecode 2.7 (62211)
# Decompiled from: Python 2.7.5 (default, Aug  7 2019, 00:51:29)
# [GCC 4.8.5 20150623 (Red Hat 4.8.5-39)]
# Compiled at: 2020-04-08 22:43:46
import logging
from odoo import api
from odoo import fields, models
from odoo.http import root
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from dateutil.relativedelta import *
from datetime import datetime
_logger = logging.getLogger(__name__)

class ir_sessions(models.Model):
    _name = 'ir.sessions'
    _description = 'Sessions'
    user_id = fields.Many2one('res.users', 'User', ondelete='cascade', required=True)
    logged_in = fields.Boolean('Logged in', required=True, index=True)
    session_id = fields.Char('Session ID', size=100, required=True)
    last_use = fields.Datetime('Last Use')
    ip = fields.Char('Remote IP', size=15, required=True)
    type_session = fields.Selection([
     ('standard', 'Standard'),
     ('movil', 'Movil')], 'Session Type', required=True, default='standard')

    def validate_sessions(self):
        delta = (fields.datetime.now() - relativedelta(hours=1)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        sessions = self.sudo().search([('last_use', '<=', delta), ('type_session', '=', 'standard'), ('logged_in', '=', True)])
        if sessions:
            sessions._close_session()
        return True

    @api.multi
    def _on_session_logout(self):
        cr = self.pool.cursor()
        cr.autocommit(True)
        for session in self:
            session.sudo().write({'logged_in': False})

        cr.commit()
        cr.close()
        return True

    @api.multi
    def _close_session(self):
        redirect = False
        for r in self:
            if r.user_id.id == self.env.user.id:
                redirect = True
            session = root.session_store.get(r.session_id)
            session.logout(keep_db=True, env=self.env)

        return redirect