from odoo import fields, models


class ProjectSprintBurndownLine(models.Model):
    _name = "project.sprint.burndown.line"
    _description = "Sprint Burndown Line"
    _order = "sprint_id, date, line_type"

    sprint_id = fields.Many2one(
        "project.sprint",
        string="Sprint",
        required=True,
        ondelete="cascade",
        index=True,
    )
    date = fields.Date(string="Date", required=True)
    line_type = fields.Selection([
        ("actual", "Actual"),
        ("ideal", "Ideal"),
    ], string="Line", required=True, default="actual")
    remaining_sp = fields.Integer(string="Remaining SP")
    remaining_tasks = fields.Integer(string="Remaining Tasks")
