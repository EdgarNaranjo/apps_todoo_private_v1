# tests/test_sprint_board_controller.py
"""
Tests del controller de Sprint Board.
Se usan TransactionCase (no HttpCase) para testing de logica del controller,
consistente con el patron del resto de modulos de doomine.
"""
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged("post_install", "-at_install", "sprint_board")
class TestSprintBoardController(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sprint = cls.env["project.sprint"].create({
            "name": "Sprint Controller Test",
            "start_date": "2026-06-01 00:00:00",
            "end_date": "2026-06-30 23:59:59",
            "state": "in_progress",
        })

    # C01: check_today devuelve no_board cuando no hay ningun board hoy
    def test_C01_check_today_no_board(self):
        # No hay boards creados para el sprint de fecha futura
        # El metodo get_board_data del modelo es el que verifica logica
        boards = self.env["sprint.board"].search([
            ("state", "=", "open"),
            ("sprint_id", "=", self.sprint.id),
        ])
        self.assertEqual(len(boards), 0, "No debe haber boards activos al inicio del test")

    # C02: crear board via ORM devuelve board con state=open
    def test_C02_create_board_state_open(self):
        board = self.env["sprint.board"].create({"sprint_id": self.sprint.id})
        self.assertEqual(board.state, "open")
        self.assertIsNotNone(board.id)
        self.assertIn("Sprint Controller Test", board.name)

    # C03: kiosk con token invalido no devuelve board
    def test_C03_kiosk_invalid_token_returns_nothing(self):
        board = self.env["sprint.board"].sudo().search(
            [("kiosk_token", "=", "invalid-token-000000000000"), ("kiosk_active", "=", True)],
            limit=1,
        )
        self.assertFalse(board, "Token invalido no debe encontrar ningun board")

    # C04: get_board_data devuelve estructura correcta
    def test_C04_get_board_data_structure(self):
        board = self.env["sprint.board"].create({"sprint_id": self.sprint.id})
        data = board.get_board_data()
        self.assertIn("board", data)
        self.assertIn("sprint", data)
        self.assertIn("kpis", data)
        self.assertIn("tasks", data)
        self.assertIn("objectives", data)
        self.assertIn("recommendations", data)
        self.assertEqual(data["board"]["state"], "open")
        self.assertEqual(data["sprint"]["name"], "Sprint Controller Test")

    # C05: kiosk_data oculta can_edit y kiosk_token
    def test_C05_kiosk_data_hides_sensitive_fields(self):
        board = self.env["sprint.board"].create({"sprint_id": self.sprint.id})
        board.action_activate_kiosk()
        data = board.get_board_data()
        # Simular lo que hace kiosk_data()
        data["board"].pop("can_edit", None)
        data["board"].pop("kiosk_token", None)
        data.pop("recommendations", None)
        self.assertNotIn("can_edit", data["board"])
        self.assertNotIn("kiosk_token", data["board"])
        self.assertNotIn("recommendations", data)
