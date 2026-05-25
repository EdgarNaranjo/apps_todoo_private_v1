/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";
import { SprintBoardList } from "../SprintBoardList/SprintBoardList";
import { SprintBoardDashboard } from "../SprintBoardDashboard/SprintBoardDashboard";

export class SprintBoardAction extends Component {
    static template = "sprint_board_project.SprintBoardAction";
    static components = { SprintBoardList, SprintBoardDashboard };
    static props = ["action", "actionStack?", "actionId?", "className?"];

    setup() {
        this.rpc = useService("rpc");
        this.state = useState({
            view: "loading",   // "loading" | "list" | "dashboard"
            boardId: null,
        });
        onWillStart(async () => {
            try {
                const r = await this.rpc("/sprint-board/check-today", {});
                if (r.no_board) {
                    this.state.view = "list";
                } else {
                    this.state.boardId = r.board_id;
                    this.state.view = "dashboard";
                }
            } catch (e) {
                console.error("SprintBoardAction: check-today failed", e);
                this.state.view = "list";
            }
        });
    }

    openBoard  = (boardId) => {
        this.state.boardId = boardId;
        this.state.view = "dashboard";
    }

    backToList = () => {
        this.state.boardId = null;
        this.state.view = "list";
    }
}

registry.category("actions").add("sprint_board_project.SprintBoardAction", SprintBoardAction);
