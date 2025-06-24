import logging

from odoo import _, fields, models

_logger = logging.getLogger(__name__)


class VehicleType(models.Model):
    _name = "vehicle.type"
    _description = _("VehicleType")

    name = fields.Char(required=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        default=lambda self: self.env.company
    )
    vehicle_fuel_ids = fields.One2many(
        comodel_name="vehicle.fuel",
        inverse_name="vehicle_type_id"
    )
    check_vehicle = fields.Boolean(
        'Its a car'
    )

    _sql_constraints = [
        (
            "name_company_uniq",
            "unique (name, company_id)",
            _("The name of the type must be unique per company!"),
        )
    ]
