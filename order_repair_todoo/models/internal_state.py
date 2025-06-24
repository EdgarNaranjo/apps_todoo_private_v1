from odoo import models, fields, _


class InternalState(models.Model):
    _name = 'internal.state'
    _description = 'Internal state'
    _order = 'id'

    name = fields.Char(
        'Name',
        required=True,
        translate=True
    )
    parent_id = fields.Many2one(
        'internal.state',
        'Parent state'
    )
    company_id = fields.Many2one(
        'res.company',
        'Company',
        default=lambda self: self.env.company
    )
    color = fields.Integer(
        'Color'
    )

    def name_get(self):
        result = []
        for state in self:
            name = state.name
            if state.parent_id:
                name = f"{state.parent_id.name} / {state.name}"
            result.append((state.id, name))
        return result
