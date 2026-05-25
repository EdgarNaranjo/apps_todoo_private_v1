# services/ai_service.py
import json
import logging
import re
import requests

_logger = logging.getLogger(__name__)


class SprintBoardAIService:
    """Abstrae multiples proveedores de IA para el Sprint Board."""

    def __init__(self, env, user_lang=None):
        get = lambda key, default="": env["ir.config_parameter"].sudo().get_param(key, default)
        self._env = env
        self._provider = get("sprint_board.ai_provider", "openai")
        self._api_key  = get("sprint_board.ai_api_key", "")
        self._model    = get("sprint_board.ai_model", "gpt-4o")
        self._model_fallback = get("sprint_board.ai_model_fallback", "")
        self._url      = get("sprint_board.ai_url", "")
        # Language the AI should reply in (BCP-47 code, e.g. 'es', 'en', 'fr')
        self._user_lang = user_lang or "en"

    # ── Language instruction ──────────────────────────────────────────────────

    def _lang_instruction(self) -> str:
        """Return a closing instruction so the AI replies in the user's language."""
        return f"\n\nIMPORTANT: Write your entire response in the language with BCP-47 code '{self._user_lang}'."

    # ── API publica ────────────────────────────────────────────────────────

    def order_tasks(self, tasks: list) -> list:
        """Devuelve lista de task IDs en orden sugerido. [] si hay error."""
        if not tasks:
            return []
        try:
            raw = self._call_ai(self._build_order_prompt(tasks), temperature=0)
            return [int(i) for i in self._extract_json(raw).get("order", [])]
        except Exception as e:
            _logger.warning("SprintBoardAI order_tasks error: %s", e)
            return []

    def recommend(self, context: dict) -> str:
        """Return short recommendation (max 2 sentences). '' on error."""
        try:
            return self._call_ai(self._build_recommend_prompt(context) + self._lang_instruction(), temperature=0.4).strip()
        except Exception as e:
            _logger.warning("SprintBoardAI recommend error: %s", e)
            return ""

    # ── Prompts ────────────────────────────────────────────────────────────

    def _build_order_prompt(self, tasks: list) -> str:
        lines = []
        for t in tasks:
            flags = []
            if t.get("is_priority") or t.get("priority") == "1":
                flags.append("PRIORITARIA")
            if t.get("is_bug") or "error" in (t.get("type_name") or "").lower() or "bug" in (t.get("type_name") or "").lower():
                flags.append("BUG")
            deadline_days = t.get("deadline_days")
            if deadline_days is not None:
                if deadline_days < 0:
                    flags.append("VENCIDA")
                elif deadline_days == 0:
                    flags.append("VENCE-HOY")
                elif deadline_days <= 3:
                    flags.append(f"VENCE-{deadline_days}d")
            flags_str = " ".join(flags)
            lines.append(f"{t['id']}. {flags_str} [{t.get('type_name') or t.get('type_code', '?')}][{t.get('sp', 0)}SP] {t['name']}")
        return (
            "Ordena estas tareas de sprint para maximizar el valor entregado.\n"
            "Criterios en orden de prioridad:\n"
            "  1. Tareas VENCIDAS o VENCE-HOY primero (bloquean el sprint)\n"
            "  2. PRIORITARIA: tareas marcadas como prioritarias por el equipo\n"
            "  3. BUG sin resolver\n"
            "  4. Tareas VENCE-Xd (fecha proxima) antes que las sin fecha\n"
            "  5. Menor SP antes (quick wins)\n"
            "  6. Dependencias implicitas detectadas en los nombres\n"
            'Responde SOLO con JSON: {"order": [id1, id2, ...]} usando los IDs.\n\n'
            "Tareas:\n" + "\n".join(lines)
        )

    def _build_recommend_prompt(self, ctx: dict) -> str:
        total_sp    = ctx.get("total_sp", 1) or 1
        done_sp     = ctx.get("done_sp", 0)
        pct_sp      = round(done_sp / total_sp * 100)
        done_tasks  = ctx.get("done_tasks", 0)
        open_tasks  = ctx.get("open_tasks", 0)
        total_tasks = ctx.get("total_tasks", 0)
        pct_tasks   = round(done_tasks / total_tasks * 100) if total_tasks else 0
        positive    = ctx.get("positive_examples", [])
        negative    = ctx.get("negative_examples", [])
        recent      = ctx.get("recent_texts", [])
        focus       = ctx.get("focus", "el estado general del sprint")
        style_hint  = ctx.get("style_hint", "")
        prev_retro  = ctx.get("prev_retrospective")
        pending     = ctx.get("pending_tasks", [])

        prompt = (
            f'Sprint "{ctx.get("sprint_name", "?")}". '
            f'Progreso: {done_tasks}/{total_tasks} tareas ({pct_tasks}%), '
            f'{done_sp}/{total_sp} SP. '
            f'Bugs sin resolver: {ctx.get("bug_count", 0)}. '
            f'Dias restantes: {ctx.get("days_left", 0)}.\n\n'
        )

        # Tareas pendientes con detalle
        if pending:
            bugs_p    = [t for t in pending if t.get("is_bug")]
            blocked_p = [t for t in pending if t.get("blocked")]
            priority_p = [t for t in pending if t.get("priority")]
            rest      = [t for t in pending if not t.get("is_bug") and not t.get("blocked")]

            def fmt(t):
                flags = []
                if t.get("is_bug"):    flags.append("BUG")
                if t.get("blocked"):  flags.append("BLOQUEADA")
                if t.get("priority"): flags.append("PRIORITARIA")
                sp = f"{t['sp']}SP" if t.get("sp") else "sin SP"
                tipo = t.get("type", "")
                flag_str = f"[{', '.join(flags)}] " if flags else ""
                return f"  - {flag_str}\"{t['name']}\" ({tipo}, {sp})"

            prompt += "TAREAS PENDIENTES:\n"
            if bugs_p:
                prompt += "Bugs sin resolver:\n" + "\n".join(fmt(t) for t in bugs_p) + "\n"
            if blocked_p:
                prompt += "Bloqueadas (>2 dias sin avance):\n" + "\n".join(fmt(t) for t in blocked_p) + "\n"
            if priority_p:
                prompt += "Prioritarias:\n" + "\n".join(fmt(t) for t in priority_p) + "\n"
            if rest:
                prompt += "Resto:\n" + "\n".join(fmt(t) for t in rest[:8]) + "\n"
            prompt += "\n"

        # Contexto del sprint anterior
        if prev_retro:
            # Detectar si tiene formato estructurado BIEN/MEJORAR/SIGUIENTE
            if all(k in prev_retro for k in ("BIEN:", "MEJORAR:", "SIGUIENTE:")):
                prompt += "RETROSPECTIVA SPRINT ANTERIOR:\n" + prev_retro + "\n"
                prompt += "(Usa MEJORAR y SIGUIENTE como prioridad para tus recomendaciones)\n\n"
            else:
                prompt += f"RETROSPECTIVA SPRINT ANTERIOR (detecta patrones, evita repetir errores):\n{prev_retro}\n\n"

        if style_hint:
            prompt += f"ESTILO PREFERIDO POR EL EQUIPO: {style_hint}\n\n"
        if recent:
            prompt += "Recomendaciones ya dadas (NO repetir ni mismo angulo):\n"
            prompt += "\n".join(f'- "{t}"' for t in recent) + "\n\n"
        if positive:
            prompt += "Valoradas positivamente por el equipo:\n"
            prompt += "\n".join(f'- "{e}"' for e in positive) + "\n\n"
        if negative:
            prompt += "NO valoradas (evita este estilo):\n"
            prompt += "\n".join(f'- "{e}"' for e in negative) + "\n\n"

        prompt += (
            f"FOCO: {focus}.\n"
            "Da UNA recomendacion concreta (2 frases, 30-40 palabras). REGLAS:\n"
            "1. Empieza con verbo de accion: 'Asigna...', 'Resuelve...', 'Revisa...', 'Dedica...'\n"
            "2. Menciona tareas concretas por nombre si es relevante.\n"
            "3. Primera frase: la accion. Segunda frase: el impacto esperado.\n"
            "4. Sin 'Deberias', sin relleno corporativo, sin markdown.\n"
            "Solo la recomendacion."
        )
        return prompt


    # ── Dispatch por proveedor ─────────────────────────────────────────────

    def _call_ai(self, prompt: str, temperature: float = 0.3) -> str:
        try:
            return self._dispatch_provider(prompt, temperature)
        except Exception as primary_err:
            fallback = self._model_fallback
            if fallback and fallback != self._model:
                _logger.warning(
                    "SprintBoardAI: primary model '%s' failed (%s). Trying fallback '%s'.",
                    self._model, primary_err, fallback,
                )
                original_model = self._model
                self._model = fallback
                try:
                    return self._dispatch_provider(prompt, temperature)
                finally:
                    self._model = original_model
            raise

    def _dispatch_provider(self, prompt: str, temperature: float) -> str:
        """Dispatch to the active provider method using self._model."""
        if self._provider == "ollama":
            return self._call_ollama(prompt, temperature)
        if self._provider == "anthropic":
            return self._call_anthropic(prompt, temperature)
        if self._provider == "gemini":
            return self._call_gemini(prompt, temperature)
        return self._call_openai_compat(prompt, temperature)

    def _call_openai_compat(self, prompt: str, temperature: float) -> str:
        if self._provider == "custom" and not self._url:
            raise ValueError("sprint_board.ai_url is required for provider 'custom'")
        base_urls = {
            "openai": "https://api.openai.com/v1",
            "groq":   "https://api.groq.com/openai/v1",
            "mistral": "https://api.mistral.ai/v1",
            "custom": self._url.rstrip("/"),
        }
        url = base_urls.get(self._provider, "https://api.openai.com/v1") + "/chat/completions"
        resp = requests.post(
            url,
            json={"model": self._model, "messages": [{"role": "user", "content": prompt}], "temperature": temperature, "max_tokens": 256},
            headers={"Authorization": f"Bearer {self._api_key}"},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    def _call_anthropic(self, prompt: str, temperature: float) -> str:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            json={"model": self._model, "max_tokens": 256, "temperature": temperature, "messages": [{"role": "user", "content": prompt}]},
            headers={"x-api-key": self._api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["content"][0]["text"]

    def _call_gemini(self, prompt: str, temperature: float) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self._model}:generateContent?key={self._api_key}"
        resp = requests.post(
            url,
            json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": temperature, "maxOutputTokens": 256}},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"]

    def _call_ollama(self, prompt: str, temperature: float) -> str:
        base = self._url.rstrip("/") or "http://localhost:11434"
        resp = requests.post(
            f"{base}/api/generate",
            json={"model": self._model, "prompt": prompt, "stream": False, "options": {"temperature": temperature}},
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json().get("response", "")

    # ── Helper ─────────────────────────────────────────────────────────────

    @staticmethod
    def _extract_json(text: str) -> dict:
        """Extrae el primer objeto JSON valido del texto usando balance de llaves."""
        start = text.find("{")
        if start == -1:
            raise ValueError(f"No JSON in response: {text[:200]}")
        depth = 0
        for i, ch in enumerate(text[start:], start):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return json.loads(text[start:i + 1])
        raise ValueError(f"Unbalanced JSON in response: {text[:200]}")
