import base64
import datetime
import io
import xlsxwriter
from random import randint

from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, AccessError

import logging

_logger = logging.getLogger(__name__)

LIST_FIELD = ['boolean', 'one2many', 'many2many', 'binary', 'html']
LIST_NOT = [
    #'id',
    '__last_update',
    'create_date',
    'create_uid',
    'write_date',
    'write_uid',
    'access_token',
    'access_url',
    'access_warning',
    'activity_calendar_event_id',
    'activity_exception_decoration',
    'activity_exception_icon',
    'activity_exception_decoration',
    'activity_type_icon',
    'activity_type_id',
    'activity_user_id',
    'activity_date_deadline',
    'activity_state',
    'activity_summary',
    'message_main_attachment_id',
    'my_activity_date_deadline',
    'medium_id'
]


class Document(models.Model):
    _inherit = 'documents.document'

    def unlink(self):
        env_bi = self.env['constructor.power.bi.data']
        for record in self:
            if record in env_bi.search([('state', '!=', 'draft')]).mapped('document_id'):
                raise UserError(_('It is not possible to delete a document related to a PowerBI query that '
                                  'has been processed. \nContacted an administrator.'))
        return super().unlink()


class UpdateFileCsvWizard(models.TransientModel):
    _name = 'update.file.csv.wizard'
    _description = 'Update File Csv Wizard'
    _rec_name = 'setting_id'

    setting_id = fields.Many2one('power.bi.setting', 'Power Bi Setting')
    line_ids = fields.Many2many('power.bi.line', 'wizard_powerbi_rel', 'wizard_id', 'powerbi_id', 'Lines')
    check_process = fields.Boolean('Not processed', help='Show only "Not processed" lines')

    def action_update_records(self):
        for setting in self.env['power.bi.setting'].search([('id', '=', self.setting_id.id), ('state', '=', 'active')]):
            setting.update_list_excel(self)

    @api.onchange('check_process')
    def onchange_lines(self):
        if self.check_process:
            self.line_ids = self.line_ids.filtered(lambda e: not e.ok_process)


