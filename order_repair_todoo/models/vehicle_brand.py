import logging

from odoo import _, fields, models, api

_logger = logging.getLogger(__name__)


class VehicleBrand(models.Model):
    _name = "vehicle.brand"
    _description = _("Vehicle Brand")

    name = fields.Char(required=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        default=lambda self: self.env.company
    )
    vehicle_fuel_id = fields.Many2one(
        comodel_name="vehicle.fuel"
    )
    vehicle_model_ids = fields.One2many(
        comodel_name="vehicle.model",
        inverse_name="vehicle_brand_id"
    )
    vehicle_type_id = fields.Many2one(
        comodel_name="vehicle.type"
    )

    _sql_constraints = [
        (
            "name_company_uniq",
            "unique (name, vehicle_fuel_id, company_id)",
            _("The name of the brand must be unique per company!"),
        )
    ]

    def _compute_display_name(self):
        for brand in self:
            name = brand.name
            if brand.vehicle_fuel_id:
                name = f"{name} ({brand.vehicle_fuel_id.name})"
            brand.display_name = name

    @api.onchange('vehicle_fuel_id')
    def onchange_vehicle_fuel_id(self):
        if self.vehicle_fuel_id:
            self.vehicle_type_id = self.vehicle_fuel_id.vehicle_type_id.id
