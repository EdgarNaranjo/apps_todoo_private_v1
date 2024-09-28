/** @odoo-module */

import { _t } from "@web/core/l10n/translation";
import { PaymentInterface } from "@point_of_sale/app/payment/payment_interface";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { sprintf } from "@web/core/utils/strings";
const { DateTime } = luxon;

export class PaymentVantivTriposCloud extends PaymentInterface {
    setup() {
        super.setup(...arguments);
        console.log("PaymentVantivTriposCloud");
        this.paymentLineResolvers = {};
    }

    send_payment_request(cid) {
        super.send_payment_request(cid);
        return this._tripos_vantiv_pay(cid);
    }
    send_payment_cancel(order, cid) {
        super.send_payment_cancel(order, cid);
        return this._tripos_vantiv_cancel();
    }

    set_line_id(id) {
        console.log("set line");
        this.lineId = id;
    }

    pending_tripos_vantiv_line() {
        return this.pos.getPendingPaymentLine("tripos_vantiv");
    }

    _handle_odoo_connection_failure(data = {}) {
        // handle timeout
        var line = this.pending_tripos_vantiv_line();
        if (line) {
            line.set_payment_status("retry");
        }
        this._show_error(
            _t(
                "Could not connect to the Odoo server, please check your internet connection and try again."
            )
        );

        return Promise.reject(data); // prevent subsequent onFullFilled's from being called
    }

    _call_tripos_vantiv(data, operation=false) {
        // FIXME POSREF TIMEOUT 10000
        return this.env.services.orm.silent
            .call("pos.payment.method", "proxy_tripos_vantiv_request", [
                [this.payment_method.id],
                data,
                operation,
            ])
            .catch(this._handle_odoo_connection_failure.bind(this));
    }

    _tripos_vantiv_pay_data() {
        const order = this.pos.get_order();
        const config = this.pos.config;
        const line = order.selected_paymentline;

        const data = {
            'order_name': order.name,
            'lane_id': config.lane_id[0],
            'amount_total': line.amount,
            'transaction_type'  : 'Credit',
            'transaction_code'  : 'Sale',
            'invoice_no'        : self.pos.get_order().uid.replace(/-/g,''),
        };

        return data;
    }

    _tripos_vantiv_pay(cid) {
        const order = this.pos.get_order();

        if (order.selected_paymentline.amount < 0) {
            this._show_error(_t("Cannot process transactions with negative amount."));
            return Promise.resolve();
        }

        const data = this._tripos_vantiv_pay_data();
        return this._call_tripos_vantiv(data, "pay").then((data) => {
            return this._tripos_vantiv_handle_response(data);
        });
    }

    _tripos_vantiv_cancel(ignore_error) {
        var config = this.pos.config;
        var data = {
        };

        return this._call_tripos_vantiv(data, "cancel").then((data) => {
            // Only valid response is a 200 OK HTTP response which is
            // represented by true.
            if (!ignore_error && data !== true) {
                this._show_error(
                    _t(
                        "Cancelling the payment failed. Please cancel it manually on the payment terminal."
                    )
                );
            }
        });
    }

    /**
     * This method handles the response that comes from Adyen
     * when we first make a request to pay.
     */
    _tripos_vantiv_handle_response(response) {
        var line = this.pending_tripos_vantiv_line();
        status_code = response['statusCode']

        if (status_code === "UnsupportedCard") {
            this._show_error(_t("Card is gift only card but the configuration does not allow for gift transactions."));
            line.set_payment_status("waitingCard");
            return this.waitForPaymentConfirmation();
        }
        else if (status_code === "Failed") {
            this._show_error(_t("Credit card has been failed."));
            line.set_payment_status("waitingCard");
            return this.waitForPaymentConfirmation();
        }
        else if (status_code === "PinPadError") {
            this._show_error(_t("Transaction Failed. Please re-attempt the transaction. Customer has not been charged."));
            line.set_payment_status("waitingCard");
            return this.waitForPaymentConfirmation();
        }
        else if (status_code === "Declined") {
            this._show_error(_t("Credit card has been declined."));
            line.set_payment_status("waitingCard");
            return this.waitForPaymentConfirmation();
        }
        else if (status_code === "timeout") {
            this._show_error(_t("Credit card has been declined."));
            line.set_payment_status("waitingCard");
            return false;
        }
        else if (status_code === "not setup") {
            this._show_error(_t("Please setup lane in your POS."));
            line.set_payment_status("waitingCard");
            return this.waitForPaymentConfirmation();
        }
        else if (status_code === "internal error") {
            this._show_error(_t("Odoo error while processing transaction."));
            line.set_payment_status("waitingCard");
            return this.waitForPaymentConfirmation();
        } else {
            line.set_payment_status("force");
            return false;
        }

    }
    waitForPaymentConfirmation() {
        return new Promise((resolve) => {
            this.paymentLineResolvers[this.pending_tripos_vantiv_line().cid] = resolve;
        });
    }

    _show_error(msg, title) {
        if (!title) {
            title = _t("Vantiv Tripos Cloud Error");
        }
        this.env.services.popup.add(ErrorPopup, {
            title: title,
            body: msg,
        });
    }
}
