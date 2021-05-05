# uncompyle6 version 3.5.0
# Python bytecode 2.7 (62211)
# Decompiled from: Python 2.7.5 (default, Aug  7 2019, 00:51:29)
# [GCC 4.8.5 20150623 (Red Hat 4.8.5-39)]
# Embedded file name: E:\Desarrollo\reposodoo10_2020\l10n_cu_hlg_erp\l10n_cu_hlg_single_login\models\res_users.py
# Compiled at: 2020-04-08 22:43:46

import werkzeug.contrib.sessions, werkzeug.datastructures, werkzeug.exceptions, werkzeug.local, werkzeug.routing, werkzeug.wrappers, werkzeug.wsgi
from odoo.http import request
from odoo import api
from odoo import fields, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

class res_users(models.Model):
    _inherit = 'res.users'
    session_ids = fields.One2many('ir.sessions', 'user_id', 'User Sessions')
    block_multiple_session = fields.Boolean('Block Multiple Sessions', default=True)

    @api.model
    def _check_session_validity(self, db, uid, passwd):
        if not request:
            return
        now = fields.datetime.now()
        session = request.session
        if session.db and session.uid:
            session_obj = request.env['ir.sessions']
            cr = self.pool.cursor()
            cr.autocommit(True)
            session_ids = session_obj.search([('session_id', '=', session.sid), ('logged_in', '=', True)])
            if session_ids:
                if request.httprequest.path[:5] == '/web/' or request.httprequest.path[:9] == '/im_chat/' or request.httprequest.path[:6] == '/ajax/':
                    for s in session_ids:
                        last_use = now.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                        cr.execute('UPDATE ir_sessions SET last_use=%s WHERE id= %s', (
                         last_use, s.id))

                    cr.commit()
            else:
                session.logout(keep_db=True)
            cr.close()
        return True

    @classmethod
    def check(cls, db, uid, passwd):
        res = super(res_users, cls).check(db, uid, passwd)
        cr = cls.pool.cursor()
        self = api.Environment(cr, uid, {})[cls._name]
        cr.commit()
        cr.close()
        self.browse(uid)._check_session_validity(db, uid, passwd)
        return res

    @api.one
    def action_close_session(self):
        session_obj = request.env['ir.sessions']
        session_ids = session_obj.search([('user_id', '=', self.id), ('type_session', '=', 'standard'), ('logged_in', '=', True)])
        redirect = session_ids._close_session()
        if redirect:
            return werkzeug.utils.redirect('/web/login?db=%s' % self.env.cr.dbname, 303)