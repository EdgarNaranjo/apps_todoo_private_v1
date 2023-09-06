from odoo import models, fields, api, _
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError

class ProjectProject(models.Model):
    _inherit = 'project.project'

    @api.model_create_multi
    def create(self, vals_list):
        project = super(ProjectProject, self).create(vals_list)
        if not project.type_ids:
            default_stages = self.env['project.task.type'].search([('default_stage', '=', True)])
            if len(default_stages) > 0:
                project.type_ids = default_stages
        return project

    