class ConstructorPowerBiData(models.Model):
    _name = "constructor.power.bi.data"
    _description = "Constructor Power Bi Data"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = 'id desc'

    name = fields.Char('Name', default='/')
    type_query = fields.Selection([
        ('simple', 'Simple')
    ], string='Type query', tracking=1, required=True, default='simple')
    model_id = fields.Many2one('ir.model', string='Models', tracking=1)
    model_name = fields.Char(related='model_id.model', tracking=1)
    domain = fields.Char('Domain', tracking=1)
    state = fields.Selection([
        ("draft", "Draft"),
        ("process", "In construction"),
        ("done", "Done"),
    ], string="Status", default='draft', tracking=1)
    active = fields.Boolean(default=True)
    date_last_use = fields.Datetime('Last Use Date', readonly=True, tracking=1)
    field_ids = fields.One2many('power.bi.data.field', 'constructor_id', 'Fields', copy=True)
    other_field_ids = fields.One2many('additional.data.field', 'constructor_id', 'Other fields', copy=True)
    description = fields.Char('Description')
    doc_count = fields.Integer('Doc. count', compute='get_count_doc')
    document_id = fields.Many2one('documents.document', string='Document', tracking=1, copy=False)
    category_id = fields.Many2many(
        comodel_name='tag.category.document',
        relation='constructor_category_rel',
        column1='constructor_id',
        column2='category_id',
        string="Category",
        copy=False,
    )
    check_many = fields.Boolean('Check many', compute='_get_count_lines')
    data_many = fields.Integer('Many data', compute='_get_count_lines')

    def set_to_draft(self):
        self.state = 'draft'

    def get_fields_by_model_id(self, record):
        val_fields = record.model_id.field_id
        list_item = [{'constructor_id': record.id,
                      'field_id': item['id'],
                      'name': item['field_description'],
                      'field_name': item['name'],
                      'export_type': self._get_export_type(item)}
                     for item in val_fields
                     if item and item.ttype not in LIST_FIELD and item.name not in LIST_NOT]
        obj_create_item = self.env['power.bi.data.field'].create(list_item)
        if obj_create_item:
            return True

    def action_open_doc(self):
        dic_return = {
            'name': 'Related documents',
            'type': 'ir.actions.act_window',
            'view_mode': 'kanban,tree,form',
            'res_model': 'documents.document',
            'domain': [('id', '=', self.document_id.id)]
        }
        return dic_return

    def get_count_doc(self):
        for record in self:
            record.doc_count = 1 if record.document_id else 0

    @staticmethod
    def _get_export_type(field):
        type_mapping = {
            'integer': 'number',
            'float': 'number',
            'monetary': 'decimal',
            'date': 'date',
            'datetime': 'datetime',
        }
        return type_mapping.get(field.ttype, 'text')

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('constructor.power.bi.data')
        res = super(ConstructorPowerBiData, self).create(vals)
        if res and not self:
            obj_create_item = self.get_fields_by_model_id(res)
            if obj_create_item:
                _logger.info('Create items by CREATE (super)')
        return res

    def write(self, vals):
        res = super(ConstructorPowerBiData, self).write(vals)
        if 'model_id' in vals:
            for record in self.filtered(lambda r: r.type_query == 'simple'):
                record.field_ids.unlink()
                obj_create_item = self.get_fields_by_model_id(record)
                if obj_create_item:
                    _logger.info('Create items by CREATE (super)')
        return res

    def copy_data(self, default=None):
        name = _("%s (copy)", self.description)
        default = dict(default or {}, description=name)
        return super(ConstructorPowerBiData, self).copy_data(default)

    @api.depends('model_id', 'domain')
    def _get_count_lines(self):
        env_setting = self.env['power.bi.setting'].search([('state', '=', 'active')], limit=1)
        for record in self:
            record.check_many = False
            record.data_many = 0
            if record.model_id:
                model_env = self.env[record.model_id.model]
                list_domain = record.get_domain_by_data()
                records = model_env.sudo().search(list_domain, order='id')
                record.data_many = len(records)
                size = env_setting.size_query
                if record.data_many >= size:
                    record.check_many = True

    @api.constrains('state')
    def check_setting_by_state(self):
        env_setting_id = self.env['power.bi.setting']
        env_line_id = self.env['power.bi.line']
        for record in self:
            if record.document_id:
                obj_setting_id = env_setting_id.search([('state', '=', 'active')], limit=1)
                if obj_setting_id:
                    line_ids = obj_setting_id.line_ids
                    if record.state == 'done':
                        if not line_ids or record.id not in line_ids.mapped('power_bi_id.id'):
                            env_line_id.create({'setting_id': obj_setting_id.id,
                                                'power_bi_id': record.id,
                                                'document_id': record.document_id.id})
                    elif record.state == 'draft':
                        for item in line_ids:
                            if record == item.mapped('power_bi_id'):
                                item.unlink()

    def unlink(self):
        if any(record.state == 'done' for record in self):
            raise UserError(_('This record cannot be deleted!'))
        documents = self.mapped('document_id')
        if documents:
            documents.unlink()
        env_powerbi_lines = self.env['power.bi.line']
        powerbi_lines = env_powerbi_lines.search([('power_bi_id', 'in', self.ids)])
        if powerbi_lines:
            powerbi_lines.unlink()
        return super(ConstructorPowerBiData, self).unlink()

    def get_domain_by_data(self):
        val_domain = self.domain
        records_domain = []
        if val_domain:
            if val_domain[1:-1] != '':
                records_domain = eval(val_domain)
        return records_domain

    def execute_query(self):
        for rec in self:
            if not rec.write_uid.active:
                raise UserError(_(' User is inactive.'))
            lang = self.env.user.lang or 'en_US'
            model_name = rec.model_id.model
            model_env = self.env[model_name].with_context(lang=lang)
            list_domain = self.get_domain_by_data()
            records = model_env.sudo().search(list_domain, order='id')
            labels, data2export = self.export_model_data(records.with_context(replace_whitespace_chars=True))
            filename = rec.model_id.model.replace('.', '_') + '_odoo_data.xlsx'
            file_excel = __generate_excel_data__(labels, data2export)
            documents = self.create_document(file_excel, filename, rec)
            state_ct = 'process' if rec.state == 'draft' else 'done' if rec.state == 'process' else rec.state
            rec.write({'document_id': documents[0].id, 'state': state_ct, 'date_last_use': fields.Datetime.now()})

    def export_model_data(self, records):
        self.ensure_one()
        labels = []
        lines = []
        def get_export_value(_record, _field_key):
            _field = _record._fields[_field_key]
            value = _record[_field_key]
            if isinstance(value, models.BaseModel):
                _field, fname = (value._fields['name'], value['name']) if value._fields.get('name') else (
                    value._fields['display_name'], value['display_name'])
                return _field.convert_to_export(fname, value) or ''
            return _field.convert_to_export(value, _record)
        total_cols = len(self.field_ids) + len(self.other_field_ids)
        field_ids = []
        for _field in self.field_ids:
            labels.append(_field.name)
            field_key = _field.field_name
            if _field.related_property:
                field_key += _field.related_property
            field_ids.append(field_key)
        other_field_ids = []
        for _field in self.other_field_ids:
            labels.append(_field.name)
            other_field_ids.append((_field.field_id.name, _field.relation_field_id.name))
        for record in __iterable_splitter__(records):
            # main line of record, initially empty
            current = [''] * total_cols
            lines.append(current)
            i = 0
            # Process field_ids
            for i, field_key in enumerate(field_ids):
                current[i] = get_export_value(_record=record, _field_key=field_key)
            i = i + 1 if i > 0 else 0
            # Process other_field_ids
            for i, _field_tuple in enumerate(other_field_ids, start=i):
                _record = record[_field_tuple[0]]
                current[i] = get_export_value(_record=_record, _field_key=_field_tuple[1])
            i = i + 1 if i > 0 else 0
        return labels, lines

    def create_document(self, file_excel, filename, constructor_id):
        env_attachment = self.env['ir.attachment']
        folder = self.env.ref('powerbi_todoo.documents_folder_power_bi')
        categorie_created = self.env.ref('powerbi_todoo.documents_power_bi_tag00')
        categorie_updated = self.env.ref('powerbi_todoo.documents_power_bi_tag01')
        attachment_dict = {
            'db_datas': file_excel,
            'datas': file_excel,
            'name': filename}
        if constructor_id.document_id:
            constructor_id.document_id.tag_ids = categorie_updated.ids
            attachment_id = constructor_id.document_id.attachment_id
            old_attachment = attachment_id.with_context(no_document=True).copy()
            constructor_id.document_id.previous_attachment_ids = [(4, old_attachment.id, False)]
            attachment = attachment_id.write(attachment_dict)
            if attachment:
                return constructor_id.document_id, attachment_id
        else:
            attachment = env_attachment.with_context(no_document=True).create(attachment_dict)
            if attachment:
                dict_items = {
                    'folder_id': folder.id,
                    'attachment_id': attachment.id,
                    'tag_ids': categorie_created.ids
                }
                document = self.env['documents.document'].sudo().create(dict_items)
                return document, attachment


