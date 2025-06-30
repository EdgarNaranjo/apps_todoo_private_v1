from odoo import _, fields, models, api


class VehicleSerial(models.Model):
    _name = "vehicle.serial"
    _description = _("Vehicle Serial")

    name = fields.Char(
        required=True
    )
    description = fields.Char(
        required=True
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        default=lambda self: self.env.company
    )
    vehicle_model_id = fields.Many2one(
        comodel_name="vehicle.model",
        required=True
    )

    _sql_constraints = [
        (
            "name_company_uniq",
            "unique (name, company_id, vehicle_model_id)",
            _("The name serial must be unique per company!"),
        )
    ]

    def _compute_display_name(self):
        for serial in self:
            name = serial.name
            if serial.description:
                name = f"{name} ({serial.description})"
            serial.display_name = name
