# models/res_config_settings.py
from odoo import api, fields, models

AI_PROVIDERS = [
    ("openai",    "OpenAI"),
    ("groq",      "Groq"),
    ("anthropic", "Anthropic"),
    ("gemini",    "Google Gemini"),
    ("mistral",   "Mistral AI"),
    ("ollama",    "Ollama (local)"),
    ("custom",    "Custom / Other"),
]

AI_MODELS = {
    "openai":    "gpt-4o · gpt-4o-mini · gpt-4-turbo · gpt-3.5-turbo",
    "groq":      "llama-3.3-70b-versatile · llama-3.1-8b-instant · mixtral-8x7b-32768 · gemma2-9b-it",
    "anthropic": "claude-3-5-sonnet-20241022 · claude-3-5-haiku-20241022 · claude-3-opus-20240229",
    "gemini":    "gemini-2.0-flash · gemini-1.5-pro · gemini-1.5-flash",
    "mistral":   "mistral-large-latest · mistral-small-latest · codestral-latest",
    "ollama":    "qwen2.5:3b · llama3.2 · mistral · codellama",
    "custom":    "",
}


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    sprint_board_ai_provider = fields.Selection(
        AI_PROVIDERS,
        string="AI Provider",
        config_parameter="sprint_board.ai_provider",
        default="openai",
    )
    sprint_board_ai_api_key = fields.Char(
        string="API Key",
        config_parameter="sprint_board.ai_api_key",
    )
    sprint_board_ai_model = fields.Char(
        string="Primary Model",
        config_parameter="sprint_board.ai_model",
        default="gpt-4o",
    )
    sprint_board_ai_model_fallback = fields.Char(
        string="Fallback Model",
        config_parameter="sprint_board.ai_model_fallback",
        help="If the primary model fails, this one will be tried instead.",
    )
    sprint_board_ai_url = fields.Char(
        string="Base URL (Ollama/Custom)",
        config_parameter="sprint_board.ai_url",
        help="Only for Ollama or custom providers. E.g.: http://localhost:11434",
    )
    sprint_board_ai_model_hint = fields.Char(
        string="Available Models",
        compute="_compute_ai_model_hint",
        help="Recommended models for the selected provider.",
    )

    @api.depends("sprint_board_ai_provider")
    def _compute_ai_model_hint(self):
        for rec in self:
            rec.sprint_board_ai_model_hint = AI_MODELS.get(
                rec.sprint_board_ai_provider or "openai", ""
            )
