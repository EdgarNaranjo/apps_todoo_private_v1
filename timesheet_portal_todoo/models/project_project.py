# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
from odoo import models, fields, api, _


class Project(models.Model):
    _inherit = 'project.project'

    allow_timesheet_portal = fields.Boolean('Allow portal timesheet')
