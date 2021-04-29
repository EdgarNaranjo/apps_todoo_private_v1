odoo.define('pos_vantiv_refund.pos_vantiv_refund', function (require) {
    "use strict";

    var core = require('web.core');
    var screens = require('point_of_sale.screens');
    var gui = require('point_of_sale.gui');
    var pos_models = require('point_of_sale.models');
    var _db = require('point_of_sale.DB');
    var _rpc = require('web.rpc');
    var PopupWidget = require('point_of_sale.popups');
    var ScreenWidget = screens.ScreenWidget;
    var PaymentScreenWidget = screens.PaymentScreenWidget;
    var _t = core._t;

    PaymentScreenWidget.include({
        credit_code_transaction: function (parsed_result, old_deferred, retry_nr) {
            var order = this.pos.get_order();
            var self = this;

            var swipe_pending_line = self._get_swipe_pending_line();
            var purchase_amount = 0;

            if (swipe_pending_line) {
                purchase_amount = swipe_pending_line.get_amount();
            } else {
                purchase_amount = Math.abs(order.get_due(order.selected_paymentline));
            }

            var transaction = {
                'lane_id': self.pos.config.lane_id[0],
                'amount_total': purchase_amount,
                'transaction_type': 'Credit',
                'transaction_code': 'Refund',
                'invoice_no': self.pos.get_order().uid.replace(/-/g, ''),
                'journal_id': parsed_result.journal_id
            };

            var def = old_deferred || new $.Deferred();
            retry_nr = retry_nr || 0;


            if (this.pos.getOnlineVantivPaymentJournals().length === 0) {
                return;
            }

            // show the transaction popup.
            // the transaction deferred is used to update transaction status
            // if we have a previous deferred it indicates that this is a retry
            if (!old_deferred) {
                self.gui.show_popup('payment-transaction', {
                    transaction: def
                });
                def.notify({
                    message: _t('Handling transaction...'),
                });
            }

            if (order.get_due(order.selected_paymentline) < 0) {
                // this.gui.show_popup('error', {
                //     'title': _t('Refunds not supported'),
                //     'body': _t('Credit card refunds are not supported. Instead select your credit card payment method, click \'Validate\' and refund the original charge manually through the Vantiv backend.'),
                // });
                // return;
                _rpc.query({
                    model: 'pos_vantiv_tripos_cloud.transaction',
                    method: 'do_refund',
                    args: [transaction],
                }, {
                    timeout: self.server_timeout_in_ms,
                }).then(function (data) {
                    // if not receiving a response from Mercury, we should retry
                    if (data['statusCode'] === "Approved") {
                        // If the payment is approved, add a payment line
                        var order = self.pos.get_order();

                        if (swipe_pending_line) {
                            order.select_paymentline(swipe_pending_line);
                        } else {
                            order.add_paymentline(self.pos.getCashRegisterByJournalID(parsed_result.journal_id));
                        }

                        order.selected_paymentline.paid = true;
                        order.selected_paymentline.vantiv_swipe_pending = false;

                        self.order_changes();
                        self.reset_input();
                        self.render_paymentlines();
                        order.trigger('change', order); // needed so that export_to_JSON gets triggered

                        def.resolve({
                            message: _t("Transaction Successful"),
                            auto_close: true,
                        });
                    }
                    if (data['statusCode'] === "UnsupportedCard") {
                        def.resolve({
                            message: _t("Card is gift only card but the configuration does not allow for gift transactions.")
                        });
                        return;
                    }
                    if (data['statusCode'] === "Failed") {
                        def.resolve({
                            message: _t("Credit card has been failed.")
                        });
                        return;
                    }
                    if (data['statusCode'] === "PinPadError") {
                        def.resolve({
                            message: _t("Transaction Failed. Please re-attempt the transaction. Customer has not been charged.")
                        });
                        return;
                    }
                    if (data['statusCode'] === "Cancelled") {
                        def.resolve({
                            message: _t("The request has been canceled.")
                        });
                        return;
                    }
                    if (data['statusCode'] === "Declined") {
                        def.resolve({
                            message: _t("Credit card has been declined.")
                        });
                        return;
                    }
                    if (data === "timeout") {
                        self.retry_vantiv_transaction(def, null, retry_nr, true, self.credit_code_transaction, [parsed_result, def, retry_nr + 1]);
                        return;
                    }
                    if (data === "not setup") {
                        def.resolve({
                            message: _t("Please setup lane in your POS.")
                        });
                        return;
                    }

                    if (data === "internal error") {
                        def.resolve({
                            message: _t("Odoo error while processing transaction.")
                        });
                        return;
                    }

                }).fail(function (type, error) {
                    self.retry_vantiv_transaction(def, null, retry_nr, false, self.credit_code_transaction, [parsed_result, def, retry_nr + 1]);
                });
                return;
            }

            _rpc.query({
                model: 'pos_vantiv_tripos_cloud.transaction',
                method: 'do_transaction',
                args: [transaction],
            }, {
                timeout: self.server_timeout_in_ms,
            })
                .then(function (data) {
                    // if not receiving a response from Mercury, we should retry
                    if (data['statusCode'] === "Approved") {
                        // If the payment is approved, add a payment line
                        var order = self.pos.get_order();

                        if (swipe_pending_line) {
                            order.select_paymentline(swipe_pending_line);
                        } else {
                            order.add_paymentline(self.pos.getCashRegisterByJournalID(parsed_result.journal_id));
                        }

                        order.selected_paymentline.paid = true;
                        order.selected_paymentline.vantiv_swipe_pending = false;

                        self.order_changes();
                        self.reset_input();
                        self.render_paymentlines();
                        order.trigger('change', order); // needed so that export_to_JSON gets triggered

                        def.resolve({
                            message: _t("Transaction Successful"),
                            auto_close: true,
                        });
                    }
                    if (data['statusCode'] === "UnsupportedCard") {
                        def.resolve({
                            message: _t("Card is gift only card but the configuration does not allow for gift transactions.")
                        });
                        return;
                    }
                    if (data['statusCode'] === "Failed") {
                        def.resolve({
                            message: _t("Credit card has been failed.")
                        });
                        return;
                    }
                    if (data['statusCode'] === "PinPadError") {
                        def.resolve({
                            message: _t("Transaction Failed. Please re-attempt the transaction. Customer has not been charged.")
                        });
                        return;
                    }
                    if (data['statusCode'] === "Cancelled") {
                        def.resolve({
                            message: _t("The request has been canceled.")
                        });
                        return;
                    }
                    if (data['statusCode'] === "Declined") {
                        def.resolve({
                            message: _t("Credit card has been declined.")
                        });
                        return;
                    }
                    if (data === "timeout") {
                        self.retry_vantiv_transaction(def, null, retry_nr, true, self.credit_code_transaction, [parsed_result, def, retry_nr + 1]);
                        return;
                    }
                    if (data === "not setup") {
                        def.resolve({
                            message: _t("Please setup lane in your POS.")
                        });
                        return;
                    }

                    if (data === "internal error") {
                        def.resolve({
                            message: _t("Odoo error while processing transaction.")
                        });
                        return;
                    }

                }).fail(function (type, error) {
                self.retry_vantiv_transaction(def, null, retry_nr, false, self.credit_code_transaction, [parsed_result, def, retry_nr + 1]);
            });
        },
    });

});