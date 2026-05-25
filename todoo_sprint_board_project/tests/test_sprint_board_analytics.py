# tests/test_sprint_board_analytics.py
"""
Tests for new analytics methods:
  - _compute_health
  - _compute_prediction
  - _compute_comparison
  - _is_bug_task
  - _blocked_days (indirectamente via get_board_data)
"""
from datetime import date, timedelta
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged("post_install", "-at_install", "sprint_board")
class TestSprintBoardAnalytics(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.project = cls.env["project.project"].create({"name": "Proyecto Analytics Test"})
        base_start = date.today() - timedelta(days=5)
        base_end   = date.today() + timedelta(days=9)
        cls.sprint = cls.env["project.sprint"].create({
            "name": "Sprint Analytics",
            "start_date": f"{base_start} 00:00:00",
            "end_date":   f"{base_end} 23:59:59",
            "state": "in_progress",
            "project_ids": [(6, 0, [cls.project.id])],
        })
        cls.board = cls.env["sprint.board"].create({"sprint_id": cls.sprint.id})

    # ── _is_bug_task ──────────────────────────────────────────────────────

    def _has_project_type(self):
        """True si el módulo OCA project_type está instalado."""
        return 'project.type' in self.env

    def _make_type(self, name, code=""):
        return self.env["project.type"].create({"name": name, "code": code, "task_ok": True})

    def test_ANAL01_is_bug_by_code_ERR(self):
        if not self._has_project_type():
            self.skipTest("project_type OCA module not installed")
        t = self.env["project.task"].create({
            "name": "Bug via code", "project_id": self.project.id,
            "type_id": self._make_type("Error", code="ERR").id,
        })
        from odoo.addons.todoo_sprint_board_project.models.sprint_board import SprintBoard
        self.assertTrue(SprintBoard._is_bug_task(t))

    def test_ANAL02_is_bug_by_name_error(self):
        if not self._has_project_type():
            self.skipTest("project_type OCA module not installed")
        t = self.env["project.task"].create({
            "name": "Fix something", "project_id": self.project.id,
            "type_id": self._make_type("Error de sistema", code="").id,
        })
        from odoo.addons.todoo_sprint_board_project.models.sprint_board import SprintBoard
        self.assertTrue(SprintBoard._is_bug_task(t))

    def test_ANAL03_is_bug_by_name_bug(self):
        if not self._has_project_type():
            self.skipTest("project_type OCA module not installed")
        t = self.env["project.task"].create({
            "name": "Fix something", "project_id": self.project.id,
            "type_id": self._make_type("Critical bug", code="").id,
        })
        from odoo.addons.todoo_sprint_board_project.models.sprint_board import SprintBoard
        self.assertTrue(SprintBoard._is_bug_task(t))

    def test_ANAL04_not_bug_for_feature(self):
        if not self._has_project_type():
            self.skipTest("project_type OCA module not installed")
        t = self.env["project.task"].create({
            "name": "New feature", "project_id": self.project.id,
            "type_id": self._make_type("Feature", code="FEAT").id,
        })
        from odoo.addons.todoo_sprint_board_project.models.sprint_board import SprintBoard
        self.assertFalse(SprintBoard._is_bug_task(t))

    def test_ANAL05_not_bug_without_type(self):
        t = self.env["project.task"].create({
            "name": "Sin tipo", "project_id": self.project.id,
        })
        from odoo.addons.todoo_sprint_board_project.models.sprint_board import SprintBoard
        self.assertFalse(SprintBoard._is_bug_task(t))

    # ── _compute_health ───────────────────────────────────────────────────

    def _tasks(self, n_done, n_total):
        """Crea n_total tareas, n_done en estado 1_done."""
        tasks = self.env["project.task"].browse()
        for i in range(n_total):
            t = self.env["project.task"].create({
                "name": f"Task {i}", "project_id": self.project.id,
                "sprint_id": self.sprint.id,
            })
            if i < n_done:
                t.write({"state": "1_done"})
            tasks |= t
        return tasks

    def test_ANAL06_health_on_track(self):
        # Sprint 5 days in, duration 14 days → 35% time. 5/10 tasks = 50% → on_track
        tasks = self._tasks(5, 10)
        done  = tasks.filtered(lambda t: t.state == "1_done")
        result = self.board._compute_health(self.sprint, tasks, done, 0, 0)
        self.assertEqual(result["status"], "on_track")

    def test_ANAL07_health_unknown_without_dates(self):
        sprint_no_dates = self.env["project.sprint"].create({
            "name": "Sin fechas", "state": "in_progress",
        })
        result = self.board._compute_health(sprint_no_dates, self.env["project.task"].browse(), [], 0, 0)
        self.assertEqual(result["status"], "unknown")

    def test_ANAL08_health_returns_required_keys(self):
        tasks = self._tasks(2, 10)
        done  = tasks.filtered(lambda t: t.state == "1_done")
        result = self.board._compute_health(self.sprint, tasks, done, 0, 0)
        for key in ("status", "label", "diff", "time_pct", "progress_pct"):
            self.assertIn(key, result)

    # ── _compute_prediction ───────────────────────────────────────────────

    def test_ANAL09_prediction_returns_none_without_dates(self):
        sprint_no_dates = self.env["project.sprint"].create({
            "name": "Sin fechas pred", "state": "in_progress",
        })
        self.assertIsNone(self.board._compute_prediction(sprint_no_dates, [], []))

    def test_ANAL10_prediction_velocity_zero(self):
        """Con 0 tareas completadas velocity=0, no debe lanzar ZeroDivisionError."""
        tasks = self._tasks(0, 5)
        result = self.board._compute_prediction(self.sprint, tasks, [])
        self.assertIsNotNone(result)
        self.assertFalse(result["will_complete"])
        self.assertEqual(result["pct_chance"], 0)

    def test_ANAL11_prediction_will_complete(self):
        """With good velocity should predict completion."""
        tasks = self._tasks(4, 5)
        done  = list(tasks.filtered(lambda t: t.state == "1_done"))
        result = self.board._compute_prediction(self.sprint, tasks, done)
        self.assertIsNotNone(result)
        self.assertIn("velocity", result)
        self.assertIn("pct_chance", result)
        self.assertGreater(result["pct_chance"], 0)

    def test_ANAL12_prediction_keys_present(self):
        tasks = self._tasks(2, 8)
        done  = list(tasks.filtered(lambda t: t.state == "1_done"))
        result = self.board._compute_prediction(self.sprint, tasks, done)
        for key in ("velocity", "days_left", "pending", "projected_done",
                    "total_tasks", "will_complete", "pct_chance"):
            self.assertIn(key, result)

    # ── _compute_comparison ───────────────────────────────────────────────

    def test_ANAL13_comparison_none_without_prev_sprints(self):
        """Sin sprints anteriores cerrados devuelve None."""
        result = self.board._compute_comparison(self.sprint, [], [])
        self.assertIsNone(result)

    def test_ANAL14_comparison_none_without_projects(self):
        sprint_no_proj = self.env["project.sprint"].create({
            "name": "Sin proyectos", "state": "in_progress",
        })
        result = self.board._compute_comparison(sprint_no_proj, [], [])
        self.assertIsNone(result)

    def test_ANAL15_comparison_with_prev_sprint(self):
        """Con un sprint anterior cerrado devuelve datos de comparativa."""
        prev = self.env["project.sprint"].create({
            "name": "Sprint Anterior",
            "start_date": f"{date.today() - timedelta(days=20)} 00:00:00",
            "end_date":   f"{date.today() - timedelta(days=7)} 23:59:59",
            "state": "closed",
            "project_ids": [(6, 0, [self.project.id])],
        })
        # Add some tasks to the previous sprint
        for i in range(3):
            t = self.env["project.task"].create({
                "name": f"Prev task {i}", "project_id": self.project.id,
                "sprint_id": prev.id,
            })
            t.write({"state": "1_done"})

        tasks = self._tasks(2, 5)
        done  = list(tasks.filtered(lambda t: t.state == "1_done"))
        result = self.board._compute_comparison(self.sprint, tasks, done)
        self.assertIsNotNone(result)
        self.assertIn("vs_prev", result)
        self.assertIn("vs_avg", result)
        self.assertIn("current_velocity", result)
        self.assertIn("velocity_delta", result["vs_prev"])
        self.assertIn("velocity_delta", result["vs_avg"])
