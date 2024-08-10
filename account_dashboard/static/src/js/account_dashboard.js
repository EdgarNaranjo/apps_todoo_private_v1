odoo.define("account_dashboard.account_dashboard_definition", function (require) {
    "use strict";

    const AbstractAction = require('web.AbstractAction');
    const core = require("web.core");
    const session = require("web.session");
    const field_utils = require("web.field_utils")
    const QWeb = core.qweb;
    const monetary = function (value) {
        return field_utils.format.monetary(value, {}, { currency_id: session.currency_id });
    };

    const AccountDashboardAction = AbstractAction.extend({
        contentTemplate: 'account_dashboard.dashboard',
        events: {
            'click button.ad_update_dashboard': function (e) {
                const self = this;
                this._rpc({
                    model: 'account.year',
                    method: 'run_update_data'
                }).then(function () {
                    self.start();
                });
            },
            'mouseover button.ad_update_dashboard': function (e) {
                $('.ad_update_dashboard').css({ 'opacity': 1 });
            },
            'mouseout button.ad_update_dashboard': function (e) {
                $('.ad_update_dashboard').css({ 'opacity': 0.5 });
            }
        },
        start: function () {
            const def = this._super.apply(this, arguments);
            const self = this;

            this._rpc({
                    model: 'account.year',
                    method: 'header_data',
                    args: ['sale', 'day']
            }).then(function (data) {
                data.actual_amount = monetary(data.actual_amount);
                data.past_amount = monetary(data.past_amount);
                $('#day_sales').html(QWeb.render('account_dashboard_day_sales_template', data));
            });

            this._rpc({
                model: 'account.year',
                method: 'header_data',
                args: ['sale', 'month']
            }).then(function (data) {
                data.actual_amount = monetary(data.actual_amount);
                data.past_amount = monetary(data.past_amount);
                $('#month_sales').html(QWeb.render('account_dashboard_month_sales_template', data));
            });
            this._rpc({
                model: 'account.year',
                method: 'header_data',
                args: ['purchase', 'day']
            }).then(function (data) {
                data.actual_amount = monetary(data.actual_amount);
                data.past_amount = monetary(data.past_amount);
                $('#day_purchases').html(QWeb.render('account_dashboard_day_purchases_template', data));
            });
            this._rpc({
                model: 'account.year',
                method: 'header_data',
                args: ['purchase', 'month']
            }).then(function (data) {
                data.actual_amount = monetary(data.actual_amount);
                data.past_amount = monetary(data.past_amount);
                $('#month_purchases').html(QWeb.render('account_dashboard_month_purchases_template', data));
            });

            // Rendering body charts
            this._rpc({
                model: 'account.year',
                method: 'chart_data',
                args: ['sales']
            }).then(function (data) {
                self.draw_chart_account('Sales', 'year_sales_chart', data, ['#1E9FF2', '#91E8E1', '#7CB5EC']);
            });
            this._rpc({
                model: 'account.year',
                method: 'chart_data',
                args: ['purchases']
            }).then(function (data) {
                self.draw_chart_account('Purchase', 'year_purchases_chart', data, ['#28D094', '#90ed7d', '#2b908f']);
            });
            this._rpc({
                model: 'account.year',
                method: 'chart_budget',
                args: []
            }).then(function (data) {
                self.draw_chart_budget(data);
            });

            // Rendering footer
            this._rpc({
                model: 'account.year',
                method: 'footer_data',
                args: ['sales']
            }).then(function (data) {
                data.actual_amount = monetary(data.actual_amount);
                data.past_amount = monetary(data.past_amount);
                $('#total_sales').html(QWeb.render('account_dashboard_total_sales_template', data));
            });
            this._rpc({
                model: 'account.year',
                method: 'footer_data',
                args: ['purchases']
            }).then(function (data) {
                data.actual_amount = monetary(data.actual_amount);
                data.past_amount = monetary(data.past_amount);
                $('#total_purchases').html(QWeb.render('account_dashboard_total_purchases_template', data));
            });
            this._rpc({
                model: 'account.year',
                method: 'footer_data',
                args: ['sales', false]
            }).then(function (data) {
                data.actual_amount = monetary(data.actual_amount);
                $('#pending_sales').html(QWeb.render('account_dashboard_pending_sales_template', data));
            });
            this._rpc({
                model: 'account.year',
                method: 'footer_data',
                args: ['purchases', false]
            }).then(function (data) {
                data.actual_amount = monetary(data.actual_amount);
                $('#pending_purchases').html(QWeb.render('account_dashboard_pending_purchases_template', data));
            });
            // Rendering top partners
            this._rpc({
                model: 'account.year',
                method: 'top_partners',
                args: ['sales', 'month']
            }).then(function (data) {
                data.formater = monetary;
                $('#top_clients_month').html(QWeb.render('account_dashboard_clients_month_template', data));
            });
            this._rpc({
                model: 'account.year',
                method: 'top_partners',
                args: ['sales', 'year']
            }).then(function (data) {
                data.formater = monetary;
                $('#top_clients_year').html(QWeb.render('account_dashboard_clients_year_template', data));
            });
            this._rpc({
                model: 'account.year',
                method: 'top_partners',
                args: ['purchases', 'month']
            }).then(function (data) {
                data.formater = monetary;
                $('#top_providers_month').html(QWeb.render('account_dashboard_providers_month_template', data));
            });
            this._rpc({
                model: 'account.year',
                method: 'top_partners',
                args: ['purchases', 'year']
            }).then(function (data) {
                data.formater = monetary;
                $('#top_providers_year').html(QWeb.render('account_dashboard_providers_year_template', data));
            });

            // Rendering top products
            this._rpc({
                model: 'account.year',
                method: 'top_products',
                args: ['sales', 'month']
            }).then(function (data) {
                data.formater = monetary;
                $('#top_products_sales_month').html(QWeb.render('account_dashboard_products_sales_month_template', data));
            });
            this._rpc({
                model: 'account.year',
                method: 'top_products',
                args: ['sales', 'year']
            }).then(function (data) {
                data.formater = monetary;
                $('#top_products_sales_year').html(QWeb.render('account_dashboard_products_sales_year_template', data));
            });
            this._rpc({
                model: 'account.year',
                method: 'top_products',
                args: ['purchases', 'month']
            }).then(function (data) {
                data.formater = monetary;
                $('#top_products_purchases_month').html(QWeb.render('account_dashboard_products_purchases_month_template', data));
            });
            this._rpc({
                model: 'account.year',
                method: 'top_products',
                args: ['purchases', 'year']
            }).then(function (data) {
                data.formater = monetary;
                $('#top_products_purchases_year').html(QWeb.render('account_dashboard_products_purchases_year_template', data));
            });

            return def;
        },
        draw_chart_account: function (title, char_div, series, colors) {
            Highcharts.chart(char_div, {
                chart: {
                    type: 'column',
                    height: 250
                },
                colors: colors,
                title: {
                    text: title,
                    style: {
                        color: colors[0],
                        fontWeight: 'bold'
                    }
                },
                xAxis: {
                    type: 'category'
                },
                yAxis: {
                    labels: {
                        format: '$ {value}',
                    },
                    title: {
                        text: 'Total invoiced'
                    }
                },
                legend: {
                    enabled: true
                },
                plotOptions: {
                    series: {
                        borderWidth: 0,
                        dataLabels: {
                            enabled: true,
                            format: '$ {y}'
                        }
                    }
                },
                series: series
            });
        },
        draw_chart_budget: function (series) {
            Highcharts.chart('year_budgets_chart', {
                chart: {
                    zoomType: 'xy',
                    height: 300
                },
                colors: ['#FF9149', '#28D094', '#550077'],
                title: {
                    text: 'Budget vs Annual Sales',
                    style: {
                        color: '#FF9149',
                        fontWeight: 'bold'
                    }
                },
                xAxis: [{
                    categories: ['January', 'February', 'March', 'April', 'May', 'June',
                        'July', 'August', 'September', 'October', 'November', 'December'],
                    crosshair: true
                }],
                yAxis: {
                    labels: {
                        format: '$ {value}',
                    },
                    title: {
                        text: 'Total invoiced',
                    }
                },
                tooltip: {
                    shared: true
                },
                legend: {
                    enabled: true
                },
                plotOptions: {
                    series: {
                        borderWidth: 0,
                        dataLabels: {
                            enabled: true,
                            format: '$ {y}'
                        }
                    },
                    column: {
                        grouping: false,
                        shadow: false,
                        borderWidth: 0
                    }
                },
                series: series
            });
        }
    });
    core.action_registry.add("account_dashboard.dashboard", AccountDashboardAction);
});
