/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, useRef, onMounted, onWillUnmount, markup } from "@odoo/owl";

const STORAGE_KEY = "todoo_global_search_history";
const MAX_HISTORY = 5;
const DEBOUNCE_DELAY = 300;
const RESULTS_PER_MODEL = 5;

// Font Awesome icon mapping per model
const MODEL_ICONS = {
    'sale.order':               'fa-shopping-cart',
    'purchase.order':           'fa-shopping-basket',
    'account.move':             'fa-file-text-o',
    'account.payment':          'fa-money',
    'res.partner':              'fa-address-book-o',
    'product.template':         'fa-cube',
    'product.product':          'fa-cubes',
    'stock.picking':            'fa-truck',
    'stock.quant':              'fa-archive',
    'mrp.production':           'fa-cogs',
    'project.project':          'fa-folder-open-o',
    'project.task':             'fa-tasks',
    'hr.employee':              'fa-user-circle-o',
    'crm.lead':                 'fa-phone',
    'helpdesk.ticket':          'fa-ticket',
    'res.users':                'fa-user-o',
    'fleet.vehicle':            'fa-car',
    'account.analytic.account': 'fa-bar-chart',
    'maintenance.request':      'fa-wrench',
    'stock.lot':                'fa-barcode',
};

function getModelIcon(model) {
    return MODEL_ICONS[model] || 'fa-file-o';
}

function getHistory() {
    try {
        return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
    } catch {
        return [];
    }
}

function pushHistory(term) {
    try {
        const prev = getHistory().filter(s => s !== term);
        localStorage.setItem(STORAGE_KEY, JSON.stringify([term, ...prev].slice(0, MAX_HISTORY)));
    } catch { /* storage not available */ }
}

class SystrayIcon extends Component {
    setup() {
        this.rpc = useService("rpc");
        this.action = useService("action");
        this.state = useState({
            inputSearch: "",
            results: [],
            history: [],
            isLoading: false,
            hasError: false,
            selectedIndex: -1,
            open: false,
            isExpanded: false,
        });
        this.inputRef = useRef("inputSearch");
        this._debounceTimer = null;
        this._boundGlobalKeyDown = this._globalKeyDown.bind(this);

        onMounted(() => {
            document.addEventListener("keydown", this._boundGlobalKeyDown);
        });
        onWillUnmount(() => {
            document.removeEventListener("keydown", this._boundGlobalKeyDown);
        });
    }

    // Ctrl+K (or Cmd+K on Mac) opens search from anywhere
    _globalKeyDown(ev) {
        if ((ev.ctrlKey || ev.metaKey) && ev.key === 'k') {
            ev.preventDefault();
            ev.stopPropagation();
            this.expandSearch();
        }
    }

    expandSearch() {
        this.state.isExpanded = true;
        this.state.history = getHistory();
        this.state.open = true;
        // Esperar al siguiente ciclo de render para que el input exista en el DOM
        setTimeout(() => this.inputRef.el?.focus(), 0);
    }

    get flatResults() {
        return this.state.results.flatMap(g =>
            g.records.map(r => ({ model: g.model, id: r.id, modelName: g.modelNameDisplay }))
        );
    }

    get showHistory() {
        return this.state.open &&
               !this.state.isLoading &&
               !this.state.hasError &&
               this.state.inputSearch.length < 3 &&
               this.state.history.length > 0 &&
               this.state.results.length === 0;
    }

    get showNoResults() {
        return this.state.open &&
               !this.state.isLoading &&
               !this.state.hasError &&
               this.state.inputSearch.length >= 3 &&
               this.state.results.length === 0;
    }

    get showDropdown() {
        return this.state.open && (
            this.state.isLoading ||
            this.state.hasError ||
            this.state.results.length > 0 ||
            this.showHistory ||
            this.showNoResults
        );
    }

    onFocus() {
        this.state.history = getHistory();
        this.state.open = true;
        if (this.state.inputSearch.length >= 3) {
            this._triggerSearch(this.state.inputSearch);
        }
    }

    onBlur() {
        setTimeout(() => {
            // Solo cierra si el input realmente perdió el foco (no por un doAction rápido)
            if (document.activeElement !== this.inputRef.el) {
                this.state.open = false;
                this.state.selectedIndex = -1;
            }
        }, 200);
    }

