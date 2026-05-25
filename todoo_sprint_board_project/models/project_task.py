from odoo import api, models, fields, _
from odoo.exceptions import ValidationError, UserError
from .const import CLOSING_STAGE_KEYWORDS


class TaskScrumExtend(models.Model):
    """Extends project.task with Scrum fields and logic."""
    _inherit = ['project.task']

    @api.model
    def _get_estimate_effort(self):
        return [
            ("1", "1"),
            ("2", "2"),
            ("3", "3"),
            ("5", "5"),
            ("8", "8"),
            ("13", "13"),
            ("00", "Not Set"),
        ]

    estimate_effort = fields.Selection(
        selection='_get_estimate_effort',
        string='Estimate Effort',
        help=_('Estimate effort in Fibonacci numbers.'),
        required=True,
        default='00',
        tracking=True
    )

    @api.model
    def _get_real_effort(self):
        return [
            ("1", "1"),
            ("2", "2"),
            ("3", "3"),
            ("5", "5"),
            ("8", "8"),
            ("13", "13"),
            ("00", "Not Set"),
        ]

    real_effort = fields.Selection(
        selection='_get_real_effort',
        string='Real Effort',
        help=_('Real effort in Fibonacci numbers.'),
        default='00',
        tracking=True
    )

    sprint_id = fields.Many2one(
        'project.sprint',
        string='Sprint',
        domain=[('state', '!=', 'closed')],
        help=_('Sprint associated with this task.'),
        tracking=True,
        index=True
    )

    objective_ids = fields.Many2many(
        "project.sprint.objective",
        "sprint_objective_task_rel",
        "task_id",
        "objective_id",
        string="Sprint Objectives",
    )

    @api.constrains('stage_id', 'estimate_effort', 'date_deadline')
    def _validate_stage_requirements(self):
        """Validate requirements when moving task to specific stages"""
        for task in self:
            if task.stage_id and task.stage_id.name:
                stage_name = task.stage_id.name.lower()
                if 'curso' in stage_name:
                    if not task.estimate_effort or task.estimate_effort == '00':
                        raise ValidationError(
                            _("Task '%s' cannot be moved to 'In Progress' "
                              "without a valid estimated effort (greater than 0).") % task.name
                        )
                    if not task.date_deadline:
                        raise ValidationError(
                            _("Task '%s' cannot be moved to 'In Progress' "
                              "without a deadline.") % task.name
                        )

    _CLOSING_STAGES = CLOSING_STAGE_KEYWORDS

    def _is_closing_stage(self, stage):
        name = (stage.name or '').lower().strip()
        return any(keyword in name for keyword in self._CLOSING_STAGES)

    def _check_effort_for_closing(self, stage, vals=None):
        """Raise UserError if estimate/real effort not set when closing a task."""
        for task in self:
            estimate = vals.get('estimate_effort', task.estimate_effort) if vals else task.estimate_effort
            real = vals.get('real_effort', task.real_effort) if vals else task.real_effort
            if not estimate or estimate == '00':
                raise UserError(
                    _("Task '%s' cannot be moved to '%s': estimated effort is missing.")
                    % (task.name, stage.name)
                )
            if not real or real == '00':
                raise UserError(
                    _("Task '%s' cannot be moved to '%s': actual effort is missing.")
                    % (task.name, stage.name)
                )

    @api.onchange('stage_id')
    def _onchange_stage_id_effort(self):
        if not self.stage_id or not self._is_closing_stage(self.stage_id):
            return
        missing = []
        if not self.estimate_effort or self.estimate_effort == '00':
            missing.append(_("estimated effort"))
        if not self.real_effort or self.real_effort == '00':
            missing.append(_("actual effort"))
        if missing:
            self.stage_id = self._origin.stage_id
            return {'warning': {
                'title': _("Cannot Close Task"),
                'message': _("Please fill in %s before moving the task to '%s'.")
                           % (' and '.join(missing), self.stage_id.name or ''),
            }}

    def write(self, vals):
        if 'stage_id' in vals and not self.env.context.get('install_mode'):
            new_stage = self.env['project.task.type'].browse(vals['stage_id'])
            if self._is_closing_stage(new_stage):
                self._check_effort_for_closing(new_stage, vals)
        return super().write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if not self.env.context.get('install_mode'):
            for record in records:
                if record.stage_id and record._is_closing_stage(record.stage_id):
                    record._check_effort_for_closing(record.stage_id)
        return records
