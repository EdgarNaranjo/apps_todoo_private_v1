# Copyright 2024-TODAY Todooweb (www.todooweb.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.model
    def create(self, vals_list):
        res = super(ResCompany, self).create(vals_list)
        # When a new company is created should be created the sequence necessary to generate the task sequence
        self.env['ir.sequence'].sudo().create({
            'name': 'OTs ({})'.format(res.name),
            'code': 'project.task',
            'padding': 5,
            'prefix': 'OT/%(y)s/',
            'use_date_range': True,
            'company_id': res.id
        })
        return res


class IrSequence(models.Model):
    _inherit = 'ir.sequence'

    def unlink(self):
        for rec in self:
            if rec.code == 'project.task' and rec.company_id:
                # Block message to avoid some necessary sequence could be delete manually
                raise ValidationError(_("Sorry this sequence can't be deleted because it's necessary for"
                                        "task's sequence generation. If it's necessary please contact with Admin"))
        return super().unlink()


class ProductProduct(models.Model):
    _inherit = 'product.product'

    location_info = fields.Text(
        string='Location Info'
    )

    @api.onchange('name')
    def get_name_short(self):
        for record in self:
            if record.name:
                record.name_short = record.name


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    name_short = fields.Char(
        string='Short name'
    )
    can_movility = fields.Boolean(string="It is displacement")

    @api.onchange('name')
    def get_name_short(self):
        for record in self:
            if record.name:
                record.name_short = record.name


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    material_id = fields.Many2one(
        string='Material',
        comodel_name='ot.material.line'
    )
    location_id = fields.Many2one(
        related='material_id.location_id'
    )
    lot_id = fields.Many2one(
        related='material_id.lot_id'
    )

    @api.constrains('state')
    def _check_state_line(self):
        for record in self:
            if record.state == 'cancel':
                record.material_id.state = 'block'

    @api.constrains('product_template_id', 'product_id')
    def check_short_name_by_product(self):
        for record in self:
            if record.product_template_id and record.product_template_id.name_short:
                record.name = record.product_template_id.name_short
            elif record.product_id and record.product_id.name_short:
                record.name = record.product_id.name_short

    def _purchase_service_create(self, quantity=False):
        """ On Sales Order confirmation, some lines (services ones) can create a purchase order line and maybe a purchase order.
            If a line should create a RFQ, it will check for existing PO. If no one is find, the SO line will create one, then adds
            a new PO line. The created purchase order line will be linked to the SO line.
            :param quantity: the quantity to force on the PO line, expressed in SO line UoM
        """
        PurchaseOrder = self.env['purchase.order']
        supplier_po_map = {}
        sale_line_purchase_map = {}
        for line in self:
            line = line.with_company(line.company_id)
            # determine vendor of the order (take the first matching company and product)
            suppliers = line.product_id._select_seller(quantity=line.product_uom_qty, uom_id=line.product_uom)
            if not suppliers:
                raise UserError(_("There is no vendor associated to the product %s. Please define a vendor for this product.") % (line.product_id.display_name,))
            supplierinfo = suppliers[0]
            partner_supplier = supplierinfo.partner_id

            # determine (or create) PO
            purchase_order = supplier_po_map.get(partner_supplier.id)
            if not purchase_order:
                purchase_order = PurchaseOrder.search([
                    ('partner_id', '=', partner_supplier.id),
                    ('state', '=', 'draft'),
                    ('company_id', '=', line.company_id.id),
                    ('check_service', '=', True)
                ], limit=1)
            if not purchase_order:
                values = line._purchase_service_prepare_order_values(supplierinfo)
                purchase_order = PurchaseOrder.with_context(mail_create_nosubscribe=True).create(values)
            else:  # update origin of existing PO
                so_name = line.order_id.name
                origins = []
                if purchase_order.origin:
                    origins = purchase_order.origin.split(', ') + origins
                if so_name not in origins:
                    origins += [so_name]
                    purchase_order.write({
                        'origin': ', '.join(origins)
                    })
            supplier_po_map[partner_supplier.id] = purchase_order

            # add a PO line to the PO
            values = line._purchase_service_prepare_line_values(purchase_order, quantity=quantity)
            purchase_line = line.env['purchase.order.line'].create(values)

            # link the generated purchase to the SO line
            sale_line_purchase_map.setdefault(line, line.env['purchase.order.line'])
            sale_line_purchase_map[line] |= purchase_line
        return sale_line_purchase_map


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _compute_show_reset_to_draft_button(self):
        super()._compute_show_reset_to_draft_button()
        for move in self:
            if move.sudo().line_ids.stock_valuation_layer_ids:
                move.show_reset_to_draft_button = True


