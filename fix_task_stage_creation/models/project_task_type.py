from odoo import models, fields, api, _
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError

class ProjectTaskType(models.Model):
    _inherit = 'project.task.type'

    default_stage = fields.Boolean(
        string='Default Stage',
    )
