# Copyright 2025-TODAY Todooweb (www.todooweb.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
import datetime
from collections import defaultdict

from odoo import models, fields, _, api
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, is_html_empty


class RepairOrder(models.Model):
    _inherit = 'repair.order'

    def _default_repair_reason(self):
        param = self.env['ir.config_parameter'].sudo().get_param('order_repair_todoo.reason_id')
        return int(param) if param and param.isdigit() else False

    def _default_repair_type(self):
        param = self.env['ir.config_parameter'].sudo().get_param('order_repair_todoo.repair_type_id')
        return int(param) if param and param.isdigit() else False

    def _default_invoice_method(self):
        return self.env['ir.config_parameter'].sudo().get_param('order_repair_todoo.invoice_method', 'none')

    def _default_internal_state(self):
        return self.env['internal.state'].search([], limit=1)

    duration = fields.Char(
        string="Repair Duration",
        help="Duration in hours and minutes.", default='00d-00h-00m'
    )
    picking_ids = fields.Many2many(
        comodel_name="stock.picking",
        string="Transfers",
        copy=False
    )
    transfer_count = fields.Integer(
        'Count transfer',
        compute='get_count_transfer'
    )
    check_in = fields.Boolean(
        'Incoming picking',
        compute='_get_related_pickings'
    )
    check_out = fields.Boolean(
        'Outgoing picking',
        compute='_get_related_pickings'
    )
    license_vin = fields.Char(
        'License/VIN',
        required=True,
        tracking=1,
        states={'2binvoiced': [('readonly', True)], 'done': [('readonly', True)], 'cancel': [('readonly', True)]}
    )
    technical_sheet = fields.Binary(
        'Technical sheet',
        attachment=True)
    unit = fields.Selection([
        ('ecu', 'ECU'),
        ('bodywork', 'Bodywork unit'),
        ('abs', 'ABS'),
        ('instrument', 'Instrument panel'),
        ('exchange', 'Unit of exchange'),
        ('airbag', 'Airbag'),
        ('immobilizer', 'Immobilizer'),
        ('other', 'Other units'),
    ], string='Unit', required=True, tracking=1,
        states={'2binvoiced': [('readonly', True)], 'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    reference = fields.Char(
        'Reference',
        help='Unit reference',
        required=True, tracking=1,
        states={'2binvoiced': [('readonly', True)], 'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    tag_attachment = fields.Binary(
        'Unit Tag',
        attachment=True)
    vehicle_starts = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string='Vehicle starts', required=True, tracking=1,
        states={'2binvoiced': [('readonly', True)], 'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    communication_unit = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string='Communication unit', required=True, tracking=1,
        states={'2binvoiced': [('readonly', True)], 'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    fault_code = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string='Fault code', required=True, tracking=1,
        states={'2binvoiced': [('readonly', True)], 'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    diagnosis_attachment = fields.Binary(
        'Diagnosis attachment',
        attachment=True)
    delete_codes = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string='Delete codes', tracking=1,
        states={'2binvoiced': [('readonly', True)], 'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    symptoms = fields.Text('Symptoms', required=True,
                           states={'2binvoiced': [('readonly', True)], 'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    continuous_failure = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string='Continuous failure', tracking=1,
        states={'2binvoiced': [('readonly', True)], 'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    procedures_performed = fields.Text(
        'Procedures performed', help='MEASUREMENTS, CHANGING OTHER PARTS OF THE SYSTEM, DIAGNOSTIC TESTS, READING OF '
                                     'ACTUAL VALUES, ETC.')
    antecedents = fields.Text(
        'Antecedents', help='SITUATIONS OR ACTIONS THAT HAVE BEEN PERFORMED PREVIOUSLY RELATED TO THIS FAULT, '
                            'SUCH AS HUMIDITY, MANIPULATIONS, CODING, ETC.')
    repair_reason_id = fields.Many2one(
        'repair.reason',
       'Repair reason',
        tracking=1,
        default=_default_repair_reason,
       states={'2binvoiced': [('readonly', True)], 'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    repair_type_id = fields.Many2one(
        'repair.type',
       'Repair Type',
       tracking=1,
       default=_default_repair_type,
       states={'2binvoiced': [('readonly', True)], 'done': [('readonly', True)], 'cancel': [('readonly', True)]}
    )
    parent_id = fields.Many2one(
       'repair.order',
       'Repair parent',
       copy=False
    )
    child_ids = fields.One2many(
       'repair.order',
       'parent_id',
       'Repair copied'
    )
    invoice_method = fields.Selection([
       ("none", "No Invoice"),
       ("b4repair", "Before Repair"),
       ("after_repair", "After Repair")
    ], string="Invoice Method",
       default=_default_invoice_method,
       index=True, readonly=True, required=True, states={'draft': [('readonly', False)]},
       help='Selecting \'Before Repair\' or \'After Repair\' will allow you to generate invoice before or '
            'after the repair is done respectively. \'No invoice\' means you don\'t want to generate invoice '
            'for this repair order.')
    canal = fields.Selection([
        ('web', 'Web'),
        ('call', 'Call'),
        ('chat', 'Chat'),
        ('mail', 'Email'),
        ('app', 'App Mobile'),
        ('pwa', 'PWA'),
        ('website', 'Website')
    ], string='Canal', default='web')
    show_in = fields.Boolean(
       'Show in',
       compute='get_show_in'
    )
    show_out = fields.Boolean(
       'Show out',
       compute='get_show_in'
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pick', 'Pick'),
        ('confirmed', 'Confirmed'),
        ('ready', 'Ready to Repair'),
        ('under_repair', 'Under Repair'),
        ('2binvoiced', 'To be Invoiced'),
        ('done', 'Repaired'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='draft')
    internal_state_ids = fields.Many2many(
       'internal.state',
       'rel_repair_internal',
       'repair_id',
       'internal_id',
       'Internal state',
       tracking=1,
       default=_default_internal_state
    )
    check_child = fields.Boolean(
       'Have child',
       compute='_check_child'
    )
    count_child = fields.Integer(
       'Count child',
       compute='_get_child_repair'
    )
    vehicle_brand_id = fields.Many2one(
        'vehicle.brand',
        'Brand',
        required=True,
        tracking=1,
        states={'2binvoiced': [('readonly', True)], 'done': [('readonly', True)], 'cancel': [('readonly', True)]}
    )
    vehicle_model_id = fields.Many2one(
       'vehicle.model',
       'Model',
       required=True,
       tracking=1,
       states={'2binvoiced': [('readonly', True)], 'done': [('readonly', True)], 'cancel': [('readonly', True)]}
    )
    vehicle_serial_id = fields.Many2one(
       'vehicle.serial',
       'Serial',
       required=True,
       tracking=1,
       states={'2binvoiced': [('readonly', True)], 'done': [('readonly', True)], 'cancel': [('readonly', True)]}
    )

    @api.depends('child_ids')
    def _check_child(self):
        for record in self:
            record.check_child = False
            if record.child_ids:
                record.check_child = True

    @api.depends('child_ids')
    def _get_child_repair(self):
        for record in self:
            record.count_child = len(record.child_ids)

    def action_open_child(self):
        action = self.env["ir.actions.actions"]._for_xml_id('repair.action_repair_order_tree')
        action['domain'] = [('id', 'in', self.child_ids.ids)]
        action['context'] = {'create': False}
        return action

    @api.depends('picking_ids')
    def _get_related_pickings(self):
        for record in self:
            record.check_in, record.check_out = False, False
            if record.picking_ids:
                if record.picking_ids.filtered(
                        lambda e: e.picking_type_id.code == 'incoming' and e.picking_type_id.return_picking_type_id and
                                  e.state in ['confirmed', 'assigned', 'done']):
                    record.check_in = True
                if record.picking_ids.filtered(
                        lambda e: e.picking_type_id.code == 'outgoing' and e.picking_type_id.return_picking_type_id and
                                  e.state in ['confirmed', 'assigned', 'done']):
                    record.check_out = True
            else:
                record.check_out = True

    def action_open_transfers(self):
        action = self.env["ir.actions.actions"]._for_xml_id('stock.stock_picking_action_picking_type')
        action['domain'] = [('id', 'in', self.picking_ids.ids)]
        action['context'] = {'create': False}
        return action

    @api.depends('picking_ids')
    def get_count_transfer(self):
        for record in self:
            record.transfer_count = len(record.picking_ids)

    def action_repair_cancel_draft(self):
        if self.filtered(lambda repair: repair.state != 'cancel'):
            raise UserError(_("Repair must be canceled in order to reset it to draft."))
        state, state_line = 'draft', 'draft'
        if self.check_in and not self.check_out:
            if self.picking_ids.filtered(lambda e: e.picking_type_code == 'incoming' and e.state == 'done'):
                state = 'confirmed'
            else:
                state = 'pick'
        elif self.check_in and self.check_out:
            state, state_line = 'confirmed', 'confirmed'
        self.mapped('operations').write({'state': state_line})
        return self.write({'state': state, 'invoice_id': False})

    def action_picking(self):
        if self.check_in and self.check_out:
            raise UserError(
                _("You cannot generate new delivery notes if the entry and exit already exist in the 'Done' status."))
        action = self.env["ir.actions.actions"]._for_xml_id('order_repair_todoo.action_stock_picking_wizard')
        return action

    @api.depends('picking_ids')
    def get_show_in(self):
        for record in self:
            record.show_in = False
            record.show_out = False
            if record.picking_ids:
                if record.picking_ids.filtered(
                        lambda e: e.picking_type_code == 'incoming' and e.state not in ['done', 'cancel']):
                    record.show_in = True
                if record.picking_ids.filtered(
                        lambda e: e.picking_type_code == 'outgoing' and e.state not in ['done', 'cancel']):
                    record.show_out = True

    @api.constrains('internal_state_ids')
    def _check_internal_state_ids(self):
        for record in self:
            if len(record.internal_state_ids) > 1:
                raise ValidationError(
                    _("You can only select one category in the same repair order.\n If the error persists, contact an administrator."))
            elif record.internal_state_ids:
                state_names = ', '.join(record.internal_state_ids.mapped('name'))
                record.message_post(
                    body=_("Internal State set to: <b style='color: #0080A4;'>%s</b>") % state_names
                )

    @api.constrains('state')
    def check_duration_days(self):
        for record in self:
            record.duration = '00d-00h-00m'
            if record.state in ['under_repair', '2binvoiced', 'done', 'cancel']:
                diff = datetime.datetime.now() - record.create_date
                days = diff.days
                hours, rest = divmod(diff.seconds, 3600)
                minutes, _ = divmod(rest, 60)
                record.duration = f'{days}d-{hours}h-{minutes}m'

    @api.depends('company_id')
    def _compute_location_id(self):
        param_id = self.env['ir.config_parameter'].sudo().get_param('order_repair_todoo.location_id')
        for order in self:
            location = False
            if param_id and str(param_id).isdigit():
                location_candidate = self.env['stock.location'].browse(int(param_id))
                if location_candidate.exists() and (
                        not location_candidate.company_id or location_candidate.company_id == order.company_id):
                    location = location_candidate
            if not location and order.company_id:
                warehouse = self.env['stock.warehouse'].search([('company_id', '=', order.company_id.id)], limit=1)
                location = warehouse.lot_stock_id if warehouse else False
            order.location_id = location

    def action_validate(self):
        res = super(RepairOrder, self).action_validate()
        if self.filtered(lambda e: not e.check_in):
            raise UserError(_("Repair must be confirmed before generate 'incoming operation'.\n "
                              "Go to the 'Action' section and 'Generate incoming picking' of the product to be repaired."))
        return res

    def action_repair_start(self):
        res = super(RepairOrder, self).action_repair_start()
        if self.filtered(lambda e: not e.check_in):
            raise UserError(_("Repair must be confirmed before generate 'incoming operation'.\n "
                              "Go to the 'Action' section and 'Generate incoming picking' of the product to be repaired."))
        return res

    def action_repair_end(self):
        res = super(RepairOrder, self).action_repair_end()
        if self.filtered(lambda e: not e.check_out):
            raise UserError(_("Repair must be finished before generate 'outgoing operation'.\n "
                              "Go to the 'Action' section and 'Generate outgoing picking' of the product to be repaired."))
        return res

    def action_repair_confirm(self):
        self._check_company()
        self.operations._check_company()
        self.fees_lines._check_company()
        before_repair = self.filtered(lambda repair: repair.invoice_method == 'b4repair')
        before_repair.write({'state': '2binvoiced'})
        to_confirm = self - before_repair
        to_confirm_operations = to_confirm.mapped('operations')
        to_confirm_operations.write({'state': 'confirmed'})
        to_confirm.write({'state': 'confirmed'})
        return True

    @api.depends(
        'operations.price_unit', 'operations.product_uom_qty', 'operations.product_id', 'operations.discount',
        'fees_lines.price_unit', 'fees_lines.product_uom_qty', 'fees_lines.product_id', 'fees_lines.discount',
        'pricelist_id.currency_id', 'partner_id'
    )
    def _amount_tax(self):
        for order in self:
            val = 0.0
            currency = order.pricelist_id.currency_id or self.env.company.currency_id
            for operation in order.operations:
                if operation.tax_id:
                    price_discounted = operation.price_unit * (1 - (operation.discount or 0.0) / 100.0)
                    tax_calculate = operation.tax_id.compute_all(
                        price_discounted, currency, operation.product_uom_qty,
                        operation.product_id, order.partner_id
                    )
                    val += sum(t['amount'] for t in tax_calculate['taxes'])
            for fee in order.fees_lines:
                if fee.tax_id:
                    price_discounted = fee.price_unit * (1 - (fee.discount or 0.0) / 100.0)
                    tax_calculate = fee.tax_id.compute_all(
                        price_discounted, currency, fee.product_uom_qty,
                        fee.product_id, order.partner_id
                    )
                    val += sum(t['amount'] for t in tax_calculate['taxes'])
            order.amount_tax = currency.round(val)

    def _create_invoices(self, group=False):
        """ Creates invoice(s) for repair order.
        @param group: It is set to true when group invoice is to be generated.
        @return: Invoice Ids.
        """
        grouped_invoices_vals = {}
        repairs = self.filtered(lambda repair: repair.state not in ('draft', 'cancel')
                                               and not repair.invoice_id
                                               and repair.invoice_method != 'none')
        for repair in repairs:
            repair = repair.with_company(repair.company_id)
            partner_invoice = repair.partner_invoice_id or repair.partner_id
            if not partner_invoice:
                raise UserError(_('You have to select an invoice address in the repair form.'))

            narration = repair.quotation_notes
            currency = repair.pricelist_id.currency_id
            company = repair.env.company

            if (partner_invoice.id, currency.id, company.id) not in grouped_invoices_vals:
                grouped_invoices_vals[(partner_invoice.id, currency.id, company.id)] = []
            current_invoices_list = grouped_invoices_vals[(partner_invoice.id, currency.id, company.id)]

            if not group or len(current_invoices_list) == 0:
                fpos = self.env['account.fiscal.position']._get_fiscal_position(partner_invoice,
                                                                                delivery=repair.address_id)
                invoice_vals = {
                    'move_type': 'out_invoice',
                    'partner_id': partner_invoice.id,
                    'partner_shipping_id': repair.address_id.id,
                    'currency_id': currency.id,
                    'narration': narration if not is_html_empty(narration) else '',
                    'invoice_origin': repair.name,
                    'repair_ids': [(4, repair.id)],
                    'invoice_line_ids': [],
                    'fiscal_position_id': fpos.id
                }
                if partner_invoice.property_payment_term_id:
                    invoice_vals['invoice_payment_term_id'] = partner_invoice.property_payment_term_id.id
                current_invoices_list.append(invoice_vals)
            else:
                # if group == True: concatenate invoices by partner and currency
                invoice_vals = current_invoices_list[0]
                invoice_vals['invoice_origin'] += ', ' + repair.name
                invoice_vals['repair_ids'].append((4, repair.id))
                if not is_html_empty(narration):
                    if is_html_empty(invoice_vals['narration']):
                        invoice_vals['narration'] = narration
                    else:
                        invoice_vals['narration'] += Markup('<br/>') + narration

            # Create invoice lines from operations.
            for operation in repair.operations.filtered(lambda op: op.type == 'add'):
                if group:
                    name = repair.name + '-' + operation.name
                else:
                    name = operation.name

                account = operation.product_id.product_tmpl_id.get_product_accounts(fiscal_pos=fpos)['income']
                if not account:
                    raise UserError(_('No account defined for product "%s".', operation.product_id.name))

                invoice_line_vals = {
                    'name': name,
                    'account_id': account.id,
                    'quantity': operation.product_uom_qty,
                    'tax_ids': [(6, 0, operation.tax_id.ids)],
                    'product_uom_id': operation.product_uom.id,
                    'price_unit': operation.price_unit,
                    'product_id': operation.product_id.id,
                    'repair_line_ids': [(4, operation.id)],
                    'discount': operation.discount
                }

                if currency == company.currency_id:
                    balance = -(operation.product_uom_qty * operation.price_unit)
                    invoice_line_vals.update({
                        'debit': balance > 0.0 and balance or 0.0,
                        'credit': balance < 0.0 and -balance or 0.0,
                    })
                else:
                    amount_currency = -(operation.product_uom_qty * operation.price_unit)
                    balance = currency._convert(amount_currency, company.currency_id, company, fields.Date.today())
                    invoice_line_vals.update({
                        'amount_currency': amount_currency,
                        'debit': balance > 0.0 and balance or 0.0,
                        'credit': balance < 0.0 and -balance or 0.0,
                        'currency_id': currency.id,
                    })
                invoice_vals['invoice_line_ids'].append((0, 0, invoice_line_vals))

            # Create invoice lines from fees.
            for fee in repair.fees_lines:
                if group:
                    name = repair.name + '-' + fee.name
                else:
                    name = fee.name

                if not fee.product_id:
                    raise UserError(_('No product defined on fees.'))

                account = fee.product_id.product_tmpl_id.get_product_accounts(fiscal_pos=fpos)['income']
                if not account:
                    raise UserError(_('No account defined for product "%s".', fee.product_id.name))

                invoice_line_vals = {
                    'name': name,
                    'account_id': account.id,
                    'quantity': fee.product_uom_qty,
                    'tax_ids': [(6, 0, fee.tax_id.ids)],
                    'product_uom_id': fee.product_uom.id,
                    'price_unit': fee.price_unit,
                    'product_id': fee.product_id.id,
                    'repair_fee_ids': [(4, fee.id)],
                    'discount': fee.discount
                }

                if currency == company.currency_id:
                    balance = -(fee.product_uom_qty * fee.price_unit)
                    invoice_line_vals.update({
                        'debit': balance > 0.0 and balance or 0.0,
                        'credit': balance < 0.0 and -balance or 0.0,
                    })
                else:
                    amount_currency = -(fee.product_uom_qty * fee.price_unit)
                    balance = currency._convert(amount_currency, company.currency_id, company,
                                                fields.Date.today())
                    invoice_line_vals.update({
                        'amount_currency': amount_currency,
                        'debit': balance > 0.0 and balance or 0.0,
                        'credit': balance < 0.0 and -balance or 0.0,
                        'currency_id': currency.id,
                    })
                invoice_vals['invoice_line_ids'].append((0, 0, invoice_line_vals))

        # Create invoices.
        invoices_vals_list_per_company = defaultdict(list)
        for (partner_invoice_id, currency_id, company_id), invoices in grouped_invoices_vals.items():
            for invoice in invoices:
                invoices_vals_list_per_company[company_id].append(invoice)

        for company_id, invoices_vals_list in invoices_vals_list_per_company.items():
            # VFE TODO remove the default_company_id ctxt key ?
            # Account fallbacks on self.env.company, which is correct with with_company
            self.env['account.move'].with_company(company_id).with_context(default_company_id=company_id,
                                                                           default_move_type='out_invoice').create(
                invoices_vals_list)

        repairs.write({'invoiced': True})
        repairs.mapped('operations').filtered(lambda op: op.type == 'add').write({'invoiced': True})
        repairs.mapped('fees_lines').write({'invoiced': True})

        return dict((repair.id, repair.invoice_id.id) for repair in repairs)

    @api.depends('unit')
    @api.onchange('unit')
    def onchange_unit(self):
        if self.unit:
            obj_product_id = self.env['product.template'].search([('unit', '=', self.unit)], limit=1)
            self.product_id = obj_product_id.id if obj_product_id else False

    def action_add_new_order(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id('order_repair_todoo.action_repair_order_wizard')
        action['context'] = {'default_repair_id': self.id}
        return action


class RepairLine(models.Model):
    _inherit = 'repair.line'

    discount = fields.Float('Disc. %')

    @api.depends('price_unit', 'repair_id', 'product_uom_qty', 'product_id', 'tax_id', 'discount', 'repair_id.invoice_method')
    def _compute_price_total_and_subtotal(self):
        for line in self:
            price_after_discount = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(
                price_after_discount,
                line.repair_id.pricelist_id.currency_id,
                line.product_uom_qty,
                product=line.product_id,
                partner=line.repair_id.partner_id,
            )
            line.price_subtotal = line.currency_id.round(taxes['total_excluded'])
            line.price_total = line.currency_id.round(taxes['total_included'])


class RepairFee(models.Model):
    _inherit = 'repair.fee'

    discount = fields.Float('Disc. %')

    @api.depends('price_unit', 'repair_id', 'product_uom_qty', 'product_id', 'tax_id', 'discount')
    def _compute_price_total_and_subtotal(self):
        for fee in self:
            price_after_discount = fee.price_unit * (1 - (fee.discount or 0.0) / 100.0)
            taxes = fee.tax_id.compute_all(
                price_after_discount,
                fee.repair_id.pricelist_id.currency_id,
                fee.product_uom_qty,
                product=fee.product_id,
                partner=fee.repair_id.partner_id,
            )
            fee.price_subtotal = fee.currency_id.round(taxes['total_excluded'])
            fee.price_total = fee.currency_id.round(taxes['total_included'])
