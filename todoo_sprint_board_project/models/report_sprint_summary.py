from odoo import fields, models
from odoo.tools import drop_view_if_exists


class ReportSprintSummary(models.Model):
    _name = "report.sprint.summary"
    _description = "Sprint Velocity Report"
    _auto = False
    _order = "start_date, sprint_name, line_label"
    _rec_name = "sprint_name"

    sprint_id = fields.Many2one("project.sprint", string="Sprint", readonly=True)
    sprint_name = fields.Char(string="Sprint", readonly=True)
    start_date = fields.Datetime(string="Start", readonly=True)
    state = fields.Selection([
        ("draft", "Planned"),
        ("in_progress", "In Progress"),
        ("closed", "Closed"),
    ], string="State", readonly=True)
    metric_category = fields.Selection([
        ("sp", "Story Points"),
        ("tasks", "Tasks"),
    ], string="Category", readonly=True)
    line_label = fields.Char(string="Metric", readonly=True)
    value = fields.Integer(string="Value", readonly=True)

    def init(self):
        drop_view_if_exists(self.env.cr, self._table)
        # sprint_id is a field added by this module; during initial install
        # _auto_init() for project.task may not have run yet.
        self.env.cr.execute("""
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'project_task' AND column_name = 'sprint_id'
        """)
        if not self.env.cr.fetchone():
            # Create empty view so Odoo does not fail; recreated on next -u
            # once the column exists.
            self.env.cr.execute(f"""
                CREATE OR REPLACE VIEW {self._table} AS
                SELECT NULL::int     AS id,
                       NULL::int     AS sprint_id,
                       NULL::varchar AS sprint_name,
                       NULL::timestamp AS start_date,
                       NULL::varchar AS state,
                       NULL::varchar AS metric_category,
                       NULL::varchar AS line_label,
                       0::int        AS value
                WHERE FALSE
            """)
            return
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW report_sprint_summary AS (
                WITH base AS (
                    SELECT
                        s.id          AS sprint_id,
                        s.name        AS sprint_name,
                        s.start_date,
                        s.state,
                        t.id          AS task_id,
                        t.estimate_effort,
                        t.real_effort,
                        ptt.name      AS stage_name,
                        NOT EXISTS (
                            SELECT 1
                            FROM project_tags_project_task_rel rel
                            JOIN project_tags tag ON tag.id = rel.project_tags_id
                            WHERE rel.project_task_id = t.id
                              AND EXISTS (
                                  SELECT 1 FROM jsonb_each_text(tag.name) kv
                                  WHERE lower(kv.value) = 'no planificada'
                              )
                        ) AS is_planned
                    FROM project_sprint s
                    LEFT JOIN project_task t
                           ON t.sprint_id = s.id AND t.active = TRUE
                    LEFT JOIN project_task_type ptt ON ptt.id = t.stage_id
                ),
                agg AS (
                    SELECT
                        sprint_id,
                        sprint_name,
                        start_date,
                        state,
                        COALESCE(SUM(
                            CASE WHEN estimate_effort IS NOT NULL AND estimate_effort != '00'
                            THEN CAST(estimate_effort AS INTEGER) ELSE 0 END
                        ), 0)::integer AS sp_estimados,
                        COALESCE(SUM(
                            CASE WHEN real_effort IS NOT NULL AND real_effort != '00'
                            THEN CAST(real_effort AS INTEGER) ELSE 0 END
                        ), 0)::integer AS sp_reales,
                        COUNT(CASE WHEN is_planned THEN task_id END)::integer AS tasks_planificadas,
                        COALESCE(SUM(
                            CASE WHEN stage_name::text ~* '(resuelta|completada|done|completed)'
                            THEN 1 ELSE 0 END
                        ), 0)::integer AS tasks_completadas
                    FROM base
                    GROUP BY sprint_id, sprint_name, start_date, state
                )
                SELECT
                    sprint_id * 4 + m.ord  AS id,
                    sprint_id,
                    sprint_name,
                    start_date,
                    state,
                    m.metric_category,
                    m.line_label,
                    m.value
                FROM agg
                CROSS JOIN LATERAL (VALUES
                    (0, 'sp',    'Estimated',  sp_estimados),
                    (1, 'sp',    'Actual',      sp_reales),
                    (2, 'tasks', 'Planned',     tasks_planificadas),
                    (3, 'tasks', 'Completed',   tasks_completadas)
                ) AS m(ord, metric_category, line_label, value)
            )
        """)
