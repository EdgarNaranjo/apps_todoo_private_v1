/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { register_payment_method } from "@point_of_sale/app/store/pos_store";
import { Payment } from "@point_of_sale/app/store/models";
import { PaymentVantivTriposCloud } from "@pos_vantiv_tripos_cloud/js/app/payment";

register_payment_method("tripos_vantiv", PaymentVantivTriposCloud);


patch(Payment.prototype, {
    setup() {
        super.setup(...arguments);
        this.laneId = this.pos.config.lane_id[0] || null;
    },
    //@override
    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        if (json) {
            json.lane_id = this.laneId;
        }
        return json;
    },
    //@override
    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
        this.laneId = json.lane_id;
    },
    setLaneId(id) {
        this.laneId = id;
    },
});