class PowerBiDataField(models.Model):
    _name = 'power.bi.data.field'
    _description = 'Power Bi Data Field'
    _order = 'sequence'

    constructor_id = fields.Many2one('constructor.power.bi.data', ondelete='cascade', string='Constructor Power Bi')
    sequence = fields.Integer(string='Sequence', default=10)
    model = fields.Char('Model related', related='constructor_id.model_name', readonly=True)
    field_id = fields.Many2one('ir.model.fields', ondelete='cascade', string='Field',
                               domain='[("model", "=", model), ("name", "!=", "id")]')
    name = fields.Char('Label', required=True)
    field_name = fields.Char('Field Key', required=True)
    related_property = fields.Char('Related Property')
    export_type = fields.Selection([
        ('text', 'Text'),
        ('number', 'Number'),
        ('decimal', 'Decimal'),
        ('date', 'Date'),
        ('datetime', 'Datetime'),
    ], string="Type", default="text")

    @api.onchange('field_id')
    def _onchange_field_id(self):
        if self.field_id:
            self.name = self.field_id.field_description
            self.field_name = self.field_id.name
            self.export_type = self._get_export_type(self.field_id)

    @staticmethod
    def _get_export_type(field):
        type_mapping = {
            'integer': 'number',
            'float': 'number',
            'monetary': 'decimal',
            'date': 'date',
            'datetime': 'datetime',
        }
        return type_mapping.get(field.ttype, 'text')


