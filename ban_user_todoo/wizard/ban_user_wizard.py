from odoo import models, fields, api
from odoo.http import root


class BanUserWizard(models.TransientModel):
    _name = 'ban.user.wizard'
    _description = 'Ban User Wizard'

    user_id = fields.Many2one(
        'res.users',
        string="User",
        required=True,
    )
    ban_reason = fields.Text(
        string="Reason"
    )
    banned = fields.Boolean(
        string="Block User",
        compute='get_user_banned'
    )

    @api.depends('user_id')
    def get_user_banned(self):
        for record in self:
            record.banned = False
            if record.user_id.banned:
                record.banned = True

    def action_ban_user(self):
        self.ensure_one()
        if self.banned:
            self.user_id.write({'banned': False})
            type_message = "alert"
            message = f"✅ Your account has been unlocked by an administrator. Reason: {self.ban_reason or 'No reason specified'}."
        else:
            self.user_id.write({'banned': True})
            type_message = "danger"
            message = f"🚫 Your account has been blocked. The session will be closed in a few minutes. Reason: {self.ban_reason or 'No reason specified'}."
        self.env['bus.bus']._sendone(
            self.user_id.partner_id, 'simple_notification', {
                'type': type_message,
                'title': "Account Status Update",
                'message': message,
                'sticky': True,
            }
        )
