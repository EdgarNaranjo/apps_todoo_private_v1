# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo.tools.float_utils import float_round as round
from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta, date, time
from lxml import etree
import base64
import re
from odoo.exceptions import UserError, AccessError, ValidationError

from odoo import tools
import logging
_logger = logging.getLogger(__name__)


class StockModelWzard(models.TransientModel):
    _name = 'customer.model.wizard'
    _description = 'Customer Model Wizard'
    _rec_name = 'state_invoice'

    @api.depends('invoice_filters_ids', 'supplier_filters_ids')
    def _get_amounts_and_date_amount(self):
        user_id = self._uid
        company = self.env['res.users'].browse(user_id).company_id
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for wizard in self:
            amount_due = amount_overdue = 0.0
            supplier_amount_due = supplier_amount_overdue = 0.0
            for aml in wizard.invoice_filters_ids:
                if aml.company_id == company:
                    date_maturity = aml.invoice_date_due or aml.date
                    amount_due += aml.result
                    if str(date_maturity) <= current_date:
                        amount_overdue += aml.result
            wizard.payment_amount_due_amt = amount_due
            wizard.payment_amount_overdue_amt = amount_overdue
            for aml in wizard.supplier_filters_ids:
                if aml.company_id == company:
                    date_maturity = aml.invoice_date_due or aml.date
                    supplier_amount_due += aml.result
                    if str(date_maturity) <= current_date:
                        supplier_amount_overdue += aml.result
            wizard.payment_amount_due_amt_supplier = supplier_amount_due
            wizard.payment_amount_overdue_amt_supplier = supplier_amount_overdue

    start_date = fields.Date('Date Init')
    end_date = fields.Date('Date Finish')
    state_invoice = fields.Boolean('Only Paid', help='Mostrar solo transaciones pagadas')
    invoice_filters_ids = fields.Many2many('account.move', 'account_invoice_wizard_rel', 'wizard_id', 'invoice_id', 'Customer move lines')
    supplier_filters_ids = fields.Many2many('account.move', 'account_invoice_partner_id', 'wizard_id', 'invoice_id', 'Supplier move lines')
    amount_total = fields.Float('Total')
    partner_id = fields.Many2one('res.partner', 'Partner')
    payment_amount_due_amt = fields.Float(compute='_get_amounts_and_date_amount', string="Balance Due")
    payment_amount_overdue_amt = fields.Float(compute='_get_amounts_and_date_amount', string="Total Overdue Amount")
    payment_amount_due_amt_supplier = fields.Float(compute='_get_amounts_and_date_amount', string="Supplier Balance Due")
    payment_amount_overdue_amt_supplier = fields.Float(compute='_get_amounts_and_date_amount', string="Total Supplier Overdue Amount")
    first_thirty_day = fields.Float(string="0-30", compute="compute_zero_thirty_days")
    thirty_sixty_days = fields.Float(string="30-60", compute="compute_thirty_sixty_days")
    sixty_ninty_days = fields.Float(string="60-90", compute="compute_sixty_ninty_days")
    ninty_plus_days = fields.Float(string="90+", compute="compute_ninty_plus_days")
    total = fields.Float(string="Total", compute="compute_total")
    type = fields.Char('Type')

    @api.depends('start_date', 'end_date', 'state_invoice')
    @api.onchange('start_date', 'end_date', 'state_invoice')
    def onchage_get_invoice_filters(self):
        for wizard in self:
            if self.env.context.get('list_id'):
                list_id = self.env.context.get('list_id')
                obj_invoice_all = self.env['account.move'].search([('id', 'in', list_id)])
                wizard.invoice_filters_ids = obj_invoice_all
            if self.env.context.get('list_sup_id'):
                list_sup_id = self.env.context.get('list_sup_id')
                obj_invoice_sup_all = self.env['account.move'].search([('id', 'in', list_sup_id)])
                wizard.supplier_filters_ids = obj_invoice_sup_all
            if self.start_date and self.end_date:
                if wizard.start_date > wizard.end_date:
                    raise ValidationError('La fecha fin "%s" no puede ser menor que la fecha de inicio  "%s".' % (wizard.end_date, wizard.start_date))
                if wizard.invoice_filters_ids:
                    obj_invoice_date_id = wizard.invoice_filters_ids.filtered(lambda e: wizard.start_date <= e.invoice_date <= wizard.end_date)
                    if obj_invoice_date_id:
                        invoice = obj_invoice_date_id
                        if self.state_invoice:
                            obj_invoice_state_id = invoice.filtered(lambda e: e.payment_state == 'paid')
                            invoice = obj_invoice_state_id
                    else:
                        invoice = []
                    list_invoice = [inv_fil.id for inv_fil in invoice]
                    _logger.info("For a list_invoice")
                    wizard.invoice_filters_ids = wizard.invoice_filters_ids.filtered(lambda e: e.id in list_invoice)
                    _logger.info("Asignar a invoice_filter el list_invoice")
                    # wizard.amount_total = wizard.total
                if wizard.supplier_filters_ids:
                    obj_invoice_sup_date_id = wizard.supplier_filters_ids.filtered(lambda e: wizard.start_date <= e.invoice_date <= wizard.end_date)
                    if obj_invoice_sup_date_id:
                        invoice = obj_invoice_sup_date_id
                        if self.state_invoice:
                            obj_invoice_sup_state_id = invoice.filtered(lambda e: e.state == 'open')
                            invoice = obj_invoice_sup_state_id
                    else:
                        invoice = []
                    list_invoice = [inv_fil.id for inv_fil in invoice]
                    _logger.info("For a list_invoice")
                    wizard.supplier_filters_ids = wizard.supplier_filters_ids.filtered(lambda e: e.id in list_invoice)
                    _logger.info("Asignar a invoice_filter el list_invoice")
                    # for fil_supplier in wizard.supplier_filters_ids:
                    #     if fil_supplier.state == 'open':
                    #         wizard.amount_total += fil_supplier.amount_total

    @api.depends('invoice_filters_ids')
    def compute_zero_thirty_days(self):
        self.first_thirty_day = 0
        today = fields.date.today()
        for line in self.invoice_filters_ids:
            diff = today - line.invoice_date
            if diff.days <= 30:
                self.first_thirty_day = self.first_thirty_day + line.result

    @api.depends('invoice_filters_ids')
    def compute_thirty_sixty_days(self):
        self.thirty_sixty_days = 0
        today = fields.date.today()
        for line in self.invoice_filters_ids:
            diff = today - line.invoice_date
            if 30 < diff.days <= 60:
                self.thirty_sixty_days = self.thirty_sixty_days + line.result

    @api.depends('invoice_filters_ids')
    def compute_sixty_ninty_days(self):
        self.sixty_ninty_days = 0
        today = fields.date.today()
        for line in self.invoice_filters_ids:
            diff = today - line.invoice_date
            if 60 < diff.days <= 90:
                self.sixty_ninty_days = self.sixty_ninty_days + line.result

    @api.depends('invoice_filters_ids')
    def compute_ninty_plus_days(self):
        self.ninty_plus_days = 0
        today = fields.date.today()
        for line in self.invoice_filters_ids:
            diff = today - line.invoice_date
            if diff.days > 90:
                self.ninty_plus_days = self.ninty_plus_days + line.result

    @api.depends('ninty_plus_days', 'sixty_ninty_days', 'thirty_sixty_days', 'first_thirty_day')
    def compute_total(self):
        self.total = self.ninty_plus_days + self.sixty_ninty_days + self.thirty_sixty_days + self.first_thirty_day

    def action_print_customer_pdf(self):
        if self.invoice_filters_ids:
            return self.env.ref('account_statement_todoo.report_customer_filter_print').report_action(self)
        if self.supplier_filters_ids:
            return self.env.ref('account_statement_todoo.report_supplier_filter_print').report_action(self)


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _get_result(self):
        for aml in self:
            aml.result = aml.amount_total_signed - aml.credit_amount

    def _get_credit(self):
        for aml in self:
            aml.credit_amount = aml.amount_total_signed - aml.amount_residual_signed

    credit_amount = fields.Float(compute='_get_credit',   string="Credit/paid")
    result = fields.Float(compute='_get_result',   string="Balance") #'balance' field is not the same


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _get_amounts_and_date_amount(self):
        user_id = self._uid
        company = self.env['res.users'].browse(user_id).company_id
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for partner in self:
            amount_due = amount_overdue = 0.0
            supplier_amount_due = supplier_amount_overdue = 0.0
            for aml in partner.balance_invoice_ids:
                if aml.company_id == company:
                    date_maturity = aml.invoice_date_due or aml.date
                    amount_due += aml.result
                    if date_maturity <= current_date:
                        amount_overdue += aml.result
            partner.payment_amount_due_amt = amount_due
            partner.payment_amount_overdue_amt = amount_overdue
            for aml in partner.supplier_invoice_ids:
                if aml.company_id == company:
                    date_maturity = aml.invoice_date_due or aml.date
                    supplier_amount_due += aml.result
                    if date_maturity <= current_date:
                        supplier_amount_overdue += aml.result
            partner.payment_amount_due_amt_supplier = supplier_amount_due
            partner.payment_amount_overdue_amt_supplier = supplier_amount_overdue

    def do_button_print_statement(self):
        obj_invoice_ids = []
        if self.balance_invoice_ids:
            obj_invoice_ids = self.balance_invoice_ids.ids
        context = ({'default_invoice_filters_ids': obj_invoice_ids, 'default_partner_id': self.id, 'list_id': obj_invoice_ids, 'default_type': 'consu'})
        view = self.env.ref('account_statement_todoo.customer_model_wizard_form')
        return {
            'name': _('Print Invoice Customer'),
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'customer.model.wizard',
            'view_id': view.id,
            'views': [(view.id, 'form')],
            'type': 'ir.actions.act_window',
            'context': context,
        }

    def do_button_print_statement_vendor(self):
        obj_invoice_ids = []
        if self.supplier_invoice_ids:
            obj_invoice_ids = self.supplier_invoice_ids.ids
        context = ({'default_supplier_filters_ids': obj_invoice_ids, 'default_partner_id': self.id, 'list_sup_id': obj_invoice_ids, 'default_type': 'supplier'})
        view = self.env.ref('account_statement_todoo.customer_model_wizard_form')
        return {
            'name': _('Print Invoice Vendor'),
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'customer.model.wizard',
            'view_id': view.id,
            'views': [(view.id, 'form')],
            'type': 'ir.actions.act_window',
            'context': context,
        }

    supplier_invoice_ids = fields.One2many('account.move', 'partner_id', 'Customer move lines', domain=[('move_type', 'in', ['in_invoice', 'in_refund']), ('state', 'in', ['posted'])])
    balance_invoice_ids = fields.One2many('account.move', 'partner_id', 'Customer move lines', domain=[('move_type', 'in', ['out_invoice', 'out_refund']), ('state', 'in', ['posted'])])
