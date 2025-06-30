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
        tracking=1
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
    ], string='Unit', required=True, tracking=1)
    reference = fields.Char(
        'Reference',
        help='Unit reference',
        required=True, tracking=1)
    tag_attachment = fields.Binary(
        'Unit Tag',
        attachment=True)
    vehicle_starts = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string='Vehicle starts', required=True, tracking=1)
    communication_unit = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string='Communication unit', required=True, tracking=1)
    fault_code = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string='Fault code', required=True, tracking=1)
    diagnosis_attachment = fields.Binary(
        'Diagnosis attachment',
        attachment=True)
    delete_codes = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string='Delete codes', tracking=1)
    symptoms = fields.Text('Symptoms', required=True)
    continuous_failure = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string='Continuous failure', tracking=1)
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
        default=_default_repair_reason)
    repair_type_id = fields.Many2one(
        'repair.type',
       'Repair Type',
       tracking=1,
       default=_default_repair_type)
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
        tracking=1)
    vehicle_model_id = fields.Many2one(
       'vehicle.model',
       'Model',
       required=True,
       tracking=1)
    vehicle_serial_id = fields.Many2one(
       'vehicle.serial',
       'Serial',
       required=True,
       tracking=1)

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
                        lambda e: e.picking_type_code == 'incoming' and e.state in ['confirmed', 'assigned', 'done']):
                    record.check_in = True
                if record.picking_ids.filtered(
                        lambda e: e.picking_type_code == 'outgoing' and e.state in ['confirmed', 'assigned', 'done']):
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
        return self.write({'state': state})

    def action_picking(self):
        if self.check_in and self.check_out:
            raise UserError(
                _("You cannot generate new delivery notes if the entry and exit already exist in the 'Done' status."))
        action = self.env["ir.actions.actions"]._for_xml_id('order_repair_todoo.action_stock_picking_wizard')
        return action

    def _action_repair_confirm(self):
        """ Repair order state is set to 'Confirmed'.
        @param *arg: Arguments
        @return: True
        """
        repairs_to_confirm = self.filtered(lambda repair: repair.state in ['draft', 'pick'])
        repairs_to_confirm._check_company()
        repairs_to_confirm.move_ids._check_company()
        repairs_to_confirm.move_ids._adjust_procure_method()
        repairs_to_confirm.move_ids._action_confirm()
        repairs_to_confirm.move_ids._trigger_scheduler()
        repairs_to_confirm.write({'state': 'confirmed'})
        return True

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
        param_id = self.env['ir.config_parameter'].sudo().get_param('repair_todoo.location_id')
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
