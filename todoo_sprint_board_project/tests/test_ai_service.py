# tests/test_ai_service.py
from unittest.mock import patch, MagicMock
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged("post_install", "-at_install", "sprint_board")
class TestAIService(TransactionCase):

    def _get_service(self, provider="openai", model="gpt-4o", api_key="sk-test", url=""):
        from odoo.addons.sprint_board_project.services.ai_service import SprintBoardAIService
        svc = SprintBoardAIService(self.env)
        # Inyectar config directamente sin ir a ir.config_parameter
        svc._provider = provider
        svc._model = model
        svc._api_key = api_key
        svc._url = url
        return svc

    @patch("odoo.addons.sprint_board_project.services.ai_service.requests.post")
    def test_AI01_order_tasks_returns_ids(self, mock_post):
        mock_post.return_value = MagicMock(
            ok=True,
            json=lambda: {"choices": [{"message": {"content": '{"order": [3, 1, 2]}'}}]},
        )
        mock_post.return_value.raise_for_status = lambda: None
        svc = self._get_service()
        tasks = [
            {"id": 1, "name": "A", "type_code": "FEAT", "sp": 3, "state": "01_in_progress", "priority": "0"},
            {"id": 2, "name": "B", "type_code": "ERR",  "sp": 2, "state": "01_in_progress", "priority": "0"},
            {"id": 3, "name": "C", "type_code": "FEAT", "sp": 1, "state": "01_in_progress", "priority": "1"},
        ]
        result = svc.order_tasks(tasks)
        self.assertIsInstance(result, list)
        self.assertEqual(result, [3, 1, 2])  # verifica orden, no solo contenido

    @patch("odoo.addons.sprint_board_project.services.ai_service.requests.post")
    def test_AI02_recommend_returns_string(self, mock_post):
        mock_post.return_value = MagicMock(
            ok=True,
            json=lambda: {"choices": [{"message": {"content": "Enfocate en los bugs criticos."}}]},
        )
        mock_post.return_value.raise_for_status = lambda: None
        svc = self._get_service()
        result = svc.recommend({
            "sprint_name": "S", "days_left": 5,
            "total_sp": 20, "done_sp": 8, "bug_count": 2, "trigger": "test",
        })
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

    @patch("odoo.addons.sprint_board_project.services.ai_service.requests.post")
    def test_AI03_api_failure_returns_empty(self, mock_post):
        mock_post.side_effect = Exception("Connection refused")
        svc = self._get_service()
        result = svc.order_tasks([
            {"id": 1, "name": "X", "type_code": "", "sp": 1, "state": "01_in_progress", "priority": "0"},
        ])
        self.assertEqual(result, [])

    @patch("odoo.addons.sprint_board_project.services.ai_service.requests.post")
    def test_AI04_ollama_uses_custom_url(self, mock_post):
        mock_post.return_value = MagicMock(ok=True, json=lambda: {"response": '{"order": [1]}'})
        mock_post.return_value.raise_for_status = lambda: None
        svc = self._get_service(provider="ollama", model="qwen2.5:3b", url="http://localhost:11434")
        svc.order_tasks([
            {"id": 1, "name": "T", "type_code": "", "sp": 1, "state": "01_in_progress", "priority": "0"},
        ])
        self.assertIn("localhost:11434", mock_post.call_args[0][0])
