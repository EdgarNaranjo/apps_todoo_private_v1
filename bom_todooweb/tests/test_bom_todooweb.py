# Copyright 2025-TODAY Todooweb (www.todooweb.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""
Tests para bom_todooweb.

Para ejecutar:
    python odoo-bin -d <db> --test-enable -i bom_todooweb --stop-after-init

Comportamiento verificado:
  1. El campo count_lines en mrp.bom se calcula correctamente.
  2. count_lines aumenta al añadir líneas a la BoM.
  3. count_lines disminuye al eliminar líneas.
"""

from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestBomTodooweb(TransactionCase):

    def setUp(self):
        super().setUp()
        self.product_parent = self.env['product.product'].create({
            'name': 'Parent Product',
            'type': 'consu', 'is_storable': True,
        })
        self.component_a = self.env['product.product'].create({
            'name': 'Component A',
            'type': 'consu', 'is_storable': True,
        })
        self.component_b = self.env['product.product'].create({
            'name': 'Component B',
            'type': 'consu', 'is_storable': True,
        })

    def test_count_lines_field_exists(self):
        """El campo count_lines existe en mrp.bom."""
        bom = self.env['mrp.bom'].create({
            'product_tmpl_id': self.product_parent.product_tmpl_id.id,
        })
        self.assertTrue(
            hasattr(bom, 'count_lines'),
            "count_lines debe existir en mrp.bom"
        )

    def test_count_lines_empty_bom(self):
        """Una BoM sin líneas tiene count_lines = 0."""
        bom = self.env['mrp.bom'].create({
            'product_tmpl_id': self.product_parent.product_tmpl_id.id,
        })
        self.assertEqual(bom.count_lines, 0, "BoM sin líneas debe tener count_lines=0")

    def test_count_lines_increases_with_lines(self):
        """count_lines refleja el número real de líneas."""
        bom = self.env['mrp.bom'].create({
            'product_tmpl_id': self.product_parent.product_tmpl_id.id,
            'bom_line_ids': [
                (0, 0, {'product_id': self.component_a.id, 'product_qty': 1}),
                (0, 0, {'product_id': self.component_b.id, 'product_qty': 2}),
            ],
        })
        self.assertEqual(bom.count_lines, 2, "count_lines debe ser 2 con 2 líneas")

    def test_count_lines_updates_when_line_added(self):
        """count_lines se actualiza al añadir una línea."""
        bom = self.env['mrp.bom'].create({
            'product_tmpl_id': self.product_parent.product_tmpl_id.id,
            'bom_line_ids': [
                (0, 0, {'product_id': self.component_a.id, 'product_qty': 1}),
            ],
        })
        self.assertEqual(bom.count_lines, 1)

        bom.write({
            'bom_line_ids': [(0, 0, {'product_id': self.component_b.id, 'product_qty': 1})]
        })
        self.assertEqual(bom.count_lines, 2, "count_lines debe ser 2 tras añadir línea")

    def test_count_lines_updates_when_line_removed(self):
        """count_lines se actualiza al eliminar una línea."""
        bom = self.env['mrp.bom'].create({
            'product_tmpl_id': self.product_parent.product_tmpl_id.id,
            'bom_line_ids': [
                (0, 0, {'product_id': self.component_a.id, 'product_qty': 1}),
                (0, 0, {'product_id': self.component_b.id, 'product_qty': 1}),
            ],
        })
        self.assertEqual(bom.count_lines, 2)

        line_to_remove = bom.bom_line_ids[0]
        bom.write({'bom_line_ids': [(2, line_to_remove.id)]})
        self.assertEqual(bom.count_lines, 1, "count_lines debe ser 1 tras eliminar línea")
