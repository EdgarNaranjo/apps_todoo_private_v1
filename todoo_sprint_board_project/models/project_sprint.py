# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.exceptions import ValidationError
from random import randint


class ProjectSprint(models.Model):
    _name = 'project.sprint'
    _description = 'Project Sprint'
    _order = 'start_date desc, name'
    _inherit = [
        'mail.thread',
        'mail.activity.mixin'
    ]

    def _get_default_color(self):
        """Generate random color from 1 to 11 for Kanban view"""
        return randint(1, 11)

    # Core Fields
    name = fields.Char(
        string='Sprint Name',
        default='/',
        index=True,
        tracking=True,
    )

    description = fields.Text(
        string='Description',
        help='Free-form notes about this sprint'
    )

    start_date = fields.Datetime(
        string='Start Date',
        index=True,
        tracking=True,
        help='Sprint start date and time'
    )

    end_date = fields.Datetime(
        string='End Date',
        index=True,
        copy=False,
        tracking=True,
        help='Sprint end date and time'
    )

    color = fields.Integer(
        string='Color',
        default=_get_default_color,
        help='Color for the Kanban view'
    )

    # Relationships
    project_ids = fields.Many2many(
        'project.project',
        string='Projects',
        help='Projects associated with this sprint'
    )

    task_ids = fields.One2many(
        'project.task',
        'sprint_id',
        string='Tasks',
        help='Tasks included in this sprint'
    )
    task_count = fields.Integer(
        string='Task Count',
        compute='_compute_task_count',
        help='Total number of tasks in the sprint'
    )

    active = fields.Boolean(
        default=True,
        tracking=True,
        help='Mark as inactive to archive the sprint'
    )

    objective_ids = fields.One2many(
        'project.sprint.objective',
        'sprint_id',
        string='Objectives',
    )

    state = fields.Selection([
        ('draft', 'Planned'),
        ('in_progress', 'In Progress'),
        ('closed', 'Closed'),
    ], string="State", default='draft', required=True, tracking=True,
       help="Closed sprints do not appear in the sprint selector of tasks.")

    def action_set_in_progress(self):
        self.write({'state': 'in_progress'})
        self._create_burndown_snapshot(initial=True)

    def action_set_closed(self):
        self.write({'state': 'closed'})
        self.objective_ids._compute_stats()   # ensure stored values are fresh
        self.objective_ids._auto_evaluate()
        self._create_burndown_snapshot()

    def action_set_draft(self):
        self.write({'state': 'draft'})

    # -------------------------------------------------------------------------
    # Burndown
    # -------------------------------------------------------------------------

    _CLOSING_STAGES = ("resuelta", "completada", "done", "completed")

    def _get_incomplete_tasks(self):
        self.ensure_one()
        return self.task_ids.filtered(
            lambda t: not any(
                kw in (t.stage_id.name or "").lower()
                for kw in self._CLOSING_STAGES
            )
        )

    def _create_burndown_snapshot(self, date=None, initial=False):
        BurndownLine = self.env["project.sprint.burndown.line"]
        if date is None:
            date = fields.Date.today()

        for sprint in self:
            incomplete = sprint._get_incomplete_tasks()
            remaining_sp = sum(
                int(t.estimate_effort)
                for t in incomplete
                if t.estimate_effort and t.estimate_effort != "00"
            )
            remaining_tasks = len(incomplete)

            # Ideal line
            ideal_sp = 0.0
            ideal_tasks = 0.0
            if sprint.start_date and sprint.end_date:
                start = sprint.start_date.date()
                end = sprint.end_date.date()
                total_days = (end - start).days or 1
                elapsed = (date - start).days
                ratio = max(0.0, 1.0 - elapsed / total_days)

                if initial:
                    ideal_sp = float(remaining_sp)
                    ideal_tasks = float(remaining_tasks)
                else:
                    first = BurndownLine.search([
                        ("sprint_id", "=", sprint.id),
                        ("line_type", "=", "actual"),
                    ], order="date asc", limit=1)
                    if first:
                        ideal_sp = first.remaining_sp * ratio
                        ideal_tasks = first.remaining_tasks * ratio

            sprint._upsert_burndown_line(date, "actual", remaining_sp, remaining_tasks)
            sprint._upsert_burndown_line(date, "ideal", round(ideal_sp), round(ideal_tasks))

    def _upsert_burndown_line(self, date, line_type, remaining_sp, remaining_tasks):
        self.ensure_one()
        BurndownLine = self.env["project.sprint.burndown.line"]
        existing = BurndownLine.search([
            ("sprint_id", "=", self.id),
            ("date", "=", date),
            ("line_type", "=", line_type),
        ], limit=1)
        vals = {"remaining_sp": remaining_sp, "remaining_tasks": remaining_tasks}
        if existing:
            existing.write(vals)
        else:
            BurndownLine.create({
                **vals,
                "sprint_id": self.id,
                "date": date,
                "line_type": line_type,
            })

    def _cron_create_burndown_snapshot(self):
        today = fields.Date.today()
        active_sprints = self.search([("state", "=", "in_progress")])
        active_sprints._create_burndown_snapshot(date=today)

    # Constraints & Methods
    def _compute_task_count(self):
        for sprint in self:
            sprint.task_count = len(sprint.task_ids)

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        """Validate that end_date is after start_date"""
        for sprint in self:
            if sprint.start_date and sprint.end_date:
                if sprint.start_date > sprint.end_date:
                    raise ValidationError(
                        _(("The 'End Date' must be after the 'Start Date'."))
                    )

    # ── Sequence ──────────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('project.sprint') or '/'
        return super().create(vals_list)

    def write(self, vals):
        result = super().write(vals)
        # Auto-update state when dates change and sprint is still in draft
        if {'start_date', 'end_date'} & vals.keys():
            today = fields.Date.today()
            for sprint in self.filtered(lambda s: s.state == 'draft'):
                start_d = sprint.start_date.date() if sprint.start_date else None
                end_d   = sprint.end_date.date()   if sprint.end_date   else None
                if end_d and today > end_d:
                    sprint.write({'state': 'closed'})
                elif start_d and today >= start_d:
                    sprint.write({'state': 'in_progress'})
        return result