class AdditionalDataField(models.Model):
    _name = 'additional.data.field'
    _description = 'Additional Data Field'
    _order = 'sequence'

    constructor_id = fields.Many2one('constructor.power.bi.data', ondelete='cascade', string='Constructor Power Bi')
    sequence = fields.Integer(string='Sequence', default=10)
    model = fields.Char('Model related', related='constructor_id.model_name', readonly=True)
    field_id = fields.Many2one('ir.model.fields', string='Field', ondelete='cascade',
                               domain='[("model", "=", model), ("ttype", "=", "many2one")]')
    relation_model = fields.Char('Relation model', related='field_id.relation', readonly=True)
    relation_field_id = fields.Many2one('ir.model.fields', string='Related field', ondelete='cascade',
                                        domain='[("model", "=", relation_model), '
                                               '("ttype", "not in", ["binary", "boolean", "one2many", "many2many", '
                                               '"reference"])]')
    name = fields.Char('Label', required=True)
    field_name = fields.Char('Field Key', required=True)
    export_type = fields.Selection([
        ('text', 'Text'),
        ('number', 'Number'),
        ('decimal', 'Decimal'),
        ('date', 'Date'),
        ('datetime', 'Datetime'),
    ], string="Type", default="text")

    @api.onchange('relation_field_id')
    def _onchange_field_id(self):
        if self.relation_field_id:
            if self.name != self.relation_field_id.field_description:
                self.name = self.relation_field_id.field_description
            if self.field_name != self.relation_field_id.name:
                self.field_name = self.relation_field_id.name
            self.export_type = self._get_export_type(self.relation_field_id)

    @staticmethod
    def _get_export_type(field):
        type_mapping = {
            'integer': 'number',
            'float': 'number',
            'monetary': 'decimal',
            'date': 'date',
            'datetime': 'datetime',
        }
        return type_mapping.get(field.ttype, 'text')


