/** @odoo-module **/

import { Component, useState, onWillStart, useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { DateTimeInput } from "@web/core/datetime/datetime_input";

const { DateTime } = luxon;

export class SprintBoardList extends Component {
    static template = "sprint_board_project.SprintBoardList";
    static components = { DateTimeInput };
    static props = { onOpenBoard: Function };

    setup() {
        this.rpc    = useService("rpc");
        this.orm    = useService("orm");
        this.notif  = useService("notification");

        this.searchRef     = useRef("responsibleSearchInput");
        this.selectWrapRef = useRef("responsibleSelectWrap");

        this.state = useState({
            boards: [], total: 0, page: 1, perPage: 12, loading: true,
            kpis: null, kpiFilter: null,
            filterState: "open", filterPeriod: "sprint",
            filterDateFrom: null,   // luxon DateTime | null
            filterDateTo:   null,   // luxon DateTime | null
            showRangePicker: false,
            // Modal crear board
            showCreateModal: false,
            prevRetrospective: null,
            prevRetroSprint: null,
            includeRetro: true,
            retroExpanded: false,
            sprints: [],
            selectedSprintId: null,
            responsibleIds: [],
            modalLoading: false,
            taskError: null,
            // Sprint sugerido (sin board creado)
            suggestedSprints: [],
            // Responsible selector (scrum_poker pattern)
            allUsers: [],
            userSearch: "",
            dropdownOpen: false,
            dropdownTop: 0, dropdownLeft: 0, dropdownWidth: 0,
        });

        this._closeTimer = null;

        onWillStart(async () => {
            await Promise.all([this._load(), this._loadKpis(), this._checkSuggestedSprint()]);
        });
    }

    // ── Carga de boards y KPIs ───────────────────────────────────────────

    async _loadKpis() {
        const k = await this.rpc("/sprint-board/overview-kpis", {});
        this.state.kpis = k;
    }

    async _checkSuggestedSprint() {
        try {
            const r = await this.rpc("/sprint-board/check-today", {});
            this.state.suggestedSprints = r.suggested_sprints || [];
        } catch (e) {
            this.state.suggestedSprints = [];
        }
    }

    async _load() {
        this.state.loading = true;
        const p = {
            state:    this.state.filterState === "all" ? null : this.state.filterState,
            page:     this.state.page,
            per_page: this.state.perPage,
            kpi_filter: this.state.kpiFilter,
        };
        if (this.state.filterPeriod === "range") {
            p.date_from = this.state.filterDateFrom ? this.state.filterDateFrom.toFormat("yyyy-MM-dd") : null;
            p.date_to   = this.state.filterDateTo   ? this.state.filterDateTo.toFormat("yyyy-MM-dd")   : null;
        } else if (!["sprint", "all_time"].includes(this.state.filterPeriod)) {
            const days = { week: 7, month: 30, quarter: 90, year: 365 }[this.state.filterPeriod] || 0;
            p.date_from = DateTime.now().minus({ days }).toFormat("yyyy-MM-dd");
        }
        const r = await this.rpc("/sprint-board/boards", p);
        this.state.boards   = r.boards || [];
        this.state.total    = r.total  || 0;
        this.state.isEditor = r.is_editor || false;
        this.state.loading  = false;
    }

    // ── Filters and pagination ──────────────────────────────────────────────

    get totalPages()    { return Math.ceil(this.state.total / this.state.perPage); }
    get activeBoards()  { return this.state.boards.filter(b => b.state === "open"); }
    get closedBoards()  { return this.state.boards.filter(b => b.state === "closed"); }

    onStateChange  = (ev) => { this.state.filterState = ev.target.value; }
    onPeriodChange = (ev) => {
        this.state.filterPeriod    = ev.target.value;
        this.state.showRangePicker = ev.target.value === "range";
    }

    onDateFromChange = (dt) => { this.state.filterDateFrom = dt || null; }
    onDateToChange   = (dt) => { this.state.filterDateTo   = dt || null; }

    get dateFromValue() { return this.state.filterDateFrom || null; }
    get dateToValue()   { return this.state.filterDateTo   || null; }

    onApply = () => { this.state.page = 1; this._load(); this._loadKpis(); }
    onClear = () => {
        Object.assign(this.state, {
            filterState: "open", filterPeriod: "sprint",
            filterDateFrom: null, filterDateTo: null,
            showRangePicker: false, page: 1, kpiFilter: null,
        });
        this._load(); this._loadKpis();
    }
    onPagePrev  = () => { this.state.page = Math.max(1, this.state.page - 1); this._load(); }
    onPageNext  = () => { this.state.page = Math.min(this.totalPages, this.state.page + 1); this._load(); }
    onPageClick = (ev) => { this.state.page = parseInt(ev.currentTarget.dataset.page); this._load(); }
    onPerPageChange = (ev) => { this.state.perPage = parseInt(ev.target.value); this.state.page = 1; this._load(); }

    onKpiClick = (ev) => {
        const filter = ev.currentTarget.dataset.kpiFilter;
        if (this.state.kpiFilter === filter) {
            this.state.kpiFilter = null;
        } else {
            this.state.kpiFilter = filter;
            if (["active", "bugs", "at_risk"].includes(filter)) {
                this.state.filterState = "open";
            }
        }
        this.state.page = 1;
        this._load();
    }

    openBoard         = (id) => { this.props.onOpenBoard(id); }
    onBoardCardClick  = (ev) => { this.props.onOpenBoard(parseInt(ev.currentTarget.dataset.boardId)); }

    cardAccentColor(b) {
        if (b.state === "closed") return "#64748b";
        if (b.days_left <= 2 && b.pct < 20) return "#f59e0b";
        return "#6366f1";
    }

    // ── Modal Crear Board ─────────────────────────────────────────────────

    onCreateBoard = async () => {
        this.state.showCreateModal  = true;
        this.state.selectedSprintId = null;
        this.state.responsibleIds   = [];
        this.state.taskError        = null;
        this.state.userSearch       = "";
        this.state.dropdownOpen     = false;
        // Cargar sprints y todos los usuarios en paralelo
        const [sprints, users] = await Promise.all([
            this.rpc("/sprint-board/sprints-available", {}),
            this.orm.searchRead(
                "res.users",
                [["share", "=", false], ["active", "=", true]],
                ["id", "name"],
                { order: "name asc", limit: 300 }
            ),
        ]);
        this.state.sprints  = sprints;
        this.state.allUsers = users;
        // Pre-seleccionar el sprint en curso
        const inProgress = sprints.find(s => s.state === "in_progress");
        if (inProgress) {
            await this._selectSprint(inProgress.id);
        }
    }

    _selectSprint = async (sprintId) => {
        this.state.selectedSprintId  = sprintId;
        this.state.prevRetrospective = null;
        this.state.prevRetroSprint   = null;
        this.state.retroExpanded     = false;
        // Validar inmediatamente al seleccionar el sprint
        const sprint = this.state.sprints.find(s => s.id === sprintId);
        if (sprint && sprint.task_count === 0) {
            this.state.taskError = "This sprint has no tasks. Add tasks to the sprint before creating a board.";
        } else if (sprint && sprint.open_task_count === 0) {
            this.state.taskError = "All tasks in this sprint are closed. There is nothing pending to show on a board.";
        } else {
            this.state.taskError = null;
        }
        // Pre-rellenar responsables y cargar retro del sprint anterior en paralelo
        const [managers, retroData] = await Promise.all([
            this.rpc("/sprint-board/managers-for-sprint", { sprint_id: sprintId }),
            this.rpc("/sprint-board/previous-retrospective", { sprint_id: sprintId }),
        ]);
        this.state.responsibleIds    = managers.map(u => u.id);
        this.state.prevRetrospective = retroData.retrospective || null;
        this.state.prevRetroSprint   = retroData.sprint_name   || null;
    }

    onSelectSprintClick = async (ev) => {
        await this._selectSprint(parseInt(ev.currentTarget.dataset.sprintId));
    }

    closeCreateModal = () => {
        this.state.showCreateModal = false;
        this.state.dropdownOpen    = false;
    }

    // Parsea retro: { summary, blocks:[{key,icon,label,text}] } — mismo formato que dashboard
    parsePrevRetro = (text) => {
        if (!text) return { summary: "", blocks: [] };
        const KEYS = [
            { key: "BIEN:",      icon: "\u2705",         label: "Bien" },
            { key: "MEJORAR:",   icon: "\u26a0\ufe0f",   label: "Mejorar" },
            { key: "SIGUIENTE:", icon: "\ud83d\udca1",   label: "Siguiente" },
        ];
        const lines = text.split("\n").map(l => l.trim()).filter(Boolean);
        const blocks = [];
        const summaryLines = [];
        for (const line of lines) {
            const match = KEYS.find(k => line.startsWith(k.key));
            if (match) blocks.push({ ...match, text: line.slice(match.key.length).trim() });
            else if (blocks.length === 0) summaryLines.push(line);
        }
        return { summary: summaryLines.join(" "), blocks };
    }

    onCreateBoardForSprint = async (sprintId) => {
        // Open create modal pre-selecting the suggested sprint
        await this.onCreateBoard();
        await this._selectSprint(sprintId);
    }

    confirmCreateBoard = async () => {
        if (!this.state.selectedSprintId) return;
        const sprint = this.state.sprints.find(s => s.id === this.state.selectedSprintId);
        if (sprint && sprint.task_count === 0) {
            this.state.taskError = "This sprint has no tasks. Add tasks to the sprint before creating a board.";
            return;
        }
        if (sprint && sprint.open_task_count === 0) {
            this.state.taskError = "All tasks in this sprint are closed. There is nothing pending to show on a board.";
            return;
        }
        this.state.taskError    = null;
        this.state.modalLoading = true;
        try {
            const result = await this.rpc("/sprint-board/board/create", {
                sprint_id:          this.state.selectedSprintId,
                responsible_ids:    this.state.responsibleIds,
                viewer_ids:         this.state.allUsers.map(u => u.id),
                prev_retrospective: (this.state.includeRetro && this.state.prevRetrospective) || null,
            });
            if (result.error) {
                this.notif.add(result.error, { type: "danger" });
            } else {
                this.state.showCreateModal = false;
                this._loadKpis();
                this.props.onOpenBoard(result.board.id);
            }
        } catch (e) {
            this.notif.add("Error al crear el board", { type: "danger" });
        } finally {
            this.state.modalLoading = false;
        }
    }

    get selectedSprint() {
        return this.state.sprints.find(s => s.id === this.state.selectedSprintId) || null;
    }

    sprintDotStyle  = (sprint) => {
        const color = sprint.state === "in_progress" ? "#10b981" : "#6366f1";
        return `width:10px;height:10px;display:inline-block;border-radius:50%;background:${color}`;
    }
    sprintBadgeStyle = (sprint) => sprint.state === "in_progress" ? "background:#d1fae5" : "background:#eef2ff"
    sprintBadgeClass = (sprint) => "badge small fw-bold " + (sprint.state === "in_progress" ? "text-success" : "text-primary")
    sprintIconClass  = (sprint) => "fa me-1 " + (sprint.state === "in_progress" ? "fa-bolt" : "fa-calendar")

    // ── Responsible selector (scrum_poker pattern) ─────────────────────

    _calcDropdownPos() {
        const el = this.selectWrapRef.el;
        if (!el) return;
        const rect = el.getBoundingClientRect();
        this.state.dropdownTop   = rect.bottom + 4;
        this.state.dropdownLeft  = rect.left;
        this.state.dropdownWidth = rect.width;
    }

    get dropdownStyle() {
        return `position:fixed;top:${this.state.dropdownTop}px;left:${this.state.dropdownLeft}px;width:${this.state.dropdownWidth}px;z-index:9999`;
    }

    get filteredUsers() {
        const q = this.state.userSearch.trim().toLowerCase();
        if (!q) return this.state.allUsers.slice(0, 8);
        return this.state.allUsers.filter(u => u.name.toLowerCase().includes(q));
    }

    get dropdownHint() {
        if (!this.state.userSearch.trim() && this.state.allUsers.length > 8) {
            return `Mostrando 8 de ${this.state.allUsers.length}. Escribe para filtrar.`;
        }
        return null;
    }

    get selectedResponsibles() {
        return this.state.allUsers.filter(u => this.state.responsibleIds.includes(u.id));
    }

    isResponsibleSelected = (userId) => this.state.responsibleIds.includes(userId)

    onResponsibleSearchFocus = () => {
        clearTimeout(this._closeTimer);
        this._calcDropdownPos();
        this.state.dropdownOpen = true;
    }

    onResponsibleSearchBlur = () => {
        this._closeTimer = setTimeout(() => {
            this.state.dropdownOpen = false;
        }, 200);
    }

    onResponsibleSearchInput = (ev) => {
        this.state.userSearch = ev.target.value;
        this._calcDropdownPos();
        this.state.dropdownOpen = true;
    }

    onToggleResponsible = (ev) => {
        const userId = parseInt(ev.currentTarget.dataset.userId);
        const idx = this.state.responsibleIds.indexOf(userId);
        if (idx !== -1) {
            this.state.responsibleIds.splice(idx, 1);
        } else {
            this.state.responsibleIds.push(userId);
        }
        clearTimeout(this._closeTimer);
        this.searchRef.el?.focus();
    }

    removeResponsible = (ev) => {
        const userId = parseInt(ev.currentTarget.dataset.userId);
        const idx = this.state.responsibleIds.indexOf(userId);
        if (idx !== -1) this.state.responsibleIds.splice(idx, 1);
    }

    focusResponsibleSearch = () => { this.searchRef.el?.focus(); }
}
