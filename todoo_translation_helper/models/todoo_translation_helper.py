# Copyright 2025-TODAY Todooweb (www.todooweb.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import logging
import time

from odoo import api, fields, models, _
from odoo.exceptions import UserError

try:
    from googletrans import Translator
    translator = Translator()
except ImportError:
    translator = None

_logger = logging.getLogger(__name__)


class LanguageList(models.Model):
    _name = 'languages.list'
    _description = 'Language List'

    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code", required=True)


class ToolTranslationHelper(models.TransientModel):
    _name = 'tool.translation.helper'
    _description = 'Tool Translation Helper'

    name = fields.Char('Name', index=True, default='/')
    lang_id = fields.Many2one('languages.list', 'Language', index=True, tracking=True)
    origin = fields.Char('Origin')
    destiny = fields.Char('Destiny')
    synonyms = fields.Char('Synonyms')
    translation = fields.Char('Translation')
    definitions = fields.Char('Definitions')
    description = fields.Text('Source text')
    translate = fields.Text('Translation value')
    type_text = fields.Selection([
        ('word', 'Word / Sentence'),
        ('text', 'Text'),
        ('file', 'File'),
    ], string='Type', index=True, tracking=True, default='text')
    attachment_ids = fields.Many2many(
        'ir.attachment', 'attact_tool_rel', 'tool_id', 'attach_id',
        ondelete="cascade", string='Attachments',
    )

    @api.model_create_multi
    def create(self, vals_list):
        if not translator:
            raise UserError(_("googletrans library is not installed. Run: pip install googletrans==4.0.0-rc1"))
        text_obj = self.env['text.translations.helper']
        records = super().create(vals_list)
        for request in records:
            sequence_name = self.env['ir.sequence'].next_by_code('tool.translation.helper') or "/"
            request.name = 'TOOL' + sequence_name
            if request.type_text == 'file' and not request.attachment_ids:
                raise UserError(_("An attachment is required."))
            description = request.description
            if len(request.attachment_ids) > 1:
                raise UserError(_("Only one attachment is required."))
            attach = request.attachment_ids
            if attach:
                corp_message = self.read_file_source(attach, request)
                if corp_message:
                    description = corp_message
            obj_trans = self.translate_term(description, request)
            if obj_trans:
                dict_vals = {
                    k: v for k, v in {
                        'code_tool': request.name,
                        'origin': request.origin,
                        'destiny': request.destiny,
                        'synonyms': request.synonyms,
                        'translation': request.translation,
                        'definitions': request.definitions,
                        'description': request.description,
                        'translate': request.translate,
                    }.items() if v
                }
                text_obj.create(dict_vals)
        return records

    def translate_term(self, description, request):
        if not request.lang_id:
            return False
        lang = request.lang_id
        if not (lang.code and description):
            raise UserError(_("There is nothing to translate!"))
        try:
            val = translator.translate(description, dest=lang.code)
            time.sleep(1)
            request.origin = '( ' + val.src + ' )'
            request.destiny = '( ' + val.dest + ' )'
            request.translate = val.text
            if val.extra_data and request.type_text == 'word':
                if val.extra_data.get('synonyms'):
                    request.synonyms = val.extra_data['synonyms']
                if val.extra_data.get('translation'):
                    request.translation = val.extra_data['translation']
                if val.extra_data.get('definitions'):
                    request.definitions = val.extra_data['definitions']
            return True
        except Exception:
            raise UserError(_("No Translation Found. Please Check Your Internet Connection."))

    def read_file_source(self, attach, request):
        if attach:
            request.description = base64.b64decode(attach[0].datas)
            return request.description
        return False


class TextTranslationsHelper(models.Model):
    _name = 'text.translations.helper'
    _description = 'Text Translation'
    _order = 'create_date desc'

    name = fields.Char('Name', index=True, default='/')
    code_tool = fields.Char('Tools')
    origin = fields.Char('Origin')
    destiny = fields.Char('Destiny')
    synonyms = fields.Char('Synonyms')
    translation = fields.Char('Translation')
    definitions = fields.Char('Definitions')
    description = fields.Text('Source')
    translate = fields.Text('Translation')

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for request in records:
            sequence_name = self.env['ir.sequence'].next_by_code('text.translations.helper') or "/"
            request.name = 'TRANSL' + sequence_name
        return records