class StockLocation(models.Model):
    _inherit = 'stock.location'

    is_material = fields.Boolean('Material location?', help='Default location for external services.', copy=False)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    task_id = fields.Many2one('project.task', 'Work Order')
    picking_reference = fields.Char('Ref. Picking')

    @api.constrains('state', 'task_id')
    def check_material_line_in_task(self):
        env_tracking = self.env['tracking.line']
        for record in self:
            list_moves = []
            if record.state == 'done':
                if record.task_id and record.picking_type_id.code == 'incoming':
                    materials = record.task_id.ot_material_ids
                    if record.move_ids:
                        for line in record.move_ids:
                            material = materials.filtered(lambda e: e.move_line_id == line.origin_returned_move_id)
                            list_moves.append({
                                'line_origin': line,
                                'line_return': line.origin_returned_move_id,
                                'material': material
                            })
                if list_moves:
                    for item in list_moves:
                        if not env_tracking.search([('line_id', '=', item['material'].id)]):
                            if item['line_origin'].product_qty == item['line_return'].product_qty:
                                val_state = 'full'
                            else:
                                val_state = 'partial'
                            dict_tracking = {
                                'line_id': item['material'].id,
                                'picking_id': item['line_origin'].picking_id.id,
                                'picking_return_id': item['line_return'].picking_id.id,
                                'product_origin_qty': item['line_origin'].product_qty,
                                'product_dest_qty': item['line_return'].product_qty,
                                'task_id': record.task_id.id,
                                'state': val_state
                            }
                            obj_tracking = env_tracking.create(dict_tracking)
                            if obj_tracking:
                                record.task_id.message_post(body=_('Created tracking.'))


class StockMove(models.Model):
    _inherit = "stock.move"

    def _assign_picking(self):
        env_picking = self.env['stock.picking']
        picking_type_id = self.env['stock.picking.type'].search([('code', '=', 'internal')])
        res = super(StockMove, self)._assign_picking()
        move_filtered = self.filtered(lambda e: e.sale_line_id.location_id and e.location_id != e.sale_line_id.location_id)
        if move_filtered:
            for move in move_filtered:
                obj_type = picking_type_id.filtered(lambda e: e.default_location_src_id == e.default_location_dest_id and e.warehouse_id == move.sale_line_id.location_id.warehouse_id)
                if obj_type:
                    move_copy = move.copy({
                        'picking_type_id': obj_type[0].id,
                        'location_id': move.sale_line_id.location_id.id,
                        'location_dest_id': move.location_id.id,
                        'name': '',
                        'picking_id': False,
                        'picking_code': obj_type[0].code
                    })
                    move_copy.picking_type_id = obj_type[0].id
                    move_copy.picking_code = obj_type[0].code
                    new_picking = False
                    picking = move_copy._search_picking_for_assignation()
                    if not picking:
                        new_picking = True
                        picking = env_picking.create(move_copy._get_new_picking_values())
                    move_copy.write({'picking_id': picking.id})
                    move_copy._assign_picking_post_process(new=new_picking)
        return res


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    lot_task_id = fields.Many2one('stock.lot', 'Lot (OT)')

    @api.model_create_multi
    def create(self, vals_list):
        env_ot_id = self.env['ot.material.line']
        for vals in vals_list:
            if vals.get('move_id'):
                move_id = self.env['stock.move'].browse(vals['move_id'])
                obj_ot_line = env_ot_id.search([('move_line_id', '=', move_id.id), ('lot_id', '!=', False)], limit=1)
                if move_id.sale_line_id:
                    vals['lot_task_id'] = move_id.sale_line_id.lot_id.id
                else:
                    if obj_ot_line:
                        vals['lot_task_id'] = obj_ot_line.lot_id.id
        return super().create(vals_list)


class ProjectTaskType(models.Model):
    _inherit = 'project.task.type'

    is_last = fields.Boolean('Last stage', help='Determine the last stage')
    is_locked = fields.Boolean('Locked', help='Block for a technical personnel')
    is_required = fields.Boolean('Required', help='Required for use on Equipment associated with an OT')


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    check_process = fields.Boolean('Signed', help='Indicates that it was processed after being signed by the client')


class MailTemplate(models.Model):
    _inherit = "mail.template"

    check_service = fields.Boolean('External services', help='Template only for external service customization')


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    def _action_send_mail(self, auto_commit=False):
        if self.model == 'project.task':
            self = self.with_context(mailing_document_based=True)
            task_id = self.env.context.get('default_res_ids', [None])[0]
            if task_id:
                obj_task = self.env['project.task'].browse(task_id)
                if obj_task.exists():
                    material_lines = self.env['ot.material.line'].search([('task_id', '=', obj_task.id), ('state', '=', 'process')])
                    operation_lines = self.env['operation.line'].search([('task_id', '=', obj_task.id), ('state', '=', 'process')])
                    if material_lines:
                        material_lines.write({'check_send': True, 'state': 'done'})
                    if operation_lines:
                        operation_lines.write({'check_send': True})
                    obj_task.count_doc_sign += 1
                    if self.attachment_ids:
                        sign_count_str = f' ({obj_task.count_doc_sign})'
                        for attachment in self.attachment_ids:
                            name, ext = attachment.name.rsplit('.', 1)
                            attachment.write({'name': f'{name}{sign_count_str}.{ext}'})
                        obj_task.message_post(body='Sent attached to client.', attachment_ids=self.attachment_ids.ids)
        return super(MailComposeMessage, self)._action_send_mail(auto_commit=auto_commit)
