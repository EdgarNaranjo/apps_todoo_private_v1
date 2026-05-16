from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    unit = fields.Selection([
        ('ecu', 'ECU'),
        ('bodywork', 'Bodywork unit'),
        ('abs', 'ABS'),
        ('instrument', 'Instrument panel'),
        ('exchange', 'Unit of exchange'),
        ('airbag', 'Airbag'),
        ('immobilizer', 'Immobilizer'),
        ('other', 'Other units'),
    ], string='Unit', tracking=1)