class PowerBiSetting(models.Model):
    _name = 'power.bi.setting'
    _description = 'Settings'

    name = fields.Char('Name', default='/')
    state = fields.Selection([
        ("no_active", "No active"),
        ("active", "Active"),
    ], string="Status", default="active")
    line_ids = fields.One2many('power.bi.line', 'setting_id', 'Lines')
    limit_store = fields.Integer('Limit store', help='Number of times a file can be stored. '
                                                     'A negative number indicates no limit.', default=-1)
    qty_partition = fields.Selection([
        ("1", "1"),
        ("2", "2"),
        ("3", "3"),
        ("4", "4"),
        ("5", "5"),
        ("10", "10"),
        ("all", "All"),
    ], string="Partition", default="all", help='Number of files to process in each iteration.')
    ok_process = fields.Boolean('Processed', default=False)
    time_execution = fields.Integer('Time execution', help='Execution time between file packages.', default=5)
    size_query = fields.Integer('Size query', help='Reference value to show alert in PowerBI queries.')

    @api.model
    def create(self, vals):
        env_power_id = self.env['constructor.power.bi.data']
        env_line_id = self.env['power.bi.line']
        vals['name'] = self.env['ir.sequence'].next_by_code('power.bi.setting')
        request = super(PowerBiSetting, self).create(vals)
        if request:
            obj_power_bi = env_power_id.search([('state', '=', 'done'), ('active', '=', True)])
            existing_power_bi_ids = request.line_ids.mapped('power_bi_id')
            list_item = [{
                'setting_id': request.id,
                'power_bi_id': item.id,
                'document_id': item.document_id.id
            } for item in obj_power_bi if item not in existing_power_bi_ids]
            if list_item:
                env_line_id.create(list_item)
        return request

    def set_not_active(self):
        for record in self:
            record.state = 'no_active'

    def set_active(self):
        for record in self:
            record.state = 'active'

    def unlink(self):
        res = super(PowerBiSetting, self).unlink()
        if self.line_ids:
            self.line_ids.unlink()
        return res

    @api.constrains('qty_partition', 'line_ids')
    def check_qty_partition(self):
        for record in self:
            if record.qty_partition and record.qty_partition != 'all':
                if (len(record.line_ids) / int(record.qty_partition)) < 1:
                    raise UserError(
                        _('Option "{}" is not a valid value for this Configuration.').format(record.qty_partition))

    @api.model
    def read_setting_power_bi(self):
        setting_ids = self.env['power.bi.setting'].search([('state', '=', 'active'), ('ok_process', '=', False)],
                                                          limit=1)
        if setting_ids:
            setting_ids.line_ids.write({'ok_process': False})
            partitions = setting_ids.qty_partition
            total_lines = len(setting_ids.line_ids)
            dict_value = {
                'numbercall': 1 if partitions == 'all' else -1,
                'interval_number': setting_ids.time_execution,
                'interval_type': 'minutes',
                'active': 'True',
                'nextcall': fields.Datetime.now()
            }
            if partitions != 'all':
                partition_size = int(partitions)
                dict_value['numbercall'] = (total_lines // partition_size) + (total_lines % partition_size > 0)
            cron_update_data = self.env.ref('powerbi_todoo.ir_cron_data_update_list_csv').write(dict_value)
            if cron_update_data:
                _logger.info('OK!')

    @api.model
    def update_list_excel(self, wizard=False):
        origin_view = self.env.context.get('origin_view')
        state_active = [('state', '=', 'active')]
        if origin_view == 'wizard_filter':
            setting_ids = self.env['power.bi.setting'].search(state_active + [('id', '=', wizard.setting_id.id)])
        else:
            setting_ids = self.env['power.bi.setting'].search(state_active)
        for setting in setting_ids:
            list_line = setting.line_ids.filtered(lambda e: e.document_id and (origin_view != 'wizard_filter' or e in wizard.line_ids)).sorted('size_data')
            if origin_view != 'wizard_filter':
                list_line = list_line.filtered(lambda e: not e.ok_process)[:int(setting.qty_partition)]
            for line in list_line:
                self.update_file_excel(line)
                line.ok_process = True

    def action_open_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Update records manually',
            'res_model': 'update.file.csv.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {'origin_view': 'wizard_filter',
                        'default_setting_id': self.id,
                        'default_line_ids': self.line_ids.filtered(lambda e: e.document_id and e.state == 'done').ids
                        }
        }

    def update_attachment(self, file_excel, filename, bi_id, limit_store):
        env_attachment = self.env['ir.attachment']
        attachment_dict = {
            'db_datas': file_excel,
            'datas': file_excel,
            'name': filename
        }
        if bi_id.document_id:
            attachment_id = bi_id.document_id.attachment_id
            old_attachment = attachment_id.with_context(no_document=True).copy()
            bi_id.document_id.previous_attachment_ids = [(4, old_attachment.id, False)]
            if limit_store > 0:
                old_attachments = env_attachment.search([('id', 'in', bi_id.document_id.previous_attachment_ids.ids)],
                                                        order='id DESC')
                if len(old_attachments) > limit_store:
                    to_delete = old_attachments[limit_store:]
                    to_delete.unlink()
            return attachment_id.write(attachment_dict)

    def update_file_excel(self, line):
        categorie_overwrite = self.env.ref('powerbi_todoo.documents_power_bi_tag02')
        bi_id = line.power_bi_id
        lang = self.env.user.lang or 'en_US'
        list_domain = bi_id.get_domain_by_data()
        records = self.env[bi_id.model_id.model].with_context(lang=lang).sudo().search(list_domain, order='id')
        labels, data2export = bi_id.export_model_data(records.with_context(replace_whitespace_chars=True))
        filename = f"{bi_id.model_id.model.replace('.', '_')}_odoo_data.xlsx"
        file_excel = __generate_excel_data__(labels, data2export)
        limit_store = line.setting_id.limit_store
        ok_update = self.update_attachment(file_excel, filename, bi_id, limit_store)
        if ok_update:
            line.last_date_update = datetime.datetime.now()
            line.document_id.tag_ids = [(6, 0, [categorie_overwrite.id])]
            return False


