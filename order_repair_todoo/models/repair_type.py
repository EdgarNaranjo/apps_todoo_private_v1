from odoo import fields, models, _, api


class RepairType(models.Model):
    _name = 'repair.type'
    _description = 'Repair Type'

    name = fields.Char(
        string='Repair Type Name',
        copy=False,
        required=True,
        translate=True
    )
    description = fields.Text('Description')
    parent_id = fields.Many2one(
        'repair.type',
        'Parent type'
    )

    def name_get(self):
        result = []
        for repair in self:
            name = repair.name
            if repair.parent_id:
                name = f"{repair.parent_id.name} / {repair.name}"
            result.append((repair.id, name))
        return result
