# Copyright 2025-TODAY Todooweb (www.todooweb.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProjectTaskType(models.Model):
    _inherit = 'project.task.type'

    default_stage = fields.Boolean(
        string='Default Stage',
        help='When enabled, this stage will be automatically assigned to new projects '
             'that are created without specifying stages. '
             'You can mark multiple stages as default.',
    )
    project_count = fields.Integer(
        string='Projects using this stage',
        compute='_compute_project_count',
        help='Number of active projects that currently have this stage assigned',
    )

    def _compute_project_count(self):
        for stage in self:
            stage.project_count = self.env['project.project'].search_count([
                ('type_ids', 'in', stage.id)
            ])
