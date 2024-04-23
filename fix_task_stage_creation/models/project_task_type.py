from odoo import models, fields, api, _


class ProjectTaskType(models.Model):
    _inherit = 'project.task.type'

    default_stage = fields.Boolean(
        string='Default Stage',
    )