class PowerBiLine(models.Model):
    _name = 'power.bi.line'
    _description = 'Lines'
    _rec_name = 'setting_id'
    _order = 'size_data ASC'

    setting_id = fields.Many2one('power.bi.setting', 'Power Bi Setting')
    power_bi_id = fields.Many2one('constructor.power.bi.data', 'Power bi')
    description = fields.Char(related='power_bi_id.description', string='Description')
    type_query = fields.Selection(related='power_bi_id.type_query', string='Type query')
    state = fields.Selection(related='power_bi_id.state', string='Status')
    document_id = fields.Many2one('documents.document', 'Document')
    last_date_update = fields.Datetime('Last Updated')
    ok_process = fields.Boolean('Processed', default=False)
    size_data = fields.Integer('Size file')
    size_parent = fields.Integer(related='setting_id.size_query')

    @api.model
    def create(self, vals_list):
        env_bi = self.env['constructor.power.bi.data']
        if 'power_bi_id' in vals_list:
            vals_list['size_data'] = env_bi.browse(vals_list['power_bi_id']).data_many
        return super(PowerBiLine, self).create(vals_list)

    @api.constrains('last_date_update')
    def check_update_last_date_update(self):
        for record in self:
            if record.power_bi_id:
                record.size_data = record.power_bi_id.data_many


class TagCategoryDocument(models.Model):
    _name = 'tag.category.document'
    _description = 'Category'

    def _get_default_color(self):
        return randint(1, 11)

    name = fields.Char(string='Tag Name', required=True, translate=True)
    color = fields.Integer(string='Color', default=_get_default_color)


def __generate_excel_data__(labels, rows):
    fp = io.BytesIO()
    workbook = xlsxwriter.Workbook(fp)
    bold_format = workbook.add_format({"bold": True})
    num_format = workbook.add_format({'num_format': '0.00'})
    date_format = workbook.add_format({'num_format': 'd mmmm yyyy'})
    worksheet = workbook.add_worksheet('Export Data')
    for index, col_header in enumerate(labels):
        worksheet.write(0, index, col_header, bold_format)
    _logger.info(f'INFO:    >> Beginning to write {len(rows)} excel rows <<')
    for i, row in enumerate(__iterable_splitter__(rows, is_recorset=False), start=1):
        for col, data in enumerate(row):
            try:
                if isinstance(data, float):
                    worksheet.write_number(i, col, data, num_format)
                elif isinstance(data, (int, str)):
                    worksheet.write(i, col, data)
                else:
                    worksheet.write_datetime(i, col, data, date_format)
            except (MemoryError, TypeError) as e:
                _logger.error(f"ERROR:    <<<<!!!! Wrong data: {data}) !!!!!>>>>>")
                _logger.error(f"ERROR:    <<<<!!!! Writing empty value to ({i}, {col}) !!!!!>>>>>")
                worksheet.write(i, col, '')
    workbook.close()
    _logger.info(f'INFO:    >> Finished writing {len(rows)} excel rows <<')
    fp.seek(0)
    data_b64 = base64.b64encode(fp.read())
    fp.close()
    return data_b64


def __iterable_splitter__(iterable, is_recorset=True):
    count = len(iterable)
    for idx in range(0, count, 1000):
        sub = iterable[idx:idx + 1000]
        for rec in sub:
            yield rec
        if is_recorset:
            sub.invalidate_recordset()
