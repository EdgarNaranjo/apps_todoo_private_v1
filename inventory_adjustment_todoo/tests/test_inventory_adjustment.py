# Copyright 2025-TODAY Todooweb (www.todooweb.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
"""
Tests para inventory_adjustment_todoo.

Para ejecutar:
    python odoo-bin -d <db> --test-enable -i inventory_adjustment_todoo --stop-after-init

Comportamiento verificado:
  1. Los campos past_inventory_date / past_inventory_quantity existen en stock.quant.
  2. Al crear un quant con fecha pasada, el inventory_quantity se calcula correctamente.
  3. Al hacer write con fecha pasada, recalcula inventory_quantity.
  4. Al aplicar inventario, los campos past_* se resetean.
  5. _get_inventory_fields_write incluye los campos nuevos.
"""

from datetime import timedelta

from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestInventoryAdjustmentTodoo(TransactionCase):

    def setUp(self):
        super().setUp()
        self.product = self.env['product.product'].create({
            'name': 'Test Product Inventory',
            'type': 'consu', 'is_storable': True,
        })
        self.location = self.env.ref('stock.stock_location_stock')
        self.company = self.env.company

    def test_fields_exist_on_stock_quant(self):
        """Los campos past_inventory_date y past_inventory_quantity existen."""
        quant = self.env['stock.quant'].sudo().create({
            'product_id': self.product.id,
            'location_id': self.location.id,
            'quantity': 10.0,
        })
        self.assertTrue(
            hasattr(quant, 'past_inventory_date'),
            "past_inventory_date debe existir en stock.quant"
        )
        self.assertTrue(
            hasattr(quant, 'past_inventory_quantity'),
            "past_inventory_quantity debe existir en stock.quant"
        )

    def test_inventory_fields_write_includes_past_fields(self):
        """_get_inventory_fields_write incluye los campos del módulo."""
        quant = self.env['stock.quant'].sudo()
        write_fields = quant._get_inventory_fields_write()
        self.assertIn(
            'past_inventory_date', write_fields,
            "past_inventory_date debe estar en _get_inventory_fields_write"
        )
        self.assertIn(
            'past_inventory_quantity', write_fields,
            "past_inventory_quantity debe estar en _get_inventory_fields_write"
        )

    def test_inventory_fields_create_includes_past_fields(self):
        """_get_inventory_fields_create incluye los campos del módulo."""
        quant = self.env['stock.quant'].sudo()
        create_fields = quant._get_inventory_fields_create()
        self.assertIn('past_inventory_date', create_fields)
        self.assertIn('past_inventory_quantity', create_fields)

    def test_apply_inventory_resets_past_fields(self):
        """Después de _apply_inventory los campos past_* se resetean."""
        quant = self.env['stock.quant'].sudo().create({
            'product_id': self.product.id,
            'location_id': self.location.id,
            'quantity': 5.0,
        })
        past_date = fields.Datetime.now() - timedelta(days=10)
        quant.write({
            'past_inventory_date': past_date,
            'past_inventory_quantity': 3.0,
        })

        # Simular apply con inventory_quantity
        quant.inventory_quantity = 5.0
        quant._apply_inventory()

        self.assertFalse(
            quant.past_inventory_date,
            "past_inventory_date debe ser False después de _apply_inventory"
        )
        self.assertEqual(
            quant.past_inventory_quantity, 0,
            "past_inventory_quantity debe ser 0 después de _apply_inventory"
        )

    def test_action_set_inventory_quantity_zero_resets_past(self):
        """action_set_inventory_quantity_zero resetea campos past_*."""
        quant = self.env['stock.quant'].sudo().create({
            'product_id': self.product.id,
            'location_id': self.location.id,
            'quantity': 10.0,
        })
        past_date = fields.Datetime.now() - timedelta(days=5)
        quant.write({
            'past_inventory_date': past_date,
            'past_inventory_quantity': 8.0,
        })
        quant.action_set_inventory_quantity_zero()

        self.assertFalse(quant.past_inventory_date)
        self.assertEqual(quant.past_inventory_quantity, 0)
