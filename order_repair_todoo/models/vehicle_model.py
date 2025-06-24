import logging

from odoo import _, fields, models, api

_logger = logging.getLogger(__name__)


class VehicleModel(models.Model):
    _name = "vehicle.model"
    _description = _("VehicleModel")

    name = fields.Char(required=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        default=lambda self: self.env.company
    )
    vehicle_brand_id = fields.Many2one(
        comodel_name="vehicle.brand"
    )
    vehicle_fuel_id = fields.Many2one(
        comodel_name="vehicle.fuel"
    )
    vehicle_type_id = fields.Many2one(
        comodel_name="vehicle.type"
    )

    _sql_constraints = [
        (
            "name_company_uniq",
            "unique (name, vehicle_brand_id, company_id)",
            _("The name of the model must be unique per company!"),
        )
    ]

    def _get_name(self):
        model = self
        name = model.name or ''
        if model.vehicle_brand_id:
            name = "%s (%s)" % (name, model.vehicle_brand_id.name)
        return name

    def name_get(self):
        res = []
        for model in self:
            name = model._get_name()
            res.append((model.id, name))
        return res

    @api.onchange('vehicle_brand_id', 'vehicle_fuel_id')
    def onchange_vehicle_brand_id(self):
        if self.vehicle_brand_id:
            self.vehicle_fuel_id = self.vehicle_brand_id.vehicle_fuel_id.id
        if self.vehicle_fuel_id:
            self.vehicle_type_id = self.vehicle_fuel_id.vehicle_type_id.id
