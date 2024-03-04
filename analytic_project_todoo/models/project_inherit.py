# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import models, _, _lt
import json


class Project(models.Model):
    _inherit = 'project.project'

    def _get_stat_buttons(self):
        """"
        Inherit the standard function to add smart button in project overview
        """
        buttons = super(Project, self)._get_stat_buttons()
        if self.user_has_groups('project.group_project_rating'):
            buttons.append({
                'icon': 'tasks',
                'text': _lt('Analytics'),
                'action_type': 'object',
                'action': 'action_view_analytic_project',
                'additional_context': json.dumps({
                    'active_id': self.id,
                }),
                'show': True,
                'sequence': 6,
            })
        return buttons

    def action_view_analytic_project(self):
        """"
        Action to get analytics lines to show in project Overview
        """
        self.ensure_one()
        result = {
            "type": "ir.actions.act_window",
            "res_model": "account.analytic.line",
            "domain": [('account_id', '=', self.analytic_account_id.id)],
            "name": "Analytics",
            'views': [(self.env.ref('analytic.view_account_analytic_line_tree').id, 'list'),
                      (self.env.ref('analytic.view_account_analytic_line_form').id, 'form')],
            'view_mode': 'tree,form',
        }
        return result
