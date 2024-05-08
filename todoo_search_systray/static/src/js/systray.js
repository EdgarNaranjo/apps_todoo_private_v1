/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState } from "@odoo/owl";
import {Dropdown} from '@web/core/dropdown/dropdown';
import {DropdownItem} from '@web/core/dropdown/dropdown_item';

class SystrayIcon extends Component {
     state = useState({ iconSearch: false, inputSearch: "" , results:[] });
     setup() {
         this.rpc = useService("rpc");
         super.setup(...arguments);
     }

     async inputFocus(){
         if (this.state.inputSearch.length < 3) {
            return;
         }
         await this.search(this.state.inputSearch)
     }

    async _updateInputValue(event) {
        const search_term = event.target.value;
        this.state.inputSearch = search_term
        if (search_term.length < 3) {
            this.state.iconSearch = false;
            return;
        }
        this.search(search_term)
     }

    async search(search_term){
         this.state.iconSearch = true;
         const res = await this.rpc("/web/dataset/call_kw/res.users/search_terms",{
            model: 'res.users',
            method: 'search_terms',
            args: [search_term],
            kwargs: {},
         });
         this.state.results = res.map((resItem, index) => {
            return {
                id: index,
                modelNameDisplay: resItem.name,
                model: resItem.model,
                records: resItem.records.map(item => ({
                    id: item[0],
                    title: item[1]
                }))
           }
         })
    }
    clear(){
        this.state.iconSearch = false;
        this.state.inputSearch = ""
        this.state.results = []
    }

    _hideModal(){
        this.state.results = []
    }
}

SystrayIcon.template = "systray_icon";
SystrayIcon.components = {Dropdown, DropdownItem };
export const systrayItem = { Component: SystrayIcon,};
registry.category("systray").add("SystrayIcon", systrayItem, { sequence: 999});
