# Copyright 2025-TODAY Todooweb (www.todooweb.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class ProjectProject(models.Model):
    _inherit = 'project.project'

    @api.model_create_multi
    def create(self, vals_list):
        projects = super().create(vals_list)
        for project in projects:
            if not project.type_ids:
                default_stages = self.env['project.task.type'].search([
                    ('default_stage', '=', True)
                ])
                if default_stages:
                    project.type_ids = default_stages
        return projects
