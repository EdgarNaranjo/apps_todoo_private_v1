from odoo import _, fields, models, api


class VehicleSerial(models.Model):
    _name = "vehicle.serial"
    _description = _("VehicleSerial")

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

    def _get_name(self):
        serial = self
        name = serial.name or ''
        if serial.description:
            name = "%s (%s)" % (name, serial.description)
        return name

    def name_get(self):
        res = []
        for serial in self:
            name = serial._get_name()
            res.append((serial.id, name))
        return res
