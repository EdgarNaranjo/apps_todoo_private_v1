# controllers/main.py
import json
import logging
from datetime import date, datetime
from odoo import http, _
from odoo.http import request
import random
from odoo.addons.todoo_sprint_board_project_19.services.ai_service import SprintBoardAIService

_logger = logging.getLogger(__name__)

CLOSED_STATES = {"1_done", "1_canceled", "03_approved"}


class SprintBoardController(http.Controller):

    # ── Helper ────────────────────────────────────────────────────────────

    @staticmethod
    def _user_lang():
        """Return the BCP-47 language code of the current user (e.g. 'es', 'en', 'fr')."""
        lang_code = request.env.user.lang or "en_US"
        return lang_code.split("_")[0]  # 'es_ES' -> 'es'

    @staticmethod
    def _is_bug(task):
        """True si la tarea es un bug.
        1. If type_id.code is set: code in ('ERR','BUG','ERROR','DEFECTO')
        2. If code is empty: type_id.name contains .error. or .bug..
        """
        if not task.type_id:
            return False
        code = (task.type_id.code or "").strip().upper()
        if code:
            return code in ("ERR", "BUG", "ERROR", "DEFECTO", "DEFECT")
        name = (task.type_id.name or "").lower()
        return "error" in name or "bug" in name

    # ── Rutas autenticadas ─────────────────────────────────────────────────

    @http.route("/sprint-board/check-today", type="json", auth="user", methods=["GET", "POST"])
    def check_today(self):
        """Busca si existe un board open cuyo sprint cubre hoy.
        Ademas devuelve todos los sprints in_progress sin board para mostrar sugerencias."""
        today = date.today()
        boards = request.env["sprint.board"].search([("state", "=", "open")])
        user_task_sprint_ids = set(request.env["project.task"].search([
            ("user_ids", "in", [request.env.uid]), ("sprint_id", "!=", False),
        ]).mapped("sprint_id").ids)
        active = boards.filtered(
            lambda b: (
                b.sprint_id.start_date and b.sprint_id.end_date
                and b.sprint_id.start_date.date() <= today <= b.sprint_id.end_date.date()
                and (request.env.user in (b.creator_id | b.responsible_ids | b.viewer_ids)
                     or b.sprint_id.id in user_task_sprint_ids)
            )
        )
        # Sprints in_progress de hoy que no tienen ningun board creado
        sprints_today = request.env["project.sprint"].search([
            ("state", "=", "in_progress"),
            ("start_date", "<=", today),
            ("end_date", ">=", today),
        ])
        sprints_with_board = set(request.env["sprint.board"].search([
            ("sprint_id", "in", sprints_today.ids),
            ("state", "=", "open"),
        ]).mapped("sprint_id").ids)
        suggested_sprints = [
            {
                "id":         s.id,
                "name":       s.name,
                "end_date":   s.end_date.date().isoformat() if s.end_date else None,
                "task_count": len(s.task_ids),
            }
            for s in sprints_today
            if s.id not in sprints_with_board
        ]
        if active:
            return {"board_id": active[0].id, "suggested_sprints": suggested_sprints}
        return {"no_board": True, "suggested_sprints": suggested_sprints}

    @http.route("/sprint-board/boards", type="json", auth="user", methods=["GET", "POST"])
    def list_boards(self, state=None, date_from=None, date_to=None, page=1, per_page=12, kpi_filter=None):
        """Lista boards accesibles por el usuario con filtros y paginacion."""
        uid = request.env.uid
        # Sprints donde el usuario tiene tareas asignadas
        task_sprint_ids = request.env["project.task"].search([
            ("user_ids", "in", [uid]), ("sprint_id", "!=", False),
        ]).mapped("sprint_id").ids
        domain = [
            "|", ("creator_id", "=", uid),
            "|", ("responsible_ids", "in", [uid]),
            "|", ("viewer_ids", "in", [uid]),
                 ("sprint_id", "in", task_sprint_ids),
        ]
        if state and state != "all":
            domain.append(("state", "=", state))
        all_boards = request.env["sprint.board"].search(domain, order="create_date desc")
        # Prefetch sprint y tasks ANTES de cualquier filtro Python para evitar N+1
        all_boards.mapped("sprint_id.task_ids")
        all_boards.mapped("sprint_id")
        # Filtro por KPI
        if kpi_filter == "bugs":
            all_boards = all_boards.filtered(
                lambda b: any(SprintBoardController._is_bug(t) and t.state not in CLOSED_STATES
                              for t in b.sprint_id.task_ids)
            )
        elif kpi_filter == "at_risk":
            def _is_at_risk(b):
                if not b.sprint_id.end_date:
                    return False
                days = max(0, (b.sprint_id.end_date.date() - today).days)
                tasks = b.sprint_id.task_ids
                done = len(tasks.filtered(lambda t: t.state in CLOSED_STATES))
                pct = round(done / len(tasks) * 100) if tasks else 0
                return days <= 3 and pct < 30
            all_boards = all_boards.filtered(_is_at_risk)
        if date_from or date_to:
            filtered = []
            for b in all_boards:
                if not b.sprint_id.start_date:
                    continue
                s = b.sprint_id.start_date.date()
                e = b.sprint_id.end_date.date() if b.sprint_id.end_date else s
                if date_from and e < datetime.strptime(date_from, "%Y-%m-%d").date():
                    continue
                if date_to and s > datetime.strptime(date_to, "%Y-%m-%d").date():
                    continue
                filtered.append(b.id)
            all_boards = request.env["sprint.board"].browse(filtered)
        total = len(all_boards)
        offset = (int(page) - 1) * int(per_page)
        paged = all_boards[offset:offset + int(per_page)]

        def _serialize(b):
            tasks = b.sprint_id.task_ids
            done = tasks.filtered(lambda t: t.state in CLOSED_STATES)
            bugs = tasks.filtered(
                lambda t: SprintBoardController._is_bug(t)
                and t.state not in CLOSED_STATES
            )
            total_sp = sum(
                int(t.estimate_effort) for t in tasks
                if t.estimate_effort and t.estimate_effort != "00"
            )
            done_sp = sum(
                int(t.estimate_effort) for t in done
                if t.estimate_effort and t.estimate_effort != "00"
            )
            days = max(0, (b.sprint_id.end_date.date() - date.today()).days) if b.sprint_id.end_date else 0
            return {
                "id": b.id, "name": b.name, "state": b.state,
                "sprint_name": b.sprint_id.name,
                "start_date": b.sprint_id.start_date.date().isoformat() if b.sprint_id.start_date else None,
                "end_date":   b.sprint_id.end_date.date().isoformat()   if b.sprint_id.end_date   else None,
                "days_left": days, "total_tasks": len(tasks), "done_tasks": len(done),
                "pct": round(len(done) / len(tasks) * 100) if tasks else 0,
                "total_sp": total_sp, "done_sp": done_sp, "pending_sp": total_sp - done_sp,
                "bug_count": len(bugs), "creator_name": b.creator_id.name,
                "date_closed": b.date_closed.isoformat() if b.date_closed else None,
            }
        # Explicit prefetch to avoid N+1 queries in _serialize
        paged.mapped("sprint_id.task_ids")
        is_editor = request.env.user.has_group("todoo_sprint_board_project_19.group_sprint_board_editor")
        return {
            "boards": [_serialize(b) for b in paged],
            "total": total,
            "page": int(page),
            "per_page": int(per_page),
            "is_editor": is_editor,
        }

    @http.route("/sprint-board/board/<int:board_id>", type="json", auth="user", methods=["GET", "POST"])
    def get_board(self, board_id):
        """Devuelve datos completos de un board."""
        board = request.env["sprint.board"].browse(board_id)
        if not board.exists():
            return {"error": _("Tablero no encontrado")}
        uid = request.env.uid
        has_task = request.env["project.task"].search_count([
            ("user_ids", "in", [uid]), ("sprint_id", "=", board.sprint_id.id)
        ]) > 0
        if uid not in (board.creator_id | board.responsible_ids | board.viewer_ids).ids and not has_task:
            return {"error": _("Sin acceso a este tablero")}
        return board.get_board_data()

    @http.route("/sprint-board/board/create", type="json", auth="user", methods=["POST"])
    def create_board(self, sprint_id, responsible_ids=None, viewer_ids=None, prev_retrospective=None):
        """Crea un nuevo board para el sprint indicado."""
        from odoo.exceptions import UserError as OdooUserError
        sprint = request.env["project.sprint"].browse(int(sprint_id))
        if not sprint.exists():
            return {"error": _("Sprint no encontrado")}
        vals = {"sprint_id": sprint.id}
        if responsible_ids:
            vals["responsible_ids"] = [(6, 0, responsible_ids)]
        if prev_retrospective:
            vals["retrospective"] = f"[Retrospectiva sprint anterior]\n{prev_retrospective}"
        try:
            board = request.env["sprint.board"].create(vals)
        except OdooUserError as e:
            return {"error": str(e)}
        except Exception as e:
            _logger.exception("create_board: unexpected error")
            return {"error": str(e)}
        if viewer_ids:
            board.write({"viewer_ids": [(4, uid) for uid in viewer_ids]})
        return {"board": {"id": board.id, "name": board.name, "state": board.state}}

    @http.route("/sprint-board/board/<int:board_id>/retrospective-generate", type="json", auth="user", methods=["POST"])
    def retrospective_generate(self, board_id):
        """Genera un borrador de retrospectiva con IA para el board."""
        board = request.env["sprint.board"].browse(board_id)
        if not board.exists():
            return {"error": _("Board not found")}
        if request.env.uid not in (board.creator_id | board.responsible_ids).ids:
            return {"error": _("Only editors can generate the retrospective")}
        sprint = board.sprint_id
        tasks  = sprint.task_ids
        cls    = CLOSED_STATES
        done   = tasks.filtered(lambda t: t.state in cls)
        bugs_resolved = tasks.filtered(lambda t: SprintBoardController._is_bug(t) and t.state in cls)
        bugs_pending  = tasks.filtered(lambda t: SprintBoardController._is_bug(t) and t.state not in cls)
        blocked = [t for t in tasks if t.state not in cls and t.write_date and
                   (datetime.utcnow() - t.write_date).days >= max(2, int(t.estimate_effort or 0) * 1.5 if (t.estimate_effort or '00') != '00' else 3)]
        total_sp = sum(int(t.estimate_effort) for t in tasks if t.estimate_effort and t.estimate_effort != "00")
        done_sp  = sum(int(t.estimate_effort) for t in done  if t.estimate_effort and t.estimate_effort != "00")
        pct = round(len(done) / len(tasks) * 100) if tasks else 0
        days = (sprint.end_date.date() - sprint.start_date.date()).days if sprint.start_date and sprint.end_date else 0
        objs = sprint.objective_ids
        obj_achieved = objs.filtered(lambda o: o.state == 'achieved')
        svc = SprintBoardAIService(request.env, self._user_lang())
        prompt = (
            f'Generate the sprint retrospective for "{sprint.name}" ({days} days).\n'
            f'Data: {len(done)}/{len(tasks)} tasks completed ({pct}%), '
            f'{done_sp}/{total_sp} SP, {len(bugs_resolved)} bugs resolved, '
            f'{len(bugs_pending)} bugs pending'
            + (f', {len(blocked)} blocked tasks' if blocked else '') + '.\n'
            + (f'Objectives achieved: {len(obj_achieved)}/{len(objs)}.\n' if objs else '')
            + (f'Open tasks: {chr(10).join("- " + t.name for t in tasks.filtered(lambda t: t.state not in cls)[:5])}.\n' if tasks.filtered(lambda t: t.state not in cls) else '')
            + '\nReply EXACTLY in this format:\n'
            '[SUMMARY: write exactly 3 sentences. Sentence 1: overall performance with concrete data (% completed, SP, bugs resolved). Sentence 2: highlight of the sprint, team achievements or relevant incidents. Sentence 3: overall assessment of the sprint and its impact on the project or team.]\n'
            'WELL: [1 concrete sentence about what worked well, mention a stat if possible]\n'
            'IMPROVE: [1 concrete sentence about the main problem or improvement area]\n'
            'NEXT: [1 actionable recommendation sentence for the next sprint]\n'
            '\nRULES: SUMMARY must be EXACTLY 3 separate sentences (not 1, not 2, but 3). '
            'Each WELL/IMPROVE/NEXT block: 1 short sentence (max 20 words). '
            'Use real sprint data. No markdown. No extra titles.'
            + svc._lang_instruction()
        )
        fallback = (
            f"Sprint {sprint.name} completed {pct}% of tasks in {days} days "
            f"with {done_sp}/{total_sp} SP delivered.\n"
            f"WELL: Team completed {len(done)} of {len(tasks)} planned tasks.\n"
            f"IMPROVE: {'Resolve the ' + str(len(bugs_pending)) + ' pending bugs earlier.' if bugs_pending else 'Review estimates to better adjust capacity.'}\n"
            f"NEXT: Keep the pace and prioritise high-impact tasks at the start of the sprint."
        )
        try:
            text = svc._call_ai(prompt, temperature=0.4).strip()
            if not all(k in text for k in ("WELL:", "IMPROVE:", "NEXT:")):
                text = fallback
        except Exception:
            text = fallback
        return {"retrospective": text}

    @http.route("/sprint-board/board/<int:board_id>/close", type="json", auth="user", methods=["POST"])
    def close_board(self, board_id, retrospective=None):
        board = request.env["sprint.board"].browse(board_id)
        if not board.exists():
            return {"error": _("Tablero no encontrado")}
        if request.env.uid not in (board.creator_id | board.responsible_ids).ids:
            return {"error": _("Solo los editores pueden cerrar el tablero")}
        if retrospective:
            board.sudo().write({"retrospective": retrospective})
        board.sudo().action_close_board()
        return {"ok": True, "date_closed": board.date_closed.isoformat()}

    @http.route("/sprint-board/board/<int:board_id>/ai-order", type="json", auth="user", methods=["POST"])
    def ai_order(self, board_id):
        board = request.env["sprint.board"].browse(board_id)
        if not board.exists() or board.state != "open":
            return {"error": _("Tablero no disponible para IA")}
        if request.env.uid not in (board.creator_id | board.responsible_ids).ids:
            return {"error": _("Only editors can reorder with AI")}
        today = date.today()
        tasks_data = [
            {
                "id": t.id, "name": t.name,
                "type_code": t.type_id.code if t.type_id else "",
                "type_name": t.type_id.name if t.type_id else "",
                "sp": int(t.estimate_effort) if t.estimate_effort and t.estimate_effort != "00" else 0,
                "state": t.state,
                "priority": t.priority,
                "is_priority": bool(t.priority and t.priority != "0"),
                "is_bug": SprintBoardController._is_bug(t),
                "deadline_days": (
                    (t.date_deadline.date() - today).days
                    if t.date_deadline else None
                ),
            }
            for t in board.sprint_id.task_ids
        ]
        ordered_ids = SprintBoardAIService(request.env, self._user_lang()).order_tasks(tasks_data)
        if ordered_ids:
            board.sudo().write({"ai_task_order": json.dumps(ordered_ids)})
        return {"ordered_ids": ordered_ids}

    @staticmethod
    def _get_prev_retrospective(board, env):
        """Get the retrospective of the most recent previous sprint."""
        project_ids = board.sprint_id.project_ids.ids
        if not project_ids:
            return None
        prev = env["sprint.board"].search([
            ("state", "=", "closed"),
            ("retrospective", "!=", False),
            ("sprint_id.project_ids", "in", project_ids),
            ("id", "!=", board.id),
        ], order="date_closed desc", limit=1)
        return prev.retrospective if prev else None

    @staticmethod
    def _compute_style_hint(positive_examples: list, negative_examples: list) -> str:
        """Generate a preferred style description based on accumulated feedback.
        With >= 3 positives, synthesise the learned pattern."""
        if len(positive_examples) < 3:
            return ""
        # Analizar longitud promedio de positivas
        avg_len = sum(len(t.split()) for t in positive_examples) / len(positive_examples)
        style_parts = []
        if avg_len < 15:
            style_parts.append("frases cortas y directas")
        elif avg_len > 25:
            style_parts.append("explicaciones detalladas")
        # Detect if positives have urgency or motivation tone
        motivational_words = {"equipo", "podemos", "juntos", "vamos", "lograr", "adelante", "confianza"}
        urgent_words = {"urgent", "immediately", "critical", "risk", "blocker", "priority"}
        pos_text = " ".join(positive_examples).lower()
        if sum(1 for w in motivational_words if w in pos_text) >= 2:
            style_parts.append("tono motivacional y positivo")
        elif sum(1 for w in urgent_words if w in pos_text) >= 2:
            style_parts.append("direct and action-oriented tone")
        # Detect if they include numerical data
        import re as _re
        if len(_re.findall(r'\d+', pos_text)) > len(positive_examples):
            style_parts.append("includes concrete numerical data")
        return ", ".join(style_parts) if style_parts else ""

    @http.route("/sprint-board/board/<int:board_id>/ai-recommend", type="json", auth="user", methods=["GET", "POST"])
    def ai_recommend(self, board_id, trigger="On board open", force=False):
        board = request.env["sprint.board"].browse(board_id)
        if not board.exists() or board.state != "open":
            return {"error": _("Tablero no disponible para IA")}
        if request.env.uid not in (board.creator_id | board.responsible_ids | board.viewer_ids).ids:
            return {"error": _("Sin acceso a este tablero")}

        # Smart throttle — only for automatic triggers (not forced)
        if not force:
            from datetime import datetime as _dt2, timedelta
            cutoff = _dt2.utcnow() - timedelta(minutes=15)
            recent = request.env["sprint.board.recommendation"].sudo().search([
                ("board_id", "=", board.id),
                ("create_date", ">=", cutoff),
            ], order="create_date desc", limit=1)
            if recent:
                # Allow if progress changed since last recommendation
                sprint = board.sprint_id
                cls_s  = CLOSED_STATES
                current_done = len(sprint.task_ids.filtered(lambda t: t.state in cls_s))
                # Extract done_count from last rec (if in the text)
                # Simplification: if recent within 15 min, skip
                return {"recommendation": None, "skipped": True}

        sprint = board.sprint_id
        tasks = sprint.task_ids
        bugs = tasks.filtered(
            lambda t: SprintBoardController._is_bug(t)
            and t.state not in CLOSED_STATES
        )
        total_sp = sum(int(t.estimate_effort) for t in tasks if t.estimate_effort and t.estimate_effort != "00")
        done_sp = sum(
            int(t.estimate_effort) for t in tasks.filtered(lambda t: t.state in CLOSED_STATES)
            if t.estimate_effort and t.estimate_effort != "00"
        )
        days_left = max(0, (sprint.end_date.date() - date.today()).days) if sprint.end_date else 0
        # Ultimas recs del board para evitar repetir y foco rotativo
        Rec = request.env["sprint.board.recommendation"]
        recent_texts = Rec.search(
            [("board_id", "=", board.id)], order="create_date desc", limit=3
        ).mapped("text")
        rec_count = Rec.search_count([("board_id", "=", board.id)])
        focus_topics = ["progreso y velocidad del equipo", "gestion del tiempo restante",
                        "calidad y deuda tecnica", "distribucion de trabajo entre tareas",
                        "riesgos del sprint"]
        focus = focus_topics[rec_count % len(focus_topics)]
        # Datos enriquecidos
        done_tasks  = len(tasks.filtered(lambda t: t.state in CLOSED_STATES))
        open_tasks  = len(tasks) - done_tasks
        pending_tasks = tasks.filtered(lambda t: t.state not in CLOSED_STATES)
        # Pending tasks with context for the AI (max 15 to avoid saturating the prompt)
        pending_for_ai = [
            {
                "name":    t.name,
                "sp":      int(t.estimate_effort) if t.estimate_effort and t.estimate_effort != "00" else 0,
                "type":    t.type_id.name if t.type_id else "",
                "is_bug":  SprintBoardController._is_bug(t),
                "state":   t.state,
                "blocked": bool(t.write_date and (datetime.utcnow() - t.write_date).days >= 2 and t.state == "01_in_progress"),
                "priority": t.priority == "1",
            }
            for t in pending_tasks[:15]
        ]
        # Feedback filtered to board/project (more relevant than global feedback)
        Rec = request.env["sprint.board.recommendation"]
        project_board_ids = request.env["sprint.board"].search([
            ("sprint_id.project_ids", "in", sprint.project_ids.ids),
        ]).ids
        positive_examples = Rec.sudo().search(
            [("feedback", "=", "positive"), ("board_id", "in", project_board_ids)],
            order="create_date desc", limit=3
        ).mapped("text")
        neg_recs = Rec.sudo().search(
            [("feedback", "=", "negative"), ("board_id", "in", project_board_ids)],
            order="create_date desc", limit=2
        )
        negative_examples = [
            f"{r.text}" + (f" (Motivo: {r.feedback_reason})" if r.feedback_reason else "")
            for r in neg_recs
        ]
        ctx = {
            "sprint_name": sprint.name, "days_left": days_left,
            "total_sp": total_sp, "done_sp": done_sp,
            "bug_count": len(bugs), "trigger": trigger,
            "done_tasks": done_tasks, "open_tasks": open_tasks, "total_tasks": len(tasks),
            "pending_tasks": pending_for_ai,
            "positive_examples": positive_examples,
            "negative_examples": negative_examples,
            "recent_texts": recent_texts,
            "focus": focus,
            "style_hint": self._compute_style_hint(positive_examples, negative_examples),
            "prev_retrospective": board.sprint_id.mapped("project_ids") and self._get_prev_retrospective(board, request.env) or None,
        }
        text = SprintBoardAIService(request.env, self._user_lang()).recommend(ctx)
        rec_id = None
        if text:
            rec = request.env["sprint.board.recommendation"].sudo().create({
                "board_id": board.id, "text": text, "trigger": trigger,
            })
            rec_id = rec.id
        return {"recommendation": text, "rec_id": rec_id}

    @http.route("/sprint-board/recommendation/<int:rec_id>/feedback", type="json", auth="user", methods=["POST"])
    def recommendation_feedback(self, rec_id, feedback, reason=None):
        """Guarda feedback (positive/negative) en una recomendacion. Solo editores del board."""
        rec = request.env["sprint.board.recommendation"].sudo().browse(rec_id)
        if not rec.exists():
            return {"error": _("Recommendation not found")}
        board = rec.board_id
        if request.env.uid not in (board.creator_id | board.responsible_ids).ids:
            return {"error": _("Solo los editores pueden valorar recomendaciones")}
        if feedback not in ("positive", "negative", None):
            return {"error": _("Invalid feedback")}
        # Toggle: si ya tiene ese feedback, lo quita
        new_feedback = None if rec.feedback == feedback else feedback
        rec.write({
            "feedback": new_feedback,
            "feedback_uid": request.env.uid if new_feedback else False,
            "feedback_reason": reason if new_feedback == "negative" else False,
        })
        return {"ok": True, "feedback": new_feedback}

    @http.route("/sprint-board/board/<int:board_id>/ai-headline", type="json", auth="user", methods=["GET", "POST"])
    def ai_headline(self, board_id):
        """Titular corto (1 frase) sobre el estado del sprint. Sin throttle."""
        board = request.env["sprint.board"].browse(board_id)
        if not board.exists() or board.state != "open":
            return {"headline": None}
        if request.env.uid not in (board.creator_id | board.responsible_ids | board.viewer_ids).ids:
            return {"headline": None}
        sprint = board.sprint_id
        tasks  = sprint.task_ids
        closed_states = CLOSED_STATES
        done  = len(tasks.filtered(lambda t: t.state in closed_states))
        total = len(tasks)
        bugs  = len(tasks.filtered(lambda t: SprintBoardController._is_bug(t) and t.state not in closed_states))
        total_sp = sum(int(t.estimate_effort) for t in tasks if t.estimate_effort and t.estimate_effort != "00")
        done_sp  = sum(int(t.estimate_effort) for t in tasks.filtered(lambda t: t.state in closed_states) if t.estimate_effort and t.estimate_effort != "00")
        days_left = max(0, (sprint.end_date.date() - date.today()).days) if sprint.end_date else 0
        pct = round(done / total * 100) if total else 0
        open_tasks = total - done
        pct_sp = round(done_sp / total_sp * 100) if total_sp else 0
        # Famous teamwork quotes to motivate the team
        quotes = [
            "You go faster alone, further together — African proverb",
            "El talento gana partidos, pero el trabajo en equipo gana campeonatos — Michael Jordan",
            "Ninguno de nosotros es tan inteligente como todos nosotros — Ken Blanchard",
            "La fuerza del equipo es cada miembro individual; la fuerza de cada miembro es el equipo — Phil Jackson",
            "Grandes cosas en los negocios nunca las hace una sola persona, las hace un equipo — Steve Jobs",
            "A team is not a group of people who work together. It is a group of people who trust each other — Simon Sinek",
            "Success is not the result of working alone, but of working as a team — Vince Lombardi",
        ]
        # Alternate: 1 in 3 times use a famous quote instead of an analytical headline
        # Combine: analytical headline + possible famous quote in the same prompt
        # The AI decides what fits best based on the sprint state
        prompt = (
            f'Datos del sprint "{sprint.name}":\n'
            f'- Tareas cerradas: {done}/{total} ({pct}%)\n'
            f'- Story Points: {done_sp}/{total_sp} ({pct_sp}%)\n'
            f'- Dias restantes: {days_left}\n'
            f'- Bugs sin resolver: {bugs}\n\n'
            f'Frases celebres disponibles:\n'
        )
        random.seed(datetime.now().minute + datetime.now().hour * 60)
        random.shuffle(quotes)
        prompt += "\n".join(f'- {q}' for q in quotes[:4]) + "\n\n"
        prompt += (
            'Escribe UN titular para mostrar en un dashboard de equipo.\n'
            'LONGITUD: entre 8 y 12 palabras. Ni demasiado corto ni demasiado largo.\n'
            'TONO: directo, claro, con personalidad. Que se lea bien en voz alta.\n'
            'CONTENT: mix ONE concrete sprint stat with context or emotion.\n'
            'FORBIDDEN: "let\'s go", "we can", "team", stacking multiple numbers.\n'
            '\nEJEMPLOS DEL ESTILO QUE BUSCAMOS:\n'
            '- "42% done and 6 days ahead — good pace"\n'
            '- "El sprint avanza bien, pero ese bug sigue esperando"\n'
            '- "5 tareas cerradas, 7 por conquistar antes del viernes"\n'
            '- "La recta final del sprint empieza ahora mismo"\n'
            '- "You go faster alone, further together"\n'
            '- "Tight sprint: every day counts to reach 100%"\n'
            '\nNo punctuation at the end. No quotes. No markdown. Only the headline.'
            + SprintBoardAIService(request.env, self._user_lang())._lang_instruction()
        )
        try:
            text = SprintBoardAIService(request.env, self._user_lang())._call_ai(prompt, temperature=0.9).strip()
            # Limpiar si viene con comillas o puntuacion final
            text = text.strip('"\' .').rstrip('.')
        except Exception:
            text = None
        return {"headline": text}

    @http.route("/sprint-board/overview-kpis", type="json", auth="user", methods=["GET", "POST"])
    def overview_kpis(self):
        """KPIs globales para la pantalla de lista de boards."""
        uid = request.env.uid
        CLOSED = CLOSED_STATES

        # Boards accesibles por el usuario
        domain = [
            "|", ("creator_id", "=", uid),
            "|", ("responsible_ids", "in", [uid]),
                 ("viewer_ids", "in", [uid]),
        ]
        all_boards = request.env["sprint.board"].search(domain)
        active_boards = all_boards.filtered(lambda b: b.state == "open")

        total_tasks = 0
        done_tasks  = 0
        pending_sp  = 0
        bug_count   = 0
        at_risk     = 0

        from datetime import date
        today = date.today()

        for b in active_boards:
            tasks = b.sprint_id.task_ids
            done  = tasks.filtered(lambda t: t.state in CLOSED)
            total_tasks += len(tasks)
            done_tasks  += len(done)
            pending_sp  += sum(
                int(t.estimate_effort) for t in tasks.filtered(lambda t: t.state not in CLOSED)
                if t.estimate_effort and t.estimate_effort != "00"
            )
            bug_count += len(tasks.filtered(
                lambda t: SprintBoardController._is_bug(t)
                and t.state not in CLOSED
            ))
            # En riesgo: <= 3 dias y < 30% completado
            days_left = max(0, (b.sprint_id.end_date.date() - today).days) if b.sprint_id.end_date else 0
            pct = round(len(done) / len(tasks) * 100) if tasks else 0
            if days_left <= 3 and pct < 30:
                at_risk += 1

        return {
            "active_boards":  len(active_boards),
            "total_boards":   len(all_boards),
            "total_tasks":    total_tasks,
            "done_tasks":     done_tasks,
            "pending_sp":     pending_sp,
            "bug_count":      bug_count,
            "at_risk":        at_risk,
            "completion_pct": round(done_tasks / total_tasks * 100) if total_tasks else 0,
        }

    @http.route("/sprint-board/sprints-available", type="json", auth="user", methods=["GET", "POST"])
    def sprints_available(self):
        """Devuelve sprints en estado in_progress para crear un board."""
        sprints = request.env["project.sprint"].search(
            [("state", "=", "in_progress")],
            order="start_date desc",
            limit=50,
        )
        result = []
        for s in sprints:
            total = len(s.task_ids)
            open_count = len(s.task_ids.filtered(lambda t: t.state not in CLOSED_STATES))
            result.append({
                "id": s.id,
                "name": s.name,
                "state": s.state,
                "start_date": s.start_date.date().isoformat() if s.start_date else None,
                "end_date":   s.end_date.date().isoformat()   if s.end_date   else None,
                "task_count": total,
                "open_task_count": open_count,
            })
        return result

    @http.route("/sprint-board/previous-retrospective", type="json", auth="user", methods=["POST"])
    def previous_retrospective(self, sprint_id):
        """Return the retrospective of the most recent closed board for the same projects."""
        sprint = request.env["project.sprint"].browse(int(sprint_id))
        if not sprint.exists() or not sprint.project_ids:
            return {"retrospective": None, "sprint_name": None}
        project_ids = sprint.project_ids.ids
        prev_boards = request.env["sprint.board"].search([
            ("state", "=", "closed"),
            ("retrospective", "!=", False),
            ("sprint_id.project_ids", "in", project_ids),
        ], order="date_closed desc", limit=1)
        if not prev_boards:
            return {"retrospective": None, "sprint_name": None}
        b = prev_boards[0]
        return {"retrospective": b.retrospective, "sprint_name": b.sprint_id.name}

    @http.route("/sprint-board/managers-for-sprint", type="json", auth="user", methods=["POST"])
    def managers_for_sprint(self, sprint_id):
        """Devuelve los project managers del sprint (para responsible_ids)."""
        sprint = request.env["project.sprint"].browse(int(sprint_id))
        if not sprint.exists():
            return []
        managers = sprint.project_ids.mapped("user_id").filtered(lambda u: u and not u.share)
        return [{"id": u.id, "name": u.name, "initials": (u.name or "?")[:2].upper()} for u in managers]

    @http.route("/sprint-board/viewers-for-sprint", type="json", auth="user", methods=["POST"])
    def viewers_for_sprint(self, sprint_id):
        """Devuelve usuarios que deben ser viewers: asignados a tareas del sprint.
        Solo usuarios con grupo Board/Viewer o Board/Editor."""
        sprint = request.env["project.sprint"].browse(int(sprint_id))
        if not sprint.exists():
            return []
        # Usuarios asignados a tareas del sprint
        task_users = sprint.task_ids.mapped("user_ids").filtered(lambda u: not u.share)
        # Filtrar: solo los que tienen al menos grupo Viewer
        viewer_group = request.env.ref("todoo_sprint_board_project_19.group_sprint_board_viewer", raise_if_not_found=False)
        if viewer_group:
            task_users = task_users.filtered(lambda u: viewer_group in u.groups_id)
        return [{"id": u.id, "name": u.name, "initials": (u.name or "?")[:2].upper()} for u in task_users]

    @http.route("/sprint-board/objective/<int:objective_id>/achieve", type="json", auth="user", methods=["POST"])
    def achieve_objective(self, objective_id):
        """Marca un objetivo sin tareas como conseguido (100%)."""
        obj = request.env["project.sprint.objective"].browse(objective_id)
        if not obj.exists():
            return {"error": _("Objetivo no encontrado")}
        if obj.task_ids:
            return {"error": _("Este objetivo tiene tareas asociadas")}
        # Verificar que el usuario es editor del board del sprint
        board = request.env["sprint.board"].search([
            ("sprint_id", "=", obj.sprint_id.id),
            ("state", "=", "open"),
        ], limit=1)
        if not board or request.env.uid not in (board.creator_id | board.responsible_ids).ids:
            return {"error": _("Solo los editores pueden marcar objetivos")}
        obj.sudo().write({"state": "achieved"})
        return {"ok": True}

    @http.route("/sprint-board/board/<int:board_id>/kiosk-activate", type="json", auth="user", methods=["POST"])
    def kiosk_activate(self, board_id):
        board = request.env["sprint.board"].browse(board_id)
        if not board.exists():
            return {"error": _("Tablero no encontrado")}
        if request.env.uid not in (board.creator_id | board.responsible_ids).ids:
            return {"error": _("Only editors can activate the kiosk")}
        board.sudo().action_activate_kiosk()
        kiosk_url = f"{request.httprequest.host_url}sprint-board/kiosk/{board.kiosk_token}"
        return {"kiosk_token": board.kiosk_token, "kiosk_url": kiosk_url, "kiosk_active": True}

    # ── Kiosk publico (sin autenticacion) ─────────────────────────────────

    @http.route("/sprint-board/kiosk/<string:token>", type="http", auth="public", website=False)
    def kiosk_page(self, token, **kwargs):
        """Pagina HTML publica del kiosk."""
        board = request.env["sprint.board"].sudo().search(
            [("kiosk_token", "=", token), ("kiosk_active", "=", True)], limit=1,
        )
        if not board:
            return request.not_found()
        return request.render("todoo_sprint_board_project_19.kiosk_page", {
            "board": board, "sprint": board.sprint_id, "token": token,
        })

    @http.route("/sprint-board/kiosk/<string:token>/data", type="json", auth="public", methods=["GET", "POST"])
    def kiosk_data(self, token):
        """Polling JSON del kiosk (auto-refresh 30s)."""
        board = request.env["sprint.board"].sudo().search(
            [("kiosk_token", "=", token), ("kiosk_active", "=", True)], limit=1,
        )
        if not board:
            return {"error": "invalid_token"}
        data = board.get_board_data()
        data["board"].pop("can_edit", None)
        data["board"].pop("kiosk_token", None)
        data.pop("recommendations", None)
        # Titular IA para el kiosk (generado sin throttle)
        try:
            from odoo.addons.todoo_sprint_board_project_19.services.ai_service import SprintBoardAIService
            sprint   = board.sprint_id
            tasks    = sprint.task_ids
            cls_st   = CLOSED_STATES
            done     = len(tasks.filtered(lambda t: t.state in cls_st))
            total    = len(tasks)
            bugs     = len(tasks.filtered(lambda t: SprintBoardController._is_bug(t) and t.state not in cls_st))
            total_sp = sum(int(t.estimate_effort) for t in tasks if t.estimate_effort and t.estimate_effort != "00")
            done_sp  = sum(int(t.estimate_effort) for t in tasks.filtered(lambda t: t.state in cls_st) if t.estimate_effort and t.estimate_effort != "00")
            days_left = max(0, (sprint.end_date.date() - date.today()).days) if sprint.end_date else 0
            pct      = round(done / total * 100) if total else 0
            pct_sp   = round(done_sp / total_sp * 100) if total_sp else 0
            open_t   = total - done
            quotes = [
                "You go faster alone, further together",
                "El talento gana partidos, pero el trabajo en equipo gana campeonatos",
                "Ninguno de nosotros es tan inteligente como todos nosotros",
                "La fuerza del equipo es cada miembro individual",
                "Grandes cosas nunca las hace una sola persona, las hace un equipo",
            ]
            use_quote = (done % 3 == 2) and days_left > 1
            if use_quote:
                random.seed(datetime.now().minute + datetime.now().hour * 60)
                headline = random.choice(quotes)
            else:
                svc = SprintBoardAIService(request.env, self._user_lang())
                prompt = (
                    f'Sprint "{sprint.name}": {done}/{total} tasks ({pct}%), '
                    f'{open_t} open, {done_sp}/{total_sp} SP ({pct_sp}%), '
                    f'{bugs} bugs, {days_left} days left. '
                    '8-12 word headline for a team TV dashboard. '
                    'Mix ONE concrete sprint stat with context or emotion. '
                    'Clear, direct, with personality. '
                    'Examples: "42% done and 6 days ahead, good pace" / '
                    '"Sprint on track but that bug is still waiting". '
                    'No punctuation at the end. No markdown.'
                    + svc._lang_instruction()
                )
                headline = svc._call_ai(prompt, temperature=0.9).strip().strip('"\' .').rstrip('.')
        except Exception:
            headline = None
        data["board"]["headline"] = headline
        return data
