/** @odoo-module **/

import { Component, useState, onWillStart, onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class SprintBoardDashboard extends Component {
    static template = "sprint_board_project.SprintBoardDashboard";
    static props = { boardId: Number, onBack: Function };

    setup() {
        this.rpc   = useService("rpc");
        this.notif = useService("notification");
        this.state = useState({
            loading: true, board: null, sprint: null, kpis: null,
            tasks: [], objectives: [], recommendations: [],
            aiLoading: false, aiOrderLoading: false,
            showKioskModal: false, kioskUrl: "",
            showRetroModal: false,
            retroText: "",
            retroLoading: false,
            retroExpanded: false,
            showFeedbackModal: false,
            feedbackModalRecIndex: null,
            feedbackReason: "",
            filterUserId: null,   // null = todos, number = filtrar por usuario
            filterDeptId: null,   // null = todos los departamentos
            filterProjectId: null, // null = todos los proyectos
            health: null, prediction: null, comparison: null,
            headline: null,
            headlineLoading: false,
        });
        onWillStart(() => this._loadBoard());
        onMounted(async () => {
            this._loadRec("On board open");
            this._loadHeadline();
        });
    }

    async _loadHeadline(force = false) {
        // Do not regenerate if headline already loaded (avoid always-same in same session)
        if (!force && this.state.headline) return;
        if (!this.props.boardId) return;
        this.state.headlineLoading = true;
        try {
            const r = await this.rpc(`/sprint-board/board/${this.props.boardId}/ai-headline`, {});
            this.state.headline = r.headline || null;
        } catch (e) {}
        this.state.headlineLoading = false;
    }

    async _loadBoard() {
        this.state.loading = true;
        const d = await this.rpc(`/sprint-board/board/${this.props.boardId}`, {});
        if (d.error) {
            this.notif.add(d.error, { type: "danger" });
            this.props.onBack();
            return;
        }
        // DEBUG: check what arrives in priority/is_priority
        const sample = (d.tasks || []).slice(0, 3).map(t => ({
            id: t.id, name: t.name.slice(0, 25),
            priority: t.priority, is_priority: t.is_priority,
            department_id: t.department_id, department_name: t.department_name,
        }));
        console.log('[Board DEBUG] tasks sample:', JSON.stringify(sample));
        Object.assign(this.state, {
            board: d.board, sprint: d.sprint, kpis: d.kpis,
            health: d.health || null,
            prediction: d.prediction || null,
            comparison: d.comparison || null,
            tasks: d.tasks, objectives: d.objectives,
            recommendations: (d.recommendations || []).slice(0, 5), loading: false,
        });
    }

    // force=true bypasa el throttle de 30 min (llamadas manuales)
    // pero aplica un throttle minimo de 2 min por trigger para evitar spam
    async _loadRec(trigger, force = false) {
        if (!this.state.board || this.state.board.state !== "open") return;
        // Throttle minimo: evitar misma rec en menos de 2 min aunque sea force=true
        const lastRec = this.state.recommendations[0];
        if (lastRec && lastRec.trigger === trigger) {
            const elapsed = (Date.now() - new Date(lastRec.create_date).getTime()) / 1000;
            if (elapsed < 120) return;
        }
        this.state.aiLoading = true;
        const r = await this.rpc(`/sprint-board/board/${this.props.boardId}/ai-recommend`, { trigger, force });
        if (r.recommendation) {
            this.state.recommendations.unshift({
                id: r.rec_id || null,   // ID de BD para poder dar feedback
                text: r.recommendation, trigger,
                create_date: new Date().toISOString(),
                feedback: null,
            });
            // Show max 2: the latest (fresh) and the previous one
            if (this.state.recommendations.length > 5) {
                this.state.recommendations = this.state.recommendations.slice(0, 5);
            }
        }
        this.state.aiLoading = false;
    }

    onAiOrder = async () => {
        this.state.aiOrderLoading = true;
        const r = await this.rpc(`/sprint-board/board/${this.props.boardId}/ai-order`, {});
        if (r.ordered_ids?.length) {
            const om = new Map(r.ordered_ids.map((id, i) => [id, i]));
            this.state.tasks = [...this.state.tasks].sort(
                (a, b) => (om.get(a.id) ?? 9999) - (om.get(b.id) ?? 9999)
            );
            this.notif.add("Tasks reordered with AI ✨", { type: "success" });
            await this._loadRec("After AI sort", true);  // force=true: manual
        } else {
            this.notif.add("Could not sort with AI", { type: "warning" });
        }
        this.state.aiOrderLoading = false;
    }

    onCloseBoard = async () => {
        // Abrir modal de retrospectiva antes de cerrar
        this.state.showRetroModal = true;
        this.state.retroText = "";
        this.state.retroExpanded = false;
        this.state.retroLoading = true;
        try {
            const r = await this.rpc(`/sprint-board/board/${this.props.boardId}/retrospective-generate`, {});
            this.state.retroText = r.retrospective || "";
        } catch(e) {}
        this.state.retroLoading = false;
    }

    closeRetroModal = () => { this.state.showRetroModal = false; }

    confirmClose = async () => {
        this.state.showRetroModal = false;
        const r = await this.rpc(`/sprint-board/board/${this.props.boardId}/close`, {
            retrospective: this.state.retroText || null,
        });
        if (r.ok) {
            this.state.board.state = "closed";
            this.state.board.date_closed = r.date_closed;
            this.notif.add("Board closed and retrospective saved", { type: "success" });
        } else {
            this.notif.add(r.error || "Error al cerrar", { type: "danger" });
        }
    }

    onAchieveObjective = async (objectiveId) => {
        const r = await this.rpc(`/sprint-board/objective/${objectiveId}/achieve`, {});
        if (r.ok) {
            const obj = this.state.objectives.find(o => o.id === objectiveId);
            if (obj) { obj.state = "achieved"; obj.completion_rate = 100; }
            this.notif.add("Objective marked as achieved", { type: "success" });
        } else {
            this.notif.add(r.error || "Error al actualizar el objetivo", { type: "danger" });
        }
    }

    onActivateKiosk = async () => {
        const r = await this.rpc(`/sprint-board/board/${this.props.boardId}/kiosk-activate`, {});
        if (r.kiosk_token) {
            this.state.board.kiosk_active = true;
            this.state.kioskUrl = r.kiosk_url;
            this.state.showKioskModal = true;
        }
    }

    onFeedback = (ev) => {
        const recIndex = parseInt(ev.currentTarget.dataset.recIndex);
        const feedback  = ev.currentTarget.dataset.feedback;
        const rec = this.state.recommendations[recIndex];
        if (!rec || !rec.id) return;
        if (feedback === "negative") {
            // Abrir modal para pedir motivo
            this.state.feedbackModalRecIndex = recIndex;
            this.state.feedbackReason = "";
            this.state.showFeedbackModal = true;
        } else {
            this._saveFeedback(recIndex, "positive", null);
        }
    }

    closeFeedbackModal = () => {
        this.state.showFeedbackModal = false;
        this.state.feedbackModalRecIndex = null;
        this.state.feedbackReason = "";
    }

    confirmNegativeFeedback = async () => {
        const recIndex = this.state.feedbackModalRecIndex;
        const reason   = this.state.feedbackReason.trim() || null;
        this.state.showFeedbackModal = false;
        await this._saveFeedback(recIndex, "negative", reason);
    }

    _saveFeedback = async (recIndex, feedback, reason) => {
        const rec = this.state.recommendations[recIndex];
        if (!rec || !rec.id) return;
        try {
            const r = await this.rpc(
                `/sprint-board/recommendation/${rec.id}/feedback`,
                { feedback, reason }
            );
            if (r.ok) {
                this.state.recommendations[recIndex] = { ...rec, feedback: r.feedback };
            }
        } catch (e) {
            console.warn("Feedback error:", e);
        }
    }

    onCopyKioskUrl = () => {
        navigator.clipboard.writeText(this.state.kioskUrl);
        this.notif.add("Link copied!", { type: "success" });
    }

    // ── Filtro por usuario asignado ───────────────────────────────────────

    get assignableUsers() {
        // List of unique users with tasks in the sprint
        const seen = new Map();
        for (const t of this.state.tasks) {
            for (const u of (t.assignees || [])) {
                if (!seen.has(u.id)) seen.set(u.id, u);
            }
        }
        return Array.from(seen.values()).sort((a, b) => a.name.localeCompare(b.name));
    }

    onUserFilterChange = (ev) => {
        const val = ev.target.value;
        this.state.filterUserId = val ? parseInt(val) : null;
    }

    onDeptFilterChange = (ev) => {
        const val = ev.target.value;
        this.state.filterDeptId = val ? parseInt(val) : null;
    }

    onProjectFilterChange = (ev) => {
        const val = ev.target.value;
        this.state.filterProjectId = val ? val : null;
    }

    get assignableProjects() {
        const seen = new Map();
        for (const t of this.state.tasks) {
            if (t.project_name && !seen.has(t.project_name)) {
                seen.set(t.project_name, t.project_name);
            }
        }
        return Array.from(seen.keys())
            .sort((a, b) => a.localeCompare(b))
            .map(name => ({ name }));
    }

    get assignableDepts() {
        const seen = new Map();
        for (const t of this.state.tasks) {
            if (t.department_id && t.department_name && !seen.has(t.department_id)) {
                seen.set(t.department_id, t.department_name);
            }
        }
        return Array.from(seen.entries())
            .map(([id, name]) => ({ id, name }))
            .sort((a, b) => a.name.localeCompare(b.name));
    }

    // Health indicator helpers
    get healthColor() {
        const s = this.state.health?.status;
        return s === "on_track" ? "#10b981" : s === "at_risk" ? "#f59e0b" : s === "critical" ? "#ef4444" : "#94a3b8";
    }
    get healthBg() {
        const s = this.state.health?.status;
        return s === "on_track" ? "#d1fae5" : s === "at_risk" ? "#fef3c7" : s === "critical" ? "#fee2e2" : "#f1f5f9";
    }

    // Aplica el filtro de usuario a una lista de tareas
    _applyUserFilter(tasks) {
        let result = tasks;
        if (this.state.filterDeptId) {
            result = result.filter(t => t.department_id === this.state.filterDeptId);
        }
        if (this.state.filterProjectId) {
            result = result.filter(t => t.project_name === this.state.filterProjectId);
        }
        if (this.state.filterUserId) {
            result = result.filter(t =>
                (t.assignees || []).some(u => u.id === this.state.filterUserId)
            );
        }
        return result;
    }

    // ── Getters para secciones de tareas ──────────────────────────────────

    // Priority tasks sort order:
    //   1. Overdue (deadline_days < 0) — most urgent first
    //   2. About to expire (0 <= deadline_days <= 3)
    //   3. Con fecha lejana o sin fecha — al final
    _sortPriority(tasks) {
        return [...tasks].sort((a, b) => {
            // 1. Deadline: overdue and upcoming first
            const scoreA = (a.deadline_days == null) ? 9999 : a.deadline_days;
            const scoreB = (b.deadline_days == null) ? 9999 : b.deadline_days;
            if (scoreA !== scoreB) return scoreA - scoreB;
            // 2. Tiebreak: highest priority level first (3 > 2 > 1)
            const prioA = a.priority_level ?? (parseInt(a.priority) || 0);
            const prioB = b.priority_level ?? (parseInt(b.priority) || 0);
            return prioB - prioA;  // desc: 3 estrella antes que 1 estrella
        });
    }

    isDeadlineUrgent(t) {
        return t.deadline_days != null && t.deadline_days <= 3;
    }

    // Detecta prioridad: is_priority booleano del servidor,
    // o fallback: cualquier priority != "0" / 0 (estrella en Odoo)
    _isPriority(t) {
        if (t.is_priority !== undefined && t.is_priority !== null) return !!t.is_priority;
        const p = t.priority;
        return p !== undefined && p !== null && p !== false && p !== "0" && p !== 0;
    }

    get priorityTasks() {
        const tasks = this.state.tasks.filter(t => this._isPriority(t) && !t.is_closed);
        return this._applyUserFilter(this._sortPriority(tasks));
    }
    get bugTasks() {
        return this._applyUserFilter(
            this.state.tasks.filter(t => t.is_bug && !t.is_closed && !this._isPriority(t))
        );
    }
    get inProgressTasks() {
        return this._applyUserFilter(this.state.tasks.filter(
            t => t.state === "01_in_progress" && !t.is_closed
                && !t.is_bug && !this._isPriority(t)
        ));
    }
    get pendingTasks() {
        return this._applyUserFilter(this.state.tasks.filter(
            t => !t.is_closed && t.state !== "01_in_progress"
                && !t.is_bug && !this._isPriority(t)
        ));
    }
    get doneTasks() { return this._applyUserFilter(this.state.tasks.filter(t => t.is_closed)); }

    get typeDistribution() {
        // Color by type name (case-insensitive) + fallback by code
        const getColor = (name, code) => {
            const n = (name || "").toLowerCase();
            const c = (code || "").toUpperCase();
            if (n.includes("error") || n.includes("bug") || c === "ERR" || c === "BUG") return "#ef4444";
            if (n.includes("feature") || n.includes("funcional") || c === "FEAT") return "#6366f1";
            if (n.includes("analisis") || n.includes("analysis") || c === "ANAL") return "#3b82f6";
            if (n.includes("refactor") || c === "REF") return "#8b5cf6";
            if (n.includes("config") || c === "CONF") return "#10b981";
            return "#94a3b8";
        };
        const counts = {};
        for (const t of this.state.tasks) {
            const key = t.type_name || t.type_code || "Sin tipo";
            counts[key] = counts[key] || { code: t.type_code, name: key, count: 0 };
            counts[key].count++;
        }
        const total = this.state.tasks.length || 1;
        return Object.values(counts).map(c => ({
            ...c,
            pct: Math.round(c.count / total * 100),
            color: getColor(c.name, c.code),
        }));
    }

    formatDate = (iso) => {
        if (!iso) return "";
        return new Date(iso).toLocaleDateString("es-ES", {
            day: "numeric", month: "short", year: "numeric",
        });
    }

    // Parsea el formato retro: devuelve { summary, blocks: [{key,icon,text}] }
    parseRetro = (text) => {
        if (!text) return { summary: "", blocks: [] };
        const KEYS = [
            { key: "BIEN:",     icon: "\u2705", label: "Bien" },
            { key: "MEJORAR:", icon: "\u26a0\ufe0f", label: "Mejorar" },
            { key: "SIGUIENTE:", icon: "\ud83d\udca1", label: "Siguiente" },
        ];
        const lines  = text.split("\n").map(l => l.trim()).filter(Boolean);
        const blocks = [];
        const summaryLines = [];
        for (const line of lines) {
            const match = KEYS.find(k => line.startsWith(k.key));
            if (match) {
                blocks.push({ ...match, text: line.slice(match.key.length).trim() });
            } else if (blocks.length === 0) {
                summaryLines.push(line);
            }
        }
        return { summary: summaryLines.join(" "), blocks };
    }

    objIcon = (s, rate) => {
        if (s === "achieved" || rate >= 100) return "fa-circle-check text-success";
        if (s === "not_achieved" || s === "failed") return "fa-circle-xmark text-danger";
        return "fa-circle text-warning";
    }

    objBadgeClass = (s) => {
        return s === "achieved"
            ? "bg-success-subtle text-success"
            : s === "not_achieved" || s === "failed"
            ? "bg-danger-subtle text-danger"
            : "bg-warning-subtle text-warning";
    }

    get sortedObjectives() {
        const withTasks    = this.state.objectives.filter(o => o.task_count > 0);
        const withoutTasks = this.state.objectives.filter(o => o.task_count === 0);
        return [...withTasks, ...withoutTasks];
    }
}
