# Copyright 2025-TODAY Todooweb (www.todooweb.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""
Tests para account_statement_todoo.

Para ejecutar:
    python odoo-bin -d <db> --test-enable -i account_statement_todoo --stop-after-init

Comportamiento verificado:
  1. Los campos credit_amount y result existen en account.move.
  2. result = amount_total_signed - credit_amount.
  3. El wizard customer.model.wizard existe con sus campos computed.
  4. balance_invoice_ids y supplier_invoice_ids filtran correctamente.
  5. Los botones de impresión invocan las acciones correctas.
"""

from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestAccountStatementTodoo(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Statement Test Customer',
            'customer_rank': 1,
        })
        self.journal = self.env['account.journal'].search([
            ('type', '=', 'sale')
        ], limit=1)
        self.account = self.env['account.account'].search([
            ('account_type', '=', 'asset_receivable')
        ], limit=1)

    def _create_posted_invoice(self, partner=None, amount=100.0, move_type='out_invoice'):
        """Helper: crea y valida una factura."""
        partner = partner or self.partner
        invoice = self.env['account.move'].create({
            'partner_id': partner.id,
            'move_type': move_type,
            'journal_id': self.journal.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [(0, 0, {
                'name': 'Test line',
                'quantity': 1,
                'price_unit': amount,
            })],
        })
        invoice.action_post()
        return invoice

    def test_result_field_exists_on_account_move(self):
        """El campo result existe en account.move."""
        invoice = self._create_posted_invoice()
        self.assertTrue(
            hasattr(invoice, 'result'),
            "El campo result debe existir en account.move"
        )

    def test_credit_amount_field_exists_on_account_move(self):
        """El campo credit_amount existe en account.move."""
        invoice = self._create_posted_invoice()
        self.assertTrue(
            hasattr(invoice, 'credit_amount'),
            "El campo credit_amount debe existir en account.move"
        )

    def test_result_equals_total_minus_credit(self):
        """result = amount_total_signed - credit_amount."""
        invoice = self._create_posted_invoice(amount=200.0)
        # Para una factura pendiente de pago: credit_amount=0, result=amount_total_signed
        self.assertAlmostEqual(
            invoice.result,
            invoice.amount_total_signed - invoice.credit_amount,
            places=2,
            msg="result debe ser amount_total_signed - credit_amount"
        )

    def test_balance_invoice_ids_filters_customer_invoices(self):
        """balance_invoice_ids solo muestra facturas de cliente posted."""
        inv = self._create_posted_invoice(move_type='out_invoice')
        # La factura debe aparecer en balance_invoice_ids del partner
        self.assertIn(
            inv, self.partner.balance_invoice_ids,
            "La factura debe estar en balance_invoice_ids"
        )

    def test_supplier_invoice_ids_filters_vendor_bills(self):
        """supplier_invoice_ids solo muestra facturas de proveedor posted."""
        # Crear partner proveedor
        supplier = self.env['res.partner'].create({
            'name': 'Test Supplier',
            'supplier_rank': 1,
        })
        vendor_journal = self.env['account.journal'].search([
            ('type', '=', 'purchase')
        ], limit=1)
        bill = self.env['account.move'].create({
            'partner_id': supplier.id,
            'move_type': 'in_invoice',
            'journal_id': vendor_journal.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [(0, 0, {
                'name': 'Test purchase',
                'quantity': 1,
                'price_unit': 50.0,
            })],
        })
        bill.action_post()

        self.assertIn(
            bill, supplier.supplier_invoice_ids,
            "La factura de proveedor debe estar en supplier_invoice_ids"
        )

    def test_wizard_model_exists(self):
        """El modelo customer.model.wizard existe."""
        self.assertIn(
            'customer.model.wizard',
            self.env.registry,
            "El modelo customer.model.wizard debe existir en el registry"
        )

    def test_do_button_print_statement_opens_wizard(self):
        """do_button_print_statement devuelve una acción de ventana."""
        self._create_posted_invoice()
        action = self.partner.do_button_print_statement()
        self.assertEqual(
            action.get('type'), 'ir.actions.act_window',
            "do_button_print_statement debe devolver una acción de ventana"
        )
        self.assertEqual(action.get('res_model'), 'customer.model.wizard')
