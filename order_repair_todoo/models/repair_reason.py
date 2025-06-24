from odoo import models, fields, _


class RepairReason(models.Model):
    _name = 'repair.reason'
    _description = 'Repair Reason'
    _order = 'id'

    name = fields.Char(
        'Root Cause',
        required=True,
        translate=True
    )
    parent_id = fields.Many2one(
        'repair.reason',
        'Parent reason'
    )
    company_id = fields.Many2one(
        'res.company',
        'Company',
        default=lambda self: self.env.company
    )

    def name_get(self):
        result = []
        for reason in self:
            name = reason.name
            if reason.parent_id:
                name = f"{reason.parent_id.name} / {reason.name}"
            result.append((reason.id, name))
        return result
