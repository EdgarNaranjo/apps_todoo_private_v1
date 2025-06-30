from odoo import fields, models, api, _


class Picking(models.Model):
    _inherit = "stock.picking"

    @api.constrains('state')
    def check_state_confirmed(self):
        env_repair = self.env['repair.order']
        for record in self:
            if record.state  == 'done' and record.origin:
                if record.picking_type_code == 'incoming':
                    repair = env_repair.search([('name', '=', record.origin), ('state', '=', 'pick')], limit=1)
                    if repair:
                        repair.action_validate()
                        repair.message_post(
                            body=_("Repair order validated from picking: ") + record._get_html_link()
                        )
                if record.picking_type_code == 'outgoing':
                    repair = env_repair.search([('name', '=', record.origin), ('state', '=', 'under_repair')], limit=1)
                    if repair:
                        repair.action_repair_end()
                        repair.message_post(
                            body=_("Repair order has changed status from picking: ") + record._get_html_link()
                        )
