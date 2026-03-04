/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component } from "@odoo/owl";

export class DooRulesSystray extends Component {
    setup() {
        this.userService = useService("user");
        this.actionService = useService("action");
        this.orm = useService("orm");
    }

    /**
     * Codifica un string a Base64 URL-safe (UTF-8 compatible)
     */
    _toUrlSafeBase64(str) {
        try {
            const utf8Bytes = encodeURIComponent(str).replace(/%([0-9A-F]{2})/g, (match, p1) => {
                return String.fromCharCode('0x' + p1);
            });
            return window.btoa(utf8Bytes).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
        } catch (e) {
            return "";
        }
    }

    /**
     * Filtra y prioriza los campos más relevantes para reglas de negocio
     */
    _getFilteredFields(fieldsInfo) {
        const allowedTypes = ['char', 'integer', 'float', 'boolean', 'selection', 'monetary', 'date', 'datetime', 'many2one'];
        const blacklistPrefixes = ['activity_', 'message_', 'website_', 'access_', 'my_activity_'];
        const blacklistExact = ['create_uid', 'write_uid', 'create_date', 'write_date', '__last_update', 'access_token', 'access_url'];
        const priorityFields = ['state', 'amount_total', 'partner_id', 'amount_untaxed', 'date_order', 'name', 'user_id', 'company_id'];

        let filteredFields = [];
        for (const [name, field] of Object.entries(fieldsInfo)) {
            if (!allowedTypes.includes(field.type)) continue;
            if (blacklistExact.includes(name)) continue;
            if (blacklistPrefixes.some(prefix => name.startsWith(prefix))) continue;

            filteredFields.push({
                name: name,
                type: field.type,
                label: field.string || name,
                priority: priorityFields.includes(name) ? 1 : 10
            });
        }

        return filteredFields
            .sort((a, b) => a.priority - b.priority || a.name.localeCompare(b.name))
            .slice(0, 35)
            .map(({ name, type, label }) => ({ name, type, label }));
    }

    async _onClick() {
        const userName = this.userService.name;
        const controller = this.actionService.currentController;
        
        let odooContext = {
            model: "unknown",
            model_description: "General",
            task: "Asistencia general",
            fields: [],
            preferred_output: "rule_logic"
        };

        if (controller && controller.props) {
            const resModel = controller.props.resModel || controller.props.model;
            
            if (resModel && resModel !== "unknown") {
                try {
                    const modelInfo = await this.orm.searchRead('ir.model', [['model', '=', resModel]], ['name'], { limit: 1 });
                    const friendlyName = (modelInfo.length > 0) ? modelInfo[0].name : (controller.title || resModel);
                    const fieldsInfo = await this.orm.call(resModel, 'fields_get', [], { attributes: ['type', 'string'] });

                    if (fieldsInfo) {
                        odooContext = {
                            model: resModel,
                            model_description: friendlyName,
                            task: `Configurar reglas para ${friendlyName}`,
                            fields: this._getFilteredFields(fieldsInfo),
                            preferred_output: "rule_logic"
                        };
                    }
                } catch (error) {
                    // Fallback silencioso en producción
                    odooContext.model = resModel;
                    odooContext.model_description = controller.title || resModel;
                }
            }
        }

        const ctxJson = JSON.stringify(odooContext);
        const ctxB64 = this._toUrlSafeBase64(ctxJson);
        const url = `https://ia.doorules.com/?external_user=${encodeURIComponent(userName)}&odoo_context=${ctxB64}`;

        window.open(url, "_blank");
    }
}

DooRulesSystray.template = "connector_ia_doorules.DooRulesSystray";
DooRulesSystray.props = {};

export const systrayItem = {
    Component: DooRulesSystray,
};

registry.category("systray").add("DooRulesSystray", systrayItem, { sequence: 1000 });
