# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    def unlink(self):
        if any(line.validated for line in self):
            raise UserError(_("Can't delete a validated line. If you believe this is an error, please contact an Admin."))
        return super().unlink()

