# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import time
import os
import base64

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError

try:
    from googletrans import Translator
    translator = Translator()
except ImportError:
    raise ImportError('Unable to import')

import logging
_logger = logging.getLogger(__name__)


class LanguageList(models.Model):
    _name = 'languages.list'

    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code", required=True)


class ToolTranslationHelper(models.TransientModel):
    _name = 'tool.translation.helper'
    _description = 'Tool Translation Helper'

    name = fields.Char('Name', index=True, default='/')
    lang_id = fields.Many2one('languages.list', 'Language', index=True, track_visibility='always')
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
    ], string='Type', index=True, track_visibility='always', default='text')
    attachment_ids = fields.Many2many('ir.attachment', 'attact_tool_rel', 'tool_id', 'attach_id', ondelete="cascade", string='Attachments')

    @api.model
    def create(self, vals):
        text_obj = self.env['text.translations.helper']
        request = super(ToolTranslationHelper, self).create(vals)
        sequence_name = self.env['ir.sequence'].next_by_code('tool.translation.helper') or "/"
        request.name = 'TOOL' + sequence_name
        if request.type_text == 'file' and not request.attachment_ids:
            raise UserError(_("An attachment is required."))
        else:
            description = request.description
            if len(request.attachment_ids) > 1:
                raise UserError(_("Only one attachment is required."))
            else:
                attach = request.attachment_ids
                corp_message = self.read_file_source(attach, request)
                if corp_message:
                    description = corp_message
            obj_trans = self.translate_term(description, request)
            if obj_trans:
                _logger.info("Translation done!!!")
                dict_vals = {
                    'code_tool': request.name,
                    'origin': request.origin,
                    'destiny': request.destiny,
                    'synonyms': request.synonyms,
                    'translation': request.translation,
                    'definitions': request.definitions,
                    'description': request.description,
                    'translate': request.translate,
                }
                if len(dict_vals) > 0:
                    dict_vals = dict(filter(lambda x: x[1] != False, dict_vals.items()))
                    text_translate = text_obj.create(dict_vals)
                    if text_translate:
                        _logger.info("<< Create Text translate>>")
        return request

    def translate_term(self, description, request):
        ok_process = False
        if request.lang_id:
            lang = request.lang_id
            if lang.code and description:
                try:
                    val = translator.translate(description, dest=lang.code)
                    time.sleep(1)
                    request.origin = '( ' + val.src + ' )'
                    request.destiny = '( ' + val.dest + ' )'
                    request.translate = val.text
                    if val.extra_data and request.type_text == 'word':
                        if val.extra_data['synonyms']:
                            request.synonyms = val.extra_data['synonyms']
                        if val.extra_data['translation']:
                            request.translation = val.extra_data['translation']
                        if val.extra_data['definitions']:
                            request.definitions = val.extra_data['definitions']
                    ok_process = True
                except:
                    raise UserError(_("No Translation Found. Please Check Your Internet Connection."))
            else:
                raise UserError(_("There is nothing to translate !"))
        return ok_process

    def read_file_source(self, attach, request):
        if attach:
            request.description = base64.b64decode(attach[0].datas)
            return request.description


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

    @api.model
    def create(self, vals):
        request = super(TextTranslationsHelper, self).create(vals)
        sequence_name = self.env['ir.sequence'].next_by_code('text.translations.helper') or "/"
        request.name = 'TRANSL' + sequence_name
        return request

    def load_translate(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('todoo_translation_helper.action_translation_load')
        obj_translation = self.env['ir.translation'].search([('src', 'like', self.description)])
        if obj_translation:
            action['context'] = {'default_translation_ids': obj_translation.ids, 'value_translate': self.translate}
        return action


class TranslationLoad(models.TransientModel):
    _name = 'translation.load'
    _description = 'Translation Load'

    translation_ids = fields.Many2many('ir.translation', 'load_trans_rel', 'load_id', 'trans_id', 'Translation')

    def action_update_translate(self):
        if self.env.context.get('value_translate'):
            value_translate = self.env.context.get('value_translate')
            if value_translate:
                for item in self.translation_ids:
                    item.value = value_translate

