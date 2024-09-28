odoo.define('pos_vantiv_tripos_cloud.pos_vantiv_tripos_cloud', function (require) {
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
    var _payline = pos_models.Paymentline.prototype;

    pos_models.load_fields('account.journal','pos_vantiv_tripos_cloud_config_id');

    pos_models.PosModel = pos_models.PosModel.extend({
        getOnlineVantivPaymentJournals: function () {
            var self = this;
            var online_payment_journals = [];
            $.each(this.journals, function (i, val) {
                if (val.pos_vantiv_tripos_cloud_config_id) {
                    online_payment_journals.push({label:self.getCashRegisterByJournalID(val.id).journal_id[1], item:val.id, conf:val.pos_vantiv_tripos_cloud_config_id});
                }
            });

            return online_payment_journals;
        },
        getCashRegisterByJournalID: function (journal_id) {
            var cashregister_return;

            $.each(this.cashregisters, function (index, cashregister) {
                if (cashregister.journal_id[0] === journal_id) {
                    cashregister_return = cashregister;
                }
            });

            return cashregister_return;
        },

    });

    pos_models.Paymentline = pos_models.Paymentline.extend({
        export_as_JSON: function () {
            var json = _payline.export_as_JSON.call(this);
            json.paid = this.paid;
            json.vantiv_swipe_pending = this.vantiv_swipe_pending;
            return json;
        },

        init_from_JSON: function (json) {
            _payline.init_from_JSON.apply(this, arguments);
            this.paid = json.paid;
            this.vantiv_swipe_pending = json.vantiv_swipe_pending;
        },
    });

    var PaymentTransactionPopupWidget = PopupWidget.extend({
        template: 'PaymentTransactionPopupWidget',
        show: function (options) {
            var self = this;
            this._super(options);
            options.transaction.then(function (data) {
                if (data.auto_close) {
                    setTimeout(function () {
                        self.gui.close_popup();
                    }, 2000);
                } else {
                    self.close();
                    // self.$el.find('.popup').append('<div class="footer"><div class="button cancel">Ok</div></div>');

                }

                self.$el.find('p.body').html(data.message);
            }).progress(function (data) {
                self.$el.find('p.body').html(data.message);
            });
        }
    });

    gui.define_popup({name:'payment-transaction', widget: PaymentTransactionPopupWidget});

    // On all screens, if a card is swipped, return a popup error.
    ScreenWidget.include({
        credit_error_action: function () {
            this.gui.show_popup('error-barcode',_t('Go to payment screen to use cards'));
        },

        show: function () {
            this._super();
            if(this.pos.getOnlineVantivPaymentJournals().length !== 0) {
                this.pos.barcode_reader.set_action_callback('credit', _.bind(this.credit_error_action, this));
            }
        }
    });

    PaymentScreenWidget.include({
        server_timeout_in_ms: 95000,
        server_retries: 3,

        _get_swipe_pending_line: function () {
                var i = 0;
                var lines = this.pos.get_order().get_paymentlines();

                for (i = 0; i < lines.length; i++) {
                    if (lines[i].vantiv_swipe_pending) {
                        return lines[i];
                    }
                }

                return 0;
        },

        retry_vantiv_transaction: function (def, response, retry_nr, can_connect_to_server, callback, args) {
            var self = this;
            var message = "";

            if (retry_nr < self.server_retries) {
                if (response) {
                    message = "Retry #" + (retry_nr + 1) + "...<br/><br/>" + response.message;
                } else {
                    message = "Retry #" + (retry_nr + 1) + "...";
                }
                def.notify({
                    message: message,
                    auto_close: false
                });

                setTimeout(function () {
                    callback.apply(self, args);
                }, 1000);
            } else {
                if (response) {
                    message = "Error " + response.error + "<br/>" + response.message;
                } else {
                    if (can_connect_to_server) {
                        message = _t("No response from Vantiv (Vantiv down?)");
                    } else {
                        message = _t("No response from server (connected to network?)");
                    }
                }
                def.resolve({
                    message: message,
                    auto_close: false
                });
            }
        },

        credit_code_transaction: function (parsed_result, old_deferred, retry_nr) {
            var order = this.pos.get_order();
            if (order.get_due(order.selected_paymentline) < 0) {
                this.gui.show_popup('error',{
                    'title': _t('Refunds not supported'),
                    'body':  _t('Credit card refunds are not supported. Instead select your credit card payment method, click \'Validate\' and refund the original charge manually through the Vantiv backend.'),
                });
                return;
            }

            if(this.pos.getOnlineVantivPaymentJournals().length === 0) {
                return;
            }

            var self = this;
            var swipe_pending_line = self._get_swipe_pending_line();
            var purchase_amount = 0;

            if (swipe_pending_line) {
                purchase_amount = swipe_pending_line.get_amount();
            } else {
                purchase_amount = self.pos.get_order().get_due();
            }

            console.log('parsed_result', self.pos.config);
            console.log('Order ', order);

            var transaction = {
                'order_name': order.name,
                'lane_id': self.pos.config.lane_id[0],
                'amount_total': purchase_amount,
                'transaction_type'  : 'Credit',
                'transaction_code'  : 'Sale',
                'invoice_no'        : self.pos.get_order().uid.replace(/-/g,''),
                'journal_id'        : parsed_result.journal_id,
            };

            var def = old_deferred || new $.Deferred();
            retry_nr = retry_nr || 0;

            // show the transaction popup.
            // the transaction deferred is used to update transaction status
            // if we have a previous deferred it indcaites that this is a retry
            if (! old_deferred) {
                self.gui.show_popup('payment-transaction', {
                    transaction: def
                });
                def.notify({
                    message: _t('Handling transaction...'),
                    auto_close: false
                });
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
                            message: _t("Card is gift only card but the configuration does not allow for gift transactions."),
                            auto_close: false
                        });
                        return;
                    }
                    if (data['statusCode'] === "Failed") {
                        def.resolve({
                            message: _t("Credit card has been failed."),
                            auto_close: false
                        });
                        return;
                    }
                    if (data['statusCode'] === "PinPadError") {
                        def.resolve({
                             message: _t("Transaction Failed. Please re-attempt the transaction. Customer has not been charged."),
                             auto_close: false
                        });
                        return;
                    }
                    if (data['statusCode'] === "Cancelled") {
                        def.resolve({
                            message: _t("The request has been canceled."),
                            auto_close: false
                        });
                        return;
                    }
                    if (data['statusCode'] === "Declined") {
                        def.resolve({
                            message: _t("Credit card has been declined."),
                            auto_close: false
                        });
                        return;
                    }
                    if (data === "timeout") {
                        self.retry_vantiv_transaction(def, null, retry_nr, true, self.credit_code_transaction, [parsed_result, def, retry_nr + 1]);
                        return;
                    }
                    if (data === "not setup") {
                        def.resolve({
                            message: _t("Please setup lane in your POS."),
                            auto_close: false
                        });
                        return;
                    }

                    if (data === "internal error") {
                        def.resolve({
                            message: _t("Odoo error while processing transaction."),
                            auto_close: false
                        });
                        return;
                    }

                }).fail(function (type, error) {
                    self.retry_vantiv_transaction(def, null, retry_nr, false, self.credit_code_transaction, [parsed_result, def, retry_nr + 1]);
                });
        },

        credit_code_cancel: function () {
            return;
        },

        credit_code_action: function (parsed_result) {
            var self = this;
            var online_payment_journals = this.pos.getOnlineVantivPaymentJournals();

            if (online_payment_journals.length === 1) {
                parsed_result.journal_id = online_payment_journals[0].item;
                self.credit_code_transaction(parsed_result);
            } else { // this is for supporting another payment system like mercury
                this.gui.show_popup('selection',{
                    title:   'Pay ' + this.pos.get_order().get_due().toFixed(2) + ' with : ',
                    list:    online_payment_journals,
                    confirm: function (item) {
                        parsed_result.journal_id = item;
                        self.credit_code_transaction(parsed_result);
                    },
                    cancel:  self.credit_code_cancel,
                });
            }
        },

