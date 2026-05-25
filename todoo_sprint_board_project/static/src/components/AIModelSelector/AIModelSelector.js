/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { useService } from "@web/core/utils/hooks";

const AI_MODELS = {
    openai:    ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
    anthropic: ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "claude-3-opus-20240229"],
    gemini:    ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"],
    mistral:   ["mistral-large-latest", "mistral-small-latest", "codestral-latest"],
    ollama:    ["qwen2.5:3b", "llama3.2", "mistral", "codellama"],
    custom:    [],
};

export class AIModelSelectorField extends Component {
    static template = "sprint_board_project.AIModelSelectorField";
    static props = {
        ...standardFieldProps,
        // El campo proveedor — viene via options en la vista
        providerFieldName: { type: String, optional: true },
    };

    setup() {
        this.state = useState({ customValue: "" });
        onWillStart(() => {
            this.state.customValue = this.props.record.data[this.props.name] || "";
        });
    }

    get provider() {
        const fieldName = this.props.providerFieldName || "sprint_board_ai_provider";
        return this.props.record.data[fieldName] || "openai";
    }

    get suggestions() {
        return AI_MODELS[this.provider] || [];
    }

    get isCustom() {
        return this.provider === "custom" || this.provider === "ollama";
    }

    get currentValue() {
        return this.props.record.data[this.props.name] || "";
    }

    selectChip(model) {
        this.props.record.update({ [this.props.name]: model });
    }

    onCustomInput(ev) {
        this.props.record.update({ [this.props.name]: ev.target.value });
    }
}

registry.category("fields").add("ai_model_selector", AIModelSelectorField);
