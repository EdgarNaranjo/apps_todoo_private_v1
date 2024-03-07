# Copyright 2024-TODAY Rapsodoo Iberia S.r.L. (www.rapsodoo.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class MailActivity(models.Model):
    _inherit = 'mail.activity'

    mail_channel_id = fields.Many2one(
        comodel_name='mail.channel',
        string='Mail Channel'
    )
    not_show_channel = fields.Boolean(
        string='No Show Channel Mail'
    )

    def write(self, values):
        user = self.env.user
        if user != self.user_id and user != self.create_uid:
            raise ValidationError(_("You have not access to edit this activity."))
        res = super(MailActivity, self).write(values)
        return res

    def unlink(self):
        user = self.env.user
        if self and not self._context.get('check_user_access'):
            if user != self.user_id and user != self.create_uid:
                raise ValidationError(_("You have not access to delete this activity."))
        return super(MailActivity, self).unlink()

    def _action_done(self, feedback=False, attachment_ids=None):
        user = self.env.user
        if user != self.user_id and user != self.create_uid:
            raise ValidationError(_("You have not access to edit this activity."))
        res_model_id = self.res_model_id
        res_id = self.res_id
        activities = self.search([('id', '!=', self.id), ('res_id', '=', res_id),
                                  ('res_model_id', '=', res_model_id.id)])
        if activities:
            activities.with_context(check_user_access=True).unlink()
        return super(MailActivity, self)._action_done(feedback, attachment_ids)

    @api.model_create_multi
    def create(self, vals_list):
        res = False
        for rec in vals_list:
            assigned_user_id = rec['user_id']
            res = super(MailActivity, self).create(rec)
            if 'mail_channel_id' in rec and rec['mail_channel_id']:
                channel = self.env['mail.channel'].browse(rec['mail_channel_id'])
                related_user_ids = channel.channel_partner_ids.user_ids
                for each in related_user_ids:
                    if each.id != assigned_user_id:
                        rec['user_id'] = each.id
                        rec['not_show_channel'] = True
                        res = super(MailActivity, self).create(rec)
        return res