//        click_delete_paymentline: function (cid) {
//            var lines = this.pos.get_order().get_paymentlines();
//            console.log('Click delete payment');
//            console.log(lines);
//
////            for (var i = 0; i < lines.length; i++) {
////                if (lines[i].cid === cid && lines[i].mercury_data) {
////                    this.do_reversal(lines[i], false);
////                    return;
////                }
////            }
//
//            this._super(cid);
//
//
//        },

        // make sure there is only one paymentline waiting for a swipe
        click_paymentmethods: function (id) {
            console.log('Click payment', this, id);
            var i;
            var order = this.pos.get_order();
            var cashregister = null;
            for (i = 0; i < this.pos.cashregisters.length; i++) {
                if (this.pos.cashregisters[i].journal_id[0] === id){
                    cashregister = this.pos.cashregisters[i];
                    console.log('tfind', this.$el.find('.pay').addClass('pay_highlight'));
                    break;
                }
            }

            if (cashregister.journal.pos_vantiv_tripos_cloud_config_id) {
                var already_swipe_pending = false;
                var lines = order.get_paymentlines();

                for (i = 0; i < lines.length; i++) {
                    if (lines[i].vantiv_swipe_pending ){
                        console.log(this);
                    }
                    if (lines[i].cashregister.journal.pos_vantiv_tripos_cloud_config_id && lines[i].vantiv_swipe_pending) {
                        already_swipe_pending = true;
                    }
                }

                if (already_swipe_pending) {
                    this.gui.show_popup('error',{
                        'title': _t('Error'),
                        'body':  _t('One credit card swipe already pending.'),
                    });
                } else {
                    this._super(id);
                    if (order.get_due(order.selected_paymentline) > 0) {
                        order.selected_paymentline.vantiv_swipe_pending = true;
                        this.render_paymentlines();
                        order.trigger('change', order); // needed so that export_to_JSON gets triggered
                    }
                }
            } else {
                this._super(id);
            }


        },

        renderElement: function(){
            var self = this;
            this._super();

            this.$('.pay').click(function(){
                self.credit_code_action(this);
            });

        },

        show: function () {
            this._super();
            if (this.pos.getOnlineVantivPaymentJournals().length !== 0) {
                console.log('Show online payments', this)
                this.pos.barcode_reader.set_action_callback('credit', _.bind(this.credit_code_action, this));
            }
        },

        validate_order: function (force_validation) {
            if (this.pos.get_order().is_paid() && ! this.invoicing) {
                var lines = this.pos.get_order().get_paymentlines();

                for (var i = 0; i < lines.length; i++) {
                    if (lines[i].vantiv_swipe_pending) {
                        this.pos.get_order().remove_paymentline(lines[i]);
                        this.render_paymentlines();
                    }
                }
            }
            this._super(force_validation);
        },
    });

    // models.load_models({
    //     model: 'pos_vantiv_tripos_cloud.lane',
    //     fields: ['id', 'name', 'lane_id', ],
    //     loaded: function (self, lanes) {
    //         self.lanes = lanes;
    //         self.lanes_by_id = {};
    //         _.each(lanes, function (lane) {
    //             self.lanes_by_id[lane.id] = lane;
    //         });
    //     },
    // });

    // models.Order = models.Order.extend({
    //     initialize: function (session, attributes) {
    //         _super_order.initialize.call(this, session, attributes);
    //         this.lane_id = 1;
    //     },
    //     set_lane: function (lane) {
    //         var self = this;
    //         self.lane_id = lane.id;
    //         this.trigger('change');
    //     },
    //     clone: function () {
    //         var order = _super_order.clone.call(this);
    //         order.lane_id = this.lane_id;
    //         return order;
    //     },
    //     export_as_JSON: function () {
    //         var json = _super_order.export_as_JSON.call(this);
    //         json.lane_id = this.lane_id;
    //         return json;
    //     },
    //     init_from_JSON: function (json) {
    //         _super_order.init_from_JSON.apply(this, arguments);
    //         this.lane_id = json.lane_id;
    //     },
    // });



    // var TriposLaneButton = screens.ActionButtonWidget.extend({
    //     template: 'TriposLaneButton',
    //     init: function (parent, options) {
    //         this._super(parent, options);

    //         this.pos.get('orders').bind('add remove change', function () {
    //             this.renderElement();
    //         }, this);

    //         this.pos.bind('change:selectedOrder', function () {
    //             this.renderElement();
    //         }, this);
    //     },
    //     button_click: function () {
    //         var self = this;

    //         var lanes = _.map(self.pos.lanes, function (lane) {
    //             return {
    //                 label: lane.name,
    //                 item: lane
    //             };
    //         });

    //         self.gui.show_popup('selection', {
    //             title: _t('Select lane'),
    //             list: lanes,
    //             confirm: function (lane) {
    //                 var order = self.pos.get_order();
    //                 order.set_lane(lane);
    //                 console.log("confirm order 2 ", order);
    //             },
    //             is_selected: function (lane) {
    //                 var order = self.pos.get_order();
    //                 console.log("is selected ", order);
    //                 return lane.id === order.lane_id;
    //             }
    //         });
    //     },
    //     get_current_lane_name: function () {
    //         var name = _t('Select Lane');
    //         var order = this.pos.get_order();

    //         if (order) {
    //             var lane = order.lane_id;

    //             if (lane) {
    //                 name = this.pos.lanes_by_id[lane].name;
    //             }
    //         }
    //         return name;
    //     },
    // });

    // screens.define_action_button({
    //     'name': 'selectLane',
    //     'widget': TriposLaneButton,
    // });

    // return {
    //     TriposLaneButton: TriposLaneButton,
    // };
});