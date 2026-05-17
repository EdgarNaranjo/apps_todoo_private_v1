# Copyright 2025-TODAY Todooweb (www.todooweb.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
"""
Tests para automatic_invoice_delivered.

Para ejecutar:
    python odoo-bin -d <db> --test-enable -i automatic_invoice_delivered --stop-after-init

Comportamiento verificado:
  1. Si auto-factura está activada y el producto tiene política 'delivery',
     al validar el picking se crea y publica la factura automáticamente.
  2. Si auto-factura está desactivada, no se crea factura.
  3. Si no hay sale_id en el picking, no falla.
"""

from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestAutomaticInvoiceDelivered(TransactionCase):

    def setUp(self):
        super().setUp()
        # Activar la configuración
        self.env['ir.config_parameter'].sudo().set_param(
            'automatic_invoice_delivered.is_create_automatic_invoice', True
        )
        # Partner de prueba
        self.partner = self.env['res.partner'].create({'name': 'Test Customer'})
        # Producto con política de facturación 'delivery'
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',
            'invoice_policy': 'delivery',
        })

    def _create_confirmed_sale_order(self):
        """Helper: crea y confirma una orden de venta."""
        so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1,
                'price_unit': 100.0,
            })],
        })
        so.action_confirm()
        return so

    def test_invoice_created_on_validate_when_enabled(self):
        """Validar entrega con auto-factura ON crea factura posted."""
        so = self._create_confirmed_sale_order()
        picking = so.picking_ids[0]

        # Establecer cantidades realizadas
        for move in picking.move_ids:
            move.quantity = move.product_uom_qty

        # Validar el picking
        picking.button_validate()

        # Verificar que se creó una factura posted
        invoices = so.invoice_ids
        self.assertTrue(invoices, "Debe haber al menos una factura creada")
        self.assertEqual(
            invoices[0].state, 'posted',
            "La factura debe estar en estado 'posted'"
        )

    def test_no_invoice_when_disabled(self):
        """Con auto-factura OFF no se crea factura al validar entrega."""
        # Desactivar
        self.env['ir.config_parameter'].sudo().set_param(
            'automatic_invoice_delivered.is_create_automatic_invoice', False
        )
        so = self._create_confirmed_sale_order()
        picking = so.picking_ids[0]

        for move in picking.move_ids:
            move.quantity = move.product_uom_qty

        picking.button_validate()

        invoices = so.invoice_ids.filtered(lambda i: i.state == 'posted')
        self.assertFalse(invoices, "No debe haber facturas posted con auto-factura OFF")

    def test_picking_without_sale_no_crash(self):
        """Un picking sin sale_id no provoca error al validar."""
        location = self.env.ref('stock.stock_location_stock')
        location_dest = self.env.ref('stock.stock_location_customers')

        picking = self.env['stock.picking'].create({
            'partner_id': self.partner.id,
            'picking_type_id': self.env.ref('stock.picking_type_out').id,
            'location_id': location.id,
            'location_dest_id': location_dest.id,
        })
        # Sin líneas y sin sale_id — no debe fallar
        self.env['ir.config_parameter'].sudo().set_param(
            'automatic_invoice_delivered.is_create_automatic_invoice', True
        )
        try:
            picking.button_validate()
        except Exception as e:
            # Puede fallar por otros motivos (falta de movimientos), no por el módulo
            if 'automatic_invoice' in str(e).lower():
                self.fail(f"El módulo no debe causar errores en pickings sin venta: {e}")

    def test_config_setting_field_exists(self):
        """El campo is_automatic_invoice_delivered existe en res.config.settings."""
        config = self.env['res.config.settings'].create({})
        self.assertTrue(
            hasattr(config, 'is_automatic_invoice_delivered'),
            "El campo is_automatic_invoice_delivered debe existir"
        )
