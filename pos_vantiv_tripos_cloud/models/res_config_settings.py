from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    module_pos_vantiv_tripos_cloud = fields.Boolean(
        string="Tripos Vantiv Cloud Payment Terminal",
        help="The transactions are processed by Vantiv. Set your Vantiv credentials on the related payment method.",
    )
