# Copyright 2024-TODAY Todooweb (www.todooweb.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from psycopg2.extensions import TransactionRollbackError
from odoo.tools.float_utils import float_is_zero
from odoo.tools import config
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _create_recurring_invoice(self, automatic=False, batch_size=30):
        automatic = bool(automatic)
        auto_commit = automatic and not bool(config['test_enable'] or config['test_file'])
        Mail = self.env['mail.mail']
        today = fields.Date.today()
        if len(self) > 0:
            all_subscriptions = self.filtered(
                lambda so: so.is_subscription and so.subscription_management != 'upsell' and not so.payment_exception)
            need_cron_trigger = False
        else:
            search_domain = self._recurring_invoice_domain()
            all_subscriptions = self.search(search_domain, limit=batch_size + 1)
            need_cron_trigger = len(all_subscriptions) > batch_size
            if need_cron_trigger:
                all_subscriptions = all_subscriptions[:batch_size]
        if not all_subscriptions:
            return self.env['account.move']
        # don't spam sale with assigned emails.
        all_subscriptions = all_subscriptions.with_context(mail_auto_subscribe_no_notify=True)
        auto_close_subscription = all_subscriptions.filtered_domain([('end_date', '!=', False)])
        all_invoiceable_lines = all_subscriptions.with_context(recurring_automatic=automatic)._get_invoiceable_lines(
            final=False)

        auto_close_subscription._subscription_auto_close_and_renew()
        if automatic:
            all_subscriptions.write({'is_invoice_cron': True})
        lines_to_reset_qty = self.env[
            'sale.order.line']  # qty_delivered is set to 0 after invoicing for some categories of products (timesheets etc)
        account_moves = self.env['account.move']
        # Set quantity to invoice before the invoice creation. If something goes wrong, the line will appear as "to invoice"
        # It prevent to use the _compute method and compare the today date and the next_invoice_date in the compute.
        # That would be bad for perfs
        all_invoiceable_lines._reset_subscription_qty_to_invoice()
        if auto_commit:
            self.env.cr.commit()
        if not automatic and 'draft' in set(all_subscriptions.order_line.invoice_lines.move_id.mapped('state')):
            raise UserError('You cannot create another draft invoice. Please cancel it first and try again.')
        for subscription in all_subscriptions:
            # We only invoice contract in sale state. Locked contracts are invoiced in advance. They are frozen.
            if not (subscription.state == 'sale' and subscription.stage_category == 'progress'):
                continue
            try:
                subscription = subscription[
                    0]  # Trick to not prefetch other subscriptions, as the cache is currently invalidated at each iteration
                # in rare occurrences (due to external issues not related with Odoo), we may have
                # our crons running on multiple workers thus doing work in parallel
                # to avoid processing a subscription that might already be processed
                # by a different worker, we check that it has not already been set to "in exception"
                if subscription.payment_exception:
                    continue
                if auto_commit:
                    self.env.cr.commit()  # To avoid a rollback in case something is wrong, we create the invoices one by one
                invoiceable_lines = all_invoiceable_lines.filtered(lambda l: l.order_id.id == subscription.id)
                invoice_is_free = float_is_zero(sum(invoiceable_lines.mapped('price_subtotal')),
                                                precision_rounding=subscription.currency_id.rounding)
                if not invoiceable_lines or invoice_is_free:
                    # We still update the next_invoice_date if it is due
                    if not automatic or subscription.next_invoice_date < today:
                        subscription._update_next_invoice_date()
                        if invoice_is_free:
                            subscription._subscription_post_success_free_renewal()
                    if auto_commit:
                        self.env.cr.commit()
                    continue
                try:
                    invoice = subscription.with_context(recurring_automatic=automatic)._create_invoices()
                    lines_to_reset_qty |= invoiceable_lines
                except Exception as e:
                    if auto_commit:
                        self.env.cr.rollback()
                    elif isinstance(e, TransactionRollbackError):
                        # the transaction is broken we should raise the exception
                        raise
                    # we suppose that the payment is run only once a day
                    email_context = subscription._get_subscription_mail_payment_context()
                    error_message = _("Error during renewal of contract %s (Payment not recorded)", subscription.name)
                    _logger.exception(error_message)
                    mail = Mail.sudo().create({'body_html': error_message, 'subject': error_message,
                                               'email_to': email_context['responsible_email'], 'auto_delete': True})
                    mail.send()
                    continue
                if auto_commit:
                    self.env.cr.commit()
                # Handle automatic payment or invoice posting
                if automatic:
                    # quitado publicar facturas
                    existing_invoices = subscription._handle_automatic_invoices(auto_commit, invoice)
                    account_moves |= existing_invoices
                else:
                    account_moves |= invoice
                subscription.with_context(mail_notrack=True).write({'payment_exception': False})
            except Exception as error:
                _logger.exception("Error during renewal of contract %s",
                                  subscription.client_order_ref or subscription.name)
                if auto_commit:
                    self.env.cr.rollback()
                if not automatic:
                    raise error
            else:
                if auto_commit:
                    self.env.cr.commit()
        lines_to_reset_qty._reset_subscription_quantity_post_invoice()
        # quitado envio Factura
        # all_subscriptions._process_invoices_to_send(account_moves, auto_commit)
        # There is still some subscriptions to process. Then, make sure the CRON will be triggered again asap.
        if need_cron_trigger:
            if config['test_enable'] or config['test_file']:
                # Test environnement: we launch the next iteration in the same thread
                self.env['sale.order']._create_recurring_invoice(automatic, batch_size)
            else:
                self.env.ref('sale_subscription.account_analytic_cron_for_invoice')._trigger()

        if automatic and not need_cron_trigger:
            cron_subs = self.search([('is_invoice_cron', '=', True)])
            cron_subs.write({'is_invoice_cron': False})

        if not need_cron_trigger:
            failing_subscriptions = self.search([('is_batch', '=', True)])
            failing_subscriptions.write({'is_batch': False})

        return account_moves

    def _handle_automatic_invoices(self, auto_commit, invoices):
        """ This method handle the subscription with or without payment token """
        Mail = self.env['mail.mail']
        automatic_values = self._get_automatic_subscription_values()
        existing_invoices = invoices
        for order in self:
            invoice = invoices.filtered(lambda inv: inv.invoice_origin == order.name)
            email_context = self._get_subscription_mail_payment_context()
            # Set the contract in exception. If something go wrong, the exception remains.
            order.with_context(mail_notrack=True).write({'payment_exception': True})
            if order.payment_token_id:
                payment_callback_done = False
                try:
                    payment_token = order.payment_token_id
                    transaction = None
                    # execute payment
                    if payment_token:
                        if not payment_token.partner_id.country_id:
                            msg_body = 'Automatic payment failed. Contract set to "To Renew". No country specified on payment_token\'s partner'
                            order.message_post(body=msg_body)
                            order.with_context(mail_notrack=True).write(automatic_values)
                            invoice.unlink()
                            existing_invoices -= invoice
                            if auto_commit:
                                self.env.cr.commit()
                            continue
                        transaction = order._do_payment(payment_token, invoice)
                        payment_callback_done = transaction and transaction.sudo().callback_is_done
                        # commit change as soon as we try the payment, so we have a trace in the payment_transaction table
                        if auto_commit:
                            self.env.cr.commit()
                    # if transaction is a success, post a message
                    if transaction and transaction.state == 'done':
                        order.with_context(mail_notrack=True).write({'payment_exception': False})
                        self._subscription_post_success_payment(invoice, transaction)
                        if auto_commit:
                            self.env.cr.commit()
                    # if no transaction or failure, log error, rollback and remove invoice
                    if transaction and transaction.state != 'done':
                        if auto_commit:
                            # prevent rollback during tests
                            self.env.cr.rollback()
                        order._handle_subscription_payment_failure(invoice, transaction, email_context)
                        existing_invoices -= invoice  # It will be unlinked in the call above
                except Exception:
                    if auto_commit:
                        # prevent rollback during tests
                        self.env.cr.rollback()
                    # we suppose that the payment is run only once a day
                    last_transaction = self.env['payment.transaction'].search(['|',
                        ('reference', 'like', order.client_order_ref),
                        ('reference', 'like', order.name)
                    ], limit=1)
                    error_message = "Error during renewal of contract [%s] %s (%s)" \
                                    % (order.id, order.client_order_ref or order.name, 'Payment recorded: %s' % last_transaction.reference
                                       if last_transaction and last_transaction.state == 'done' else 'Payment not recorded')
                    _logger.exception(error_message)
                    mail = Mail.sudo().create({'body_html': error_message, 'subject': error_message,
                                        'email_to': email_context.get('responsible_email'), 'auto_delete': True})
                    mail.send()
                    if invoice.state == 'draft':
                        existing_invoices -= invoice
                        if not payment_callback_done:
                            invoice.unlink()
        return existing_invoices
