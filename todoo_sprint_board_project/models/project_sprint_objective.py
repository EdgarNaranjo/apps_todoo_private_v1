from odoo import api, fields, models, _
from .const import CLOSED_TASK_STATES


class ProjectSprintObjective(models.Model):
    _name = "project.sprint.objective"
    _description = "Sprint Objective"
    _order = "sequence, id"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    sequence = fields.Integer(default=10)

    name = fields.Char(string="Objective", required=True)

    sprint_id = fields.Many2one(
        "project.sprint",
        string="Sprint",
        required=True,
        ondelete="cascade",
    )

    task_ids = fields.Many2many(
        "project.task",
        "sprint_objective_task_rel",
        "objective_id",
        "task_id",
        string="Tasks",
    )

    notes = fields.Text(string="Notes")

    task_count = fields.Integer(
        string="Total Tasks",
        compute="_compute_stats",
        store=True,
    )
    completed_task_count = fields.Integer(
        string="Completed Tasks",
        compute="_compute_stats",
        store=True,
    )
    completion_rate = fields.Float(
        string="% Completed",
        compute="_compute_stats",
        store=True,
        digits=(5, 1),
    )

    state = fields.Selection([
        ("pending", "Pending"),
        ("achieved", "Achieved"),
        ("not_achieved", "Not Achieved"),
    ], string="State", default="pending", required=True, tracking=True)

    @api.depends("task_ids", "task_ids.state")
    def _compute_stats(self):
        for obj in self:
            total = len(obj.task_ids)
            completed = sum(1 for t in obj.task_ids if t.state in CLOSED_TASK_STATES)
            obj.task_count = total
            obj.completed_task_count = completed
            obj.completion_rate = (completed / total) if total else 0.0

    def action_set_achieved(self):
        self.write({"state": "achieved"})

    def action_set_not_achieved(self):
        self.write({"state": "not_achieved"})

    def action_set_pending(self):
        self.write({"state": "pending"})

    def _auto_evaluate(self):
        """Auto-set state based on live task count. Called at sprint close."""
        for obj in self:
            total = len(obj.task_ids)
            if total == 0:
                # No tasks: keep current state, don't force not_achieved
                continue
            completed = sum(1 for t in obj.task_ids if t.state in CLOSED_TASK_STATES)
            obj.state = "achieved" if completed >= total else "not_achieved"
