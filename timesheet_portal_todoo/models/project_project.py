# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
from odoo import models, fields, api, _


class Project(models.Model):
    _inherit = 'project.project'

    allow_timesheet_portal = fields.Boolean('Allow portal timesheet')

    @api.onchange('stage_id')
    def onchange_stage_id(self):
        if self.stage_id:
            if self.stage_id.check_final_stage:
                self.allow_timesheet_portal = True
            else:
                self.allow_timesheet_portal = False


class ProjectProjectStage(models.Model):
    _inherit = 'project.project.stage'

    check_final_stage = fields.Boolean('Final stage')
