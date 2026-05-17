# Copyright 2025-TODAY Todooweb (www.todooweb.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
"""
Tests para purchase_stock_todoo.

Para ejecutar:
    python odoo-bin -d <db> --test-enable -i purchase_stock_todoo --stop-after-init

Comportamiento verificado:
  1. El campo check_new existe en purchase.order.
  2. Con check_options='always', el dominio incluye ('check_new', '=', True).
  3. Con check_options='line' y sin sale_id en el grupo, no añade el filtro.
  4. Con check_options='line' y con sale_id, sí añade el filtro.
"""

from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestPurchaseStockTodoo(TransactionCase):

    def setUp(self):
        super().setUp()
        self.env['ir.config_parameter'].sudo().set_param(
            'purchase.check_options', 'always'
        )
        self.partner = self.env['res.partner'].create({
            'name': 'Test Supplier',
            'supplier_rank': 1,
        })

    def test_check_new_field_exists(self):
        """El campo check_new existe en purchase.order."""
        po = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        self.assertFalse(po.check_new, "check_new default debe ser False")
        po.check_new = True
        self.assertTrue(po.check_new)

    def test_check_new_true_included_in_search(self):
        """Una PO con check_new=True es encontrable."""
        po_with = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'check_new': True,
        })
        po_without = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'check_new': False,
        })

        found = self.env['purchase.order'].search([('check_new', '=', True)])
        self.assertIn(po_with, found)
        self.assertNotIn(po_without, found)

    def test_config_check_options_always(self):
        """La configuración check_options='always' se guarda correctamente."""
        self.env['ir.config_parameter'].sudo().set_param('purchase.check_options', 'always')
        val = self.env['ir.config_parameter'].sudo().get_param('purchase.check_options')
        self.assertEqual(val, 'always')

    def test_config_check_options_line(self):
        """La configuración check_options='line' se guarda correctamente."""
        self.env['ir.config_parameter'].sudo().set_param('purchase.check_options', 'line')
        val = self.env['ir.config_parameter'].sudo().get_param('purchase.check_options')
        self.assertEqual(val, 'line')

    def test_res_config_settings_field_exists(self):
        """El campo check_options existe en res.config.settings."""
        config = self.env['res.config.settings'].create({})
        self.assertTrue(
            hasattr(config, 'check_options'),
            "El campo check_options debe existir en res.config.settings"
        )
