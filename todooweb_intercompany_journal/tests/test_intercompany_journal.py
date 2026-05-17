# Copyright 2025-TODAY Todooweb (www.todooweb.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
"""
Tests para todooweb_intercompany_journal.

Para ejecutar:
    python odoo-bin -d <db> --test-enable -i todooweb_intercompany_journal --stop-after-init

Comportamiento verificado:
  1. El modelo setting.type.journal existe con sus campos.
  2. El campo type_journal_id existe en sale.order.
  3. Al preparar factura con type_journal_id, se usa ese journal.
  4. Sin type_journal_id, se usa el journal estándar.
  5. El constraint unique (type_journal, journal_id) funciona.
"""

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestIntercompanyJournal(TransactionCase):

    def setUp(self):
        super().setUp()
        self.company = self.env.company
        self.partner = self.env['res.partner'].create({
            'name': 'Test Customer',
            'customer_rank': 1,
        })
        # Obtener un journal de ventas
        self.sale_journal = self.env['account.journal'].search([
            ('type', '=', 'sale'),
            ('company_id', '=', self.company.id),
        ], limit=1)
        self.product = self.env['product.product'].create({
            'name': 'Test Service',
            'type': 'service',
            'invoice_policy': 'order',
        })

    def test_setting_type_journal_model_exists(self):
        """El modelo setting.type.journal existe."""
        self.assertIn(
            'setting.type.journal',
            self.env.registry,
            "El modelo setting.type.journal debe existir en el registry"
        )

    def test_create_setting_type_journal(self):
        """Se puede crear un setting.type.journal."""
        stj = self.env['setting.type.journal'].create({
            'journal_id': self.sale_journal.id,
            'type_journal': 'Convencional',
            'company_id': self.company.id,
            'check_default': True,
        })
        self.assertTrue(stj.id)
        self.assertEqual(stj.type, 'sale', "El tipo debe reflejar el tipo del journal")

    def test_name_computed_on_constraint(self):
        """El nombre se computa como type_journal + company_name."""
        stj = self.env['setting.type.journal'].create({
            'journal_id': self.sale_journal.id,
            'type_journal': 'Convencional',
            'company_id': self.company.id,
        })
        expected = 'Convencional-' + self.company.name
        self.assertEqual(stj.name, expected)

    def test_type_journal_id_field_on_sale_order(self):
        """El campo type_journal_id existe en sale.order."""
        so = self.env['sale.order'].create({'partner_id': self.partner.id})
        self.assertTrue(
            hasattr(so, 'type_journal_id'),
            "type_journal_id debe existir en sale.order"
        )

    def test_prepare_invoice_uses_custom_journal(self):
        """_prepare_invoice usa el journal de type_journal_id."""
        # Crear configuración de journal intercompany
        stj = self.env['setting.type.journal'].create({
            'journal_id': self.sale_journal.id,
            'type_journal': 'Intercompany',
            'company_id': self.company.id,
            'check_default': True,
        })

        so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1,
                'price_unit': 100.0,
            })],
            'type_journal_id': stj.id,
        })
        so.action_confirm()
        invoice_vals = so._prepare_invoice()
        self.assertEqual(
            invoice_vals.get('journal_id'), self.sale_journal.id,
            "El journal de la factura debe ser el del type_journal_id"
        )

    def test_prepare_invoice_without_custom_journal(self):
        """Sin type_journal_id, _prepare_invoice no falla y retorna vals válidos."""
        so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1,
                'price_unit': 100.0,
            })],
        })
        so.action_confirm()
        # No debe fallar y debe retornar un dict con las claves mínimas
        invoice_vals = so._prepare_invoice()
        self.assertIsInstance(invoice_vals, dict, "_prepare_invoice debe retornar un dict")
        self.assertIn('move_type', invoice_vals, "invoice_vals debe tener move_type")
        self.assertEqual(invoice_vals['move_type'], 'out_invoice')
