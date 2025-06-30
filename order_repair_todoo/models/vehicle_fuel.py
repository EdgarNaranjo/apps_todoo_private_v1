import logging

from odoo import _, fields, models

_logger = logging.getLogger(__name__)


class VehicleFuel(models.Model):
    _name = "vehicle.fuel"
    _description = _("Vehicle Fuel")

    name = fields.Char(required=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        default=lambda self: self.env.company
    )
    vehicle_brand_ids = fields.One2many(
        comodel_name="vehicle.brand",
        inverse_name="vehicle_fuel_id"
    )
    vehicle_type_id = fields.Many2one(
        comodel_name="vehicle.type"
    )

    _sql_constraints = [
        (
            "name_company_uniq",
            "unique (name, company_id, vehicle_type_id)",
            _("The name of the fuel must be unique per company!"),
        )
    ]

    def _compute_display_name(self):
        for fuel in self:
            name = fuel.name
            if fuel.vehicle_type_id:
                name = f"{name} ({fuel.vehicle_type_id.name})"
            fuel.display_name = name
