import time
from collections import OrderedDict

import pytz
from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models

MONTHS = OrderedDict(
    [
        (_('January'), 1),
        (_('February'), 1),
        (_('March'), 1),
        (_('April'), 2),
        (_('May'), 2),
        (_('June'), 2),
        (_('July'), 3),
        (_('August'), 3),
        (_('September'), 3),
        (_('October'), 4),
        (_('November'), 4),
        (_('December'), 4),
    ]
)
MADRID_TZ = pytz.timezone('Europe/Madrid')


class AccountYearPartner(models.Model):
    _name = 'account.year.partner'
    _description = 'Account top partners'
    _order = 'sequence'

    account_year_id = fields.Many2one(
        'account.year', 'Year', ondelete='cascade'
    )
    sequence = fields.Integer()
    name = fields.Char(related='partner_id.name')
    partner_id = fields.Many2one('res.partner')
    mode = fields.Selection([('sales', 'Sales'), ('purchases', 'Purchase')])
    period = fields.Selection([('month', 'Month'), ('year', 'Year')])
    amount = fields.Float()
    parent_id = fields.Many2one('res.partner', related='partner_id.parent_id')
    parent_name = fields.Char(related='parent_id.name')


class AccountYearProduct(models.Model):
    _name = 'account.year.product'
    _description = 'Account top products'
    _order = 'sequence'

    account_year_id = fields.Many2one(
        'account.year', 'Year', ondelete='cascade'
    )
    sequence = fields.Integer()
    name = fields.Char(related='product_id.display_name')
    product_id = fields.Many2one('product.product')
    mode = fields.Selection([('sales', 'Sales'), ('purchases', 'Purchase')])
    period = fields.Selection([('month', 'Month'), ('year', 'Year')])
    qty = fields.Float()
    amount = fields.Float()


class AccountYearMonth(models.Model):
    _name = 'account.year.month'
    _description = 'Account monthly data from year'

    name = fields.Char('Mes', required=True, translate=True)
    no_update = fields.Boolean(
        'No actualizar',
        default=False,
        help="If checked, it will not automatically update this month's amounts, respecting manually entered amounts."
    )
    account_year_id = fields.Many2one(
        'account.year', 'Year', ondelete='cascade'
    )
    currency_id = fields.Many2one(
        'res.currency', related='account_year_id.currency_id'
    )
    sale_amount = fields.Monetary('Sales')
    purchase_amount = fields.Monetary('Purchase')
    budget_amount = fields.Monetary('Budget')
    quarter = fields.Integer('Quarter', required=True)
    sequence = fields.Integer()