    onInput() {
        // state.inputSearch is already updated by t-model
        const term = this.state.inputSearch;
        this.state.selectedIndex = -1;
        clearTimeout(this._debounceTimer);

        if (term.length < 3) {
            this.state.results = [];
            this.state.isLoading = false;
            this.state.hasError = false;
            return;
        }

        this.state.isLoading = true;
        this._debounceTimer = setTimeout(() => this._search(term), DEBOUNCE_DELAY);
    }

    onKeyDown(ev) {
        const flat = this.flatResults;

        if (ev.key === 'Escape') {
            this.clear();
            this.inputRef.el?.blur();
            return;
        }
        if (!flat.length) return;

        if (ev.key === 'ArrowDown') {
            ev.preventDefault();
            this.state.selectedIndex = Math.min(this.state.selectedIndex + 1, flat.length - 1);
        } else if (ev.key === 'ArrowUp') {
            ev.preventDefault();
            this.state.selectedIndex = Math.max(this.state.selectedIndex - 1, -1);
        } else if (ev.key === 'Enter') {
            ev.preventDefault();
            const idx = this.state.selectedIndex >= 0 ? this.state.selectedIndex : 0;
            const item = flat[idx];
            if (item) this.openRecord(item.model, item.id);
        }
    }

    _triggerSearch(term) {
        clearTimeout(this._debounceTimer);
        this._search(term);
    }

    async _search(term) {
        this.state.isLoading = true;
        this.state.hasError = false;
        try {
            const res = await this.rpc("/web/dataset/call_kw/res.users/search_terms", {
                model: 'res.users',
                method: 'search_terms',
                args: [term],
                kwargs: {},
            });
            this.state.results = res.map((item, idx) => ({
                id: idx,
                modelNameDisplay: item.name,
                model: item.model,
                icon: getModelIcon(item.model),
                hasMore: item.has_more,
                records: item.records.map(r => ({ id: r[0], title: r[1] })),
            }));
            if (res.length > 0) pushHistory(term);
        } catch {
            this.state.hasError = true;
            this.state.results = [];
        } finally {
            this.state.isLoading = false;
        }
    }

    searchFromHistory(term) {
        this.state.inputSearch = term;
        this.state.open = true;
        this._triggerSearch(term);
    }

    isSelected(groupIdx, recIdx) {
        let offset = 0;
        for (let i = 0; i < groupIdx; i++) offset += this.state.results[i].records.length;
        return (offset + recIdx) === this.state.selectedIndex;
    }

    openRecord(model, id) {
        this.action.doAction({
            type: 'ir.actions.act_window',
            res_model: model,
            res_id: id,
            views: [[false, 'form']],
        });
        // Cierra el dropdown pero conserva el término y resultados
        // para que al volver a enfocar el input aparezcan de inmediato
        this.state.open = false;
        this.state.selectedIndex = -1;
    }

    seeMore(model, modelName) {
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: modelName,
            res_model: model,
            view_mode: 'list,form',
            views: [[false, 'list'], [false, 'form']],
            context: { search_default_name: this.state.inputSearch },
        });
        this.clear();
    }

    removeHistory(term) {
        try {
            const updated = getHistory().filter(s => s !== term);
            localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
            this.state.history = updated;
        } catch { /* noop */ }
    }

    clearHistory() {
        try { localStorage.removeItem(STORAGE_KEY); } catch { /* noop */ }
        this.state.history = [];
    }

    // Resalta el término buscado dentro del texto del resultado
    highlight(text, term) {
        if (!term || term.length < 3) return text;
        const safeText = text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
        const safeTerm = term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        return markup(safeText.replace(
            new RegExp(`(${safeTerm})`, 'gi'),
            '<mark class="o_todoo_hl">$1</mark>'
        ));
    }

    clear() {
        clearTimeout(this._debounceTimer);
        this.state.inputSearch = "";
        this.state.results = [];
        this.state.isLoading = false;
        this.state.hasError = false;
        this.state.selectedIndex = -1;
        this.state.open = false;
    }
}

SystrayIcon.template = "systray_icon";
export const systrayItem = { Component: SystrayIcon };
registry.category("systray").add("SystrayIcon", systrayItem, { sequence: 999 });

