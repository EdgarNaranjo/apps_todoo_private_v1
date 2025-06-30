from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    is_show_repair_form = fields.Boolean()

    def _is_repair_form_available(self):
        self.ensure_one()
        return self.is_show_repair_form