class AccountYear(models.Model):
    _name = 'account.year'
    _description = 'Account Year'
    _order = 'name desc'

    @api.model
    def _default_months(self):
        return [
            (0, 0, {'name': name, 'quarter': quarter, 'sequence': seq})
            for seq, (name, quarter) in enumerate(MONTHS.items(), 1)
        ]

    name = fields.Integer(
        'Year',
        required=True,
        copy=False,
        default=lambda self: fields.Date.from_string(fields.Date.today()).year,
    )
    currency_id = fields.Many2one(
        'res.currency',
        'Currency',
        default=lambda self: self.env.user.company_id.currency_id,
    )
    month_ids = fields.One2many(
        'account.year.month',
        'account_year_id',
        'Monthly Data',
        default=_default_months,
    )
    active = fields.Boolean(default=True)
    q1_sales = fields.Monetary(
        'Sales 1st quarter', compute='_compute_quarters'
    )
    q2_sales = fields.Monetary(
        'Sales 2nd quarter', compute='_compute_quarters'
    )
    q3_sales = fields.Monetary(
        'Sales 3rd quarter', compute='_compute_quarters'
    )
    q4_sales = fields.Monetary(
        'Sales 4th quarter', compute='_compute_quarters'
    )
    q1_purchases = fields.Monetary(
        'Purchase 1st quarter', compute='_compute_quarters'
    )
    q2_purchases = fields.Monetary(
        'Purchase 2nd quarter', compute='_compute_quarters'
    )
    q3_purchases = fields.Monetary(
        'Purchase 3rd quarter', compute='_compute_quarters'
    )
    q4_purchases = fields.Monetary(
        'Purchase 4th quarter', compute='_compute_quarters'
    )
    q1_budgets = fields.Monetary(
        'Budget 1st quarter', compute='_compute_quarters'
    )
    q2_budgets = fields.Monetary(
        'Budget 2nd quarter', compute='_compute_quarters'
    )
    q3_budgets = fields.Monetary(
        'Budget 3rd quarter', compute='_compute_quarters'
    )
    q4_budgets = fields.Monetary(
        'Budget 4th quarter', compute='_compute_quarters'
    )
    budget_amount = fields.Monetary('Budget')
    total_sales = fields.Monetary('Total sales', compute='_compute_quarters')
    total_purchases = fields.Monetary(
        'Total purchase', compute='_compute_quarters'
    )
    total_budgets = fields.Monetary(
        'Total budget', compute='_compute_quarters'
    )
    # header fields
    sales_day = fields.Monetary('Sales of the day')
    sales_month = fields.Monetary('Sales of the month')
    purchases_day = fields.Monetary('Purchase of the day')
    purchases_month = fields.Monetary('Purchase of the month')
    past_sales_day = fields.Monetary('Sales of the day (prev)')
    past_sales_month = fields.Monetary('Sales of the month (prev)')
    past_purchases_day = fields.Monetary('Purchase of the day (prev)')
    past_purchases_month = fields.Monetary('Purchase of the month (prev)')
    # footer fields
    current_total_sales = fields.Monetary('Cumulative sales')
    current_total_purchases = fields.Monetary('Cumulative purchase')
    past_total_sales = fields.Monetary('Cumulative sales (prev)')
    past_total_purchases = fields.Monetary('Cumulative purchase (prev)')
    pending_sales_amount = fields.Monetary('Accounts receivable (amount)')
    pending_sales_count = fields.Monetary('Accounts receivable (qty)')
    pending_purchases_amount = fields.Monetary('Accounts payable (amount)')
    pending_purchases_count = fields.Monetary('Accounts payable (qty)')
    # Top list fields
    top_partner_ids = fields.One2many(
        'account.year.partner', 'account_year_id', 'Top partners'
    )
    top_product_ids = fields.One2many(
        'account.year.product', 'account_year_id', 'Top products'
    )

    _sql_constraints = [
        ('unique_year', 'unique(name)', _('Year must be unique.'))
    ]

    def toggle_active(self):
        for rec in self:
            rec.active = not rec.active

    @api.onchange('budget_amount')
    def onchange_budget_amount(self):
        self.month_ids.update({'budget_amount': self.budget_amount})

    def _compute_quarters(self):
        for record in self:
            quarters = {
                '%d_%s' % (q, t): 0.0
                for q in [1, 2, 3, 4]
                for t in ['sales', 'purchases', 'budgets']
            }
            for month in record.month_ids:
                quarters['%d_sales' % month.quarter] += month.sale_amount
                quarters[
                    '%d_purchases' % month.quarter
                ] += month.purchase_amount
                quarters['%d_budgets' % month.quarter] += month.budget_amount
            for quarter, value in quarters.items():
                record['q%s' % quarter] = value
            record.total_sales = sum(
                record['q%d_sales' % i] for i in [1, 2, 3, 4]
            )
            record.total_purchases = sum(
                record['q%d_purchases' % i] for i in [1, 2, 3, 4]
            )
            record.total_budgets = sum(
                record['q%d_budgets' % i] for i in [1, 2, 3, 4]
            )

    def update_data(self):
        include_taxes = bool(
            int(self.env.ref('account_dashboard.include_taxes_parameter').value)
        )
        invoice_obj = self.env['account.move']
        for record in self:
            invoices = invoice_obj.search(
                [
                    ('invoice_date', '>=', '%d-01-01' % record.name),
                    ('invoice_date', '<=', '%d-12-31' % record.name),
                    ('move_type', '!=', 'entry'),
                    ('state', 'not in', ['draft', 'cancel']),
                ]
            )
            if not invoices:
                continue
            # Cleaning months data before starting
            no_update = []
            for month in record.month_ids:
                no_update.append(month.no_update)
                if month.no_update:
                    continue
                month.sale_amount = 0
                month.purchase_amount = 0
            for invoice in invoices:
                index = fields.Date.from_string(invoice.invoice_date).month - 1
                if no_update[index]:
                    continue
                amount = (
                    invoice.amount_total_signed
                    if include_taxes
                    else invoice.amount_untaxed_signed
                )
                if (
                    invoice.move_type in ['in_invoice', 'in_refund']
                    and invoice.invoice_date
                ):
                    record.month_ids[index].purchase_amount += amount
                else:
                    record.month_ids[index].sale_amount += amount
            record.compute_data()

    @api.model
    def run_update_data(self):
        self.search([]).update_data()
        self.search([], limit=1).compute_data()

    def compute_data(self):
        for record in self:
            # header data
            record.sales_day, record.past_sales_day = self.compute_header_data(
                'sale', 'day'
            )
            record.sales_month, record.past_sales_month = (
                self.compute_header_data('sale', 'month')
            )
            record.purchases_day, record.past_purchases_day = (
                self.compute_header_data('purchase', 'day')
            )
            record.purchases_month, record.past_purchases_month = (
                self.compute_header_data('purchase', 'month')
            )
            # footer data
            record.current_total_sales, record.past_total_sales = (
                self.compute_footer_data('sales')
            )
            record.current_total_purchases, record.past_total_purchases = (
                self.compute_footer_data('purchases')
            )
            record.pending_sales_amount, record.pending_sales_count = (
                self.compute_footer_data('sales', total=False)
            )
            record.pending_purchases_amount, record.pending_purchases_count = (
                self.compute_footer_data('purchases', total=False)
            )
            # top partners
            record.top_partner_ids.unlink()
            record.top_partner_ids = (
                self.compute_top_partners('sales', 'month')
                + self.compute_top_partners('sales', 'year')
                + self.compute_top_partners('purchases', 'month')
                + self.compute_top_partners('purchases', 'year')
            )
            # top products
            record.top_product_ids.unlink()
            record.top_product_ids = (
                self.compute_top_products('sales', 'month')
                + self.compute_top_products('sales', 'year')
                + self.compute_top_products('purchases', 'month')
                + self.compute_top_products('purchases', 'year')
            )

    @api.model
    def get_period_amount(self, invoice_type, start, end):
        include_taxes = bool(
            int(self.env.ref('account_dashboard.include_taxes_parameter').value)
        )
        invoices = self.env['account.move'].search(
            [
                ('move_type', 'in', invoice_type),
                ('invoice_date', '>=', start),
                ('invoice_date', '<=', end),
                ('state', 'not in', ['draft', 'cancel']),
            ]
        )
        total_amount = 0
        for inv in invoices:
            amount = (
                inv.amount_total_signed
                if include_taxes
                else inv.amount_untaxed_signed
            )
            total_amount += amount
        return total_amount

    @api.model
    def compute_header_data(self, mode, period):
        local = pytz.timezone(
            self.env.user.tz
            or self.env.context.get('tz')
            or time.tzname[0]
            or MADRID_TZ
        )
        inv_type = (
            ['out_invoice', 'out_refund']
            if mode == 'sale'
            else ['in_invoice', 'in_refund']
        )
        now = fields.Datetime.from_string(fields.Datetime.now())
        today = now.replace(tzinfo=pytz.utc).astimezone(local).date()
        if period == 'day':
            date_start = date_end = today
            past_start = past_end = today - relativedelta(years=1)
        else:
            date_start = today + relativedelta(day=1)
            date_end = today + relativedelta(months=1, day=1, days=-1)
            past_start = today + relativedelta(day=1, years=-1)
            past_end = today + relativedelta(months=1, day=1, days=-1, years=-1)

        return (
            self.get_period_amount(inv_type, date_start, date_end),
            self.get_period_amount(inv_type, past_start, past_end),
        )

    @api.model
    def header_data(self, mode, period):
        record = self.search([], limit=1)
        actual_amount = record['%ss_%s' % (mode, period)]
        past_amount = record['past_%ss_%s' % (mode, period)]
        return {
            'actual_amount': actual_amount,
            'past_amount': past_amount,
            'diff_amount': past_amount
            and int(round(actual_amount * 100 / past_amount - 100))
            or 0,
        }

    @api.model
    def chart_data(self, mode='sales'):
        divider = float(
            self.env.ref('account_dashboard.amount_divider_parameter').value
        )
        return [
            {
                'name': str(record.name),
                'tooltip': {'valueSuffix': ' %s' % record.currency_id.symbol},
                'data': [
                    {
                        'name': _('Quarter %d') % i,
                        'y': round(record['q%d_%s' % (i, mode)] / divider, 2),
                    }
                    for i in [1, 2, 3, 4]
                ],
            }
            for record in self.search([])
        ]

    @api.model
    def chart_budget(self, year=None):
        divider = float(
            self.env.ref('account_dashboard.amount_divider_parameter').value
        )
        record = self.search(
            [('name', '=', int(year))] if year else [], limit=1
        )
        sales, budgets = (
            zip(
                *[
                    (
                        round(m.sale_amount / divider, 2),
                        round(m.budget_amount / divider, 2),
                    )
                    for m in record.month_ids
                ]
            )
            if record.month_ids
            else (0, 0)
        )
        data = [
            {
                'name': _('Sales'),
                'type': 'column',
                'tooltip': {'valueSuffix': ' %s' % record.currency_id.symbol},
                'data': sales,
            },
            {
                'name': _('Goals'),
                'type': 'spline',
                'tooltip': {'valueSuffix': ' %s' % record.currency_id.symbol},
                'data': budgets,
            },
        ]
        past_record = self.search([('name', '=', record.name - 1)])
        if past_record:
            data.insert(
                1,
                {
                    'name': _('Previous'),
                    'type': 'column',
                    'tooltip': {
                        'valueSuffix': ' %s' % past_record.currency_id.symbol
                    },
                    'pointPadding': 0.3,
                    'data': [
                        round(month.sale_amount / divider, 2)
                        for month in past_record.month_ids
                    ],
                },
            )
        return data

    @api.model
    def compute_footer_data(self, mode, total=True):
        today = fields.Date.from_string(fields.Date.today())
        inv_type = (
            ['out_invoice', 'out_refund']
            if mode == 'sales'
            else ['in_invoice', 'in_refund']
        )
        this_year_start = today + relativedelta(yearday=1)
        this_year_end = today + relativedelta(yearday=1, years=1, days=-1)
        if total:
            last_year_start = today + relativedelta(yearday=1, years=-1)
            last_year_end = today + relativedelta(yearday=1, days=-1)
            actual_amount = self.get_period_amount(
                inv_type, this_year_start, this_year_end
            )
            past_amount = self.get_period_amount(
                inv_type, last_year_start, last_year_end
            )
            return (actual_amount, past_amount)
        pending_docs = self.env['account.move'].search(
            [
                ('move_type', 'in', inv_type),
                ('invoice_date', '>=', this_year_start),
                ('invoice_date', '<=', this_year_end),
                ('state', 'not in', ['draft', 'cancel', 'paid']),
            ]
        )
        return (
            sum(inv.amount_residual_signed for inv in pending_docs),
            len(pending_docs),
        )

    @api.model
    def footer_data(self, mode, total=True):
        record = self.search([], limit=1)
        data = {}
        if total:
            actual_amount = record['current_total_%s' % mode]
            past_amount = record['past_total_%s' % mode]
            data.update(
                {
                    'actual_amount': actual_amount,
                    'past_amount': past_amount,
                    'diff_amount': past_amount
                    and int(round(actual_amount * 100 / past_amount - 100))
                    or 0,
                }
            )
        else:
            data.update(
                {
                    'actual_amount': record['pending_%s_amount' % mode],
                    'doc_amount': record['pending_%s_count' % mode],
                }
            )
        return data

    @api.model
    def compute_top_partners(self, mode, period):
        include_taxes = bool(
            int(self.env.ref('account_dashboard.include_taxes_parameter').value)
        )
        local = pytz.timezone(
            self.env.user.tz
            or self.env.context.get('tz')
            or time.tzname[0]
            or MADRID_TZ
        )
        inv_type = (
            ['out_invoice', 'out_refund']
            if mode == 'sales'
            else ['in_invoice', 'in_refund']
        )
        now = fields.Datetime.from_string(fields.Datetime.now())
        today = now.replace(tzinfo=pytz.utc).astimezone(local).date()
        if period == 'month':
            date_start = today + relativedelta(day=1)
            date_end = today + relativedelta(day=1, months=1, days=-1)
        else:
            date_start = today + relativedelta(yearday=1)
            date_end = today + relativedelta(yearday=1, years=1, days=-1)
        invoices = self.env['account.move'].search(
            [
                ('move_type', 'in', inv_type),
                ('invoice_date', '>=', date_start),
                ('invoice_date', '<=', date_end),
                ('state', 'not in', ['draft', 'cancel']),
            ]
        )
        partners = {}
        for invoice in invoices:
            amount = (
                invoice.amount_total_signed
                if include_taxes
                else invoice.amount_untaxed_signed
            )
            if invoice.partner_id not in partners:
                partners[invoice.partner_id] = amount
            else:
                partners[invoice.partner_id] += amount
        return [
            (
                0,
                0,
                {
                    'sequence': i,
                    'partner_id': partner.id,
                    'amount': amount,
                    'mode': mode,
                    'period': period,
                },
            )
            for i, (partner, amount) in enumerate(
                sorted(partners.items(), key=lambda i: i[1], reverse=True)[:10],
                1,
            )
        ]

    @api.model
    def top_partners(self, mode, period):
        record = self.search([], limit=1)
        return {
            'partners': [
                {
                    'i': partner.sequence,
                    'name': partner.name,
                    'amount': partner.amount,
                    'parent_id': partner.parent_id,
                    'parent_name': partner.parent_name,
                }
                for partner in record.top_partner_ids.filtered(
                    lambda p: p.mode == mode and p.period == period
                )
            ]
        }

    @api.model
    def compute_top_products(self, mode, period):
        local = pytz.timezone(
            self.env.user.tz
            or self.env.context.get('tz')
            or time.tzname[0]
            or MADRID_TZ
        )
        inv_type = (
            ['out_invoice', 'out_refund', 'out_receipt']
            if mode == 'sales'
            else ['in_invoice', 'in_refund', 'in_receipt']
        )
        now = fields.Datetime.from_string(fields.Datetime.now())
        today = now.replace(tzinfo=pytz.utc).astimezone(local).date()
        if period == 'month':
            date_start = today + relativedelta(day=1)
            date_end = today + relativedelta(day=1, months=1, days=-1)
        else:
            date_start = today + relativedelta(yearday=1)
            date_end = today + relativedelta(yearday=1, years=1, days=-1)
        invoices = self.env['account.move'].search(
            [
                ('move_type', 'in', inv_type),
                ('invoice_date', '>=', date_start),
                ('invoice_date', '<=', date_end),
                ('state', 'not in', ['draft', 'cancel']),
            ]
        )
        products = {}
        for line in invoices.mapped('invoice_line_ids'):
            if not line.product_id:
                continue
            if line.product_id and line.product_id.detailed_type != 'service':
                if line.product_id not in products:
                    products[line.product_id] = [line.quantity, line.price_subtotal]
                else:
                    products[line.product_id][0] += line.quantity
                    products[line.product_id][1] += line.price_subtotal
        return [
            (
                0,
                0,
                {
                    'sequence': i,
                    'product_id': product.id,
                    'qty': qty,
                    'amount': amount,
                    'mode': mode,
                    'period': period,
                },
            )
            for i, (product, (qty, amount)) in enumerate(
                sorted(products.items(), key=lambda i: i[1][0], reverse=True)[
                    :10
                ],
                1,
            )
        ]

    @api.model
    def top_products(self, mode, period):
        record = self.search([], limit=1)
        return {
            'products': [
                {
                    'i': product.sequence,
                    'name': product.name,
                    'qty': product.qty,
                    'amount': product.amount,
                }
                for product in record.top_product_ids.filtered(
                    lambda p: p.mode == mode and p.period == period
                )
            ]
        }
