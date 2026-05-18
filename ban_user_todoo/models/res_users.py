from odoo import models, fields, api, _
from odoo.exceptions import AccessDenied
from datetime import datetime
from odoo.http import request


class ResUsers(models.Model):
    _inherit = 'res.users'

    banned = fields.Boolean(
        string="Banned User",
        default=False,
        help="If checked, the user will not be able to access the system."
    )
    banned_warning = fields.Html(
        string="Warning",
        compute="_compute_banned_warning",
        sanitize=False
    )

    @api.depends('banned')
    def _compute_banned_warning(self):
        for user in self:
            if user.banned:
                user.banned_warning = (
                    "<div style='background-color:#ffcccc; color:#900; padding:10px; border-radius:5px'>"
                    "<b>🚨 This user is blocked 🚨</b><br/>"
                    "You will not be able to access Odoo until an administrator unlocks it.</div>"
                )
            else:
                user.banned_warning = False

    def _check_credentials(self, password, env):
        if self.banned:
            raise AccessDenied(_("🚫 Your account has been blocked. Please contact an administrator."))
        return super()._check_credentials(password, env)

    def _check_access_rights(self, operation, raise_exception=True):
        uid = self.env.uid
        self.env.cr.execute("SELECT banned FROM res_users WHERE id = %s", (uid,))
        result = self.env.cr.fetchone()
        banned = result and result[0]
        if banned:
            if request and hasattr(request, 'session'):
                request.session.logout()
        return super()._check_access_rights(operation, raise_exception)
