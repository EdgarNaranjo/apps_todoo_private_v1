from odoo import fields, models, _


class PosConfig(models.Model):
    _inherit = 'pos.config'

    is_lane = fields.Boolean(default=False)
    show_is_lane = fields.Boolean(compute="_compute_show_is_lane")
    lane_id = fields.Many2one(
        comodel_name='pos_vantiv_tripos_cloud.lane',
        string=_('Lane'),
        required=True,
    )

    def _compute_show_is_lane(self):
        for rec in self:
            rec.show_is_lane = bool(
                rec.payment_method_ids.filtered(
                    lambda r: r.use_payment_terminal == 'tripos_vantiv'
                )
            )
