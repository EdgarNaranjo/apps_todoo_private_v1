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
try:
    import hashlib
except ImportError:
    raise ImportError("This module needs hashlib. (sudo pip install hashlib)")
try:
    import urllib.request as urllib2
except ImportError:
    raise ImportError("This module needs urllib2. (sudo pip install urllib2)")

try:
    from unidecode import unidecode
except ImportError:
    raise ImportError("This module needs unidecode. (sudo pip install unidecode)")

import logging
_logger = logging.getLogger(__name__)

route = '/tmp/DESCARGA_PO/'


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    helper_id = fields.Many2one('text.translations.helper', 'Text Translations Helper')


class ToolTranslationHelper(models.TransientModel):
    _inherit = 'tool.translation.helper'

    type_text = fields.Selection([
        ('word', 'Word / Sentence'),
        ('text', 'Text'),
        ('file', 'File'),
        ('po', 'File .po'),
    ], string='Type', index=True, track_visibility='always', default='po')
    ok_translate = fields.Boolean('Translated', default=False)
    helper_id = fields.Many2one('text.translations.helper', 'Text Translations Helper')

    @api.model
    def create(self, vals):
        request = super(ToolTranslationHelper, self).create(vals)
        if request.type_text in ['file', 'po'] and not request.attachment_ids:
            raise UserError(_("An attachment is required."))
        else:
            description = request.description
            if len(request.attachment_ids) > 1:
                raise UserError(_("Only one attachment is required."))
            elif request.attachment_ids and request.attachment_ids[0].name[-3:] not in ['txt', '.po']:
                raise UserError(_("A file of the type '.txt' or '.po' is required."))
            else:
                attach = request.attachment_ids
                corp_message = self.read_file_source_advance(attach, request)
                if corp_message:
                    description = corp_message
            obj_trans = self.translate_term(description, request)
            if obj_trans:
                _logger.info("Translation done!!!")
                obj_translations_ids = self.env['text.translations.helper'].search([('code_tool', '=', request.name)])
                if obj_translations_ids:
                    for obj_translations in obj_translations_ids:
                        dict_write = {
                            'description': request.description,
                            'translate': request.translate,
                        }
                        obj_translations.write(dict_write)
                        _logger.info("<< Update Text translate>>")
                        request.helper_id = obj_translations.id
                        if request.type_text == 'po':
                            if os.path.exists(route):
                                archivo_po = os.path.join(route, attach[0].name)
                                file_finish = self.update_file(archivo_po, request.translate)
                                if file_finish:
                                    create_attach = self.create_attachment(file_finish, obj_translations)
                                    if create_attach:
                                        _logger.info("<< Create attachment>>")
                        request.ok_translate = True
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

    def read_file_source_advance(self, attach, request):
        if attach:
            file_create = self.write_lines(attach)
            if file_create:
                file_readline = self.file_readlines(file_create)
                if file_readline:
                    request.description = file_readline
            return request.description

    def write_lines(self, attach):
        # crear ruta sino existe
        if not os.path.exists(route):
            os.makedirs(route)
        if os.path.exists(route):
            archivo_po = os.path.join(route, attach[0].name)
            with open(archivo_po, 'wb') as fw_f:
                fw_f.write(base64.b64decode(attach[0].datas))
            fw_f.close()
        return archivo_po

    def file_readlines(self, file_create):
        val_item = ''
        with open(file_create, 'r') as file_data:
            all_lines = file_data.readlines()
            for line in all_lines:
                if line.startswith('msgid "'):
                    val_item += line[6:]
        file_data.close()
        return val_item

    def update_file(self, archivo_po, translate):
        list_translate = translate.split('\n')
        cont_position = 0
        cont_file = 0
        with open(archivo_po, 'r') as file_data:
            all_lines = file_data.readlines()
            for line in all_lines:
                cont_file += 1
                if line.startswith('msgstr "'):
                    val_item = list_translate[cont_position]
                    cont_position += 1
                    concat_value = 'msgstr ' + val_item + '\n'
                    if line in all_lines[cont_file - 1]:
                        all_lines[cont_file - 1] = unidecode(all_lines[cont_file - 1].replace(line, concat_value), 'utf-8')
        with open(archivo_po, "w") as file_write:
            file_write.writelines(all_lines)
        file_data.close()
        file_write.close()
        return archivo_po

    def create_attachment(self, archivo_txt, obj_trans):
        contenido_po = file_get_contents(archivo_txt)
        bin_data = base64.b64encode(contenido_po)
        attachment = {
            'name': archivo_txt.split('/')[-1],
            'res_model': 'text.translations.helper',
            # 'datas_fname': archivo_txt.split('/')[-1],
            'db_datas': bin_data,
            'datas': bin_data,
            'file_size': len(bin_data),
            'mimetype': 'text/plain',
            'checksum': hashlib.sha1(bin_data).hexdigest(),
            'res_id': obj_trans.id,
            'helper_id': obj_trans.id,
        }
        obj_att = self.env['ir.attachment'].create(attachment)
        os.remove(archivo_txt)
        return obj_att

def file_get_contents(filename, use_include_path=0, context=None, offset=-1, maxlen=-1):
    if filename.find('://') > 0:
        ret = urllib2.urlopen(filename).read()
        if offset > 0:
            ret = ret[offset:]
        if maxlen > 0:
            ret = ret[:maxlen]
        return ret
    else:
        fp = open(filename, 'rb')
        try:
            if offset > 0:
                fp.seek(offset)
            ret = fp.read(maxlen)
            return ret
        finally:
            fp.close()


class TextTranslationsHelper(models.Model):
    _inherit = 'text.translations.helper'

    name = fields.Char('Name', index=True, default='/')
    attachment_count = fields.Integer(compute='_compute_todo_attachment')
    attachment_ids = fields.One2many('ir.attachment', 'helper_id', 'Attachments')

    def _compute_todo_attachment(self):
        for obj_helper in self:
            obj_helper.attachment_count = len(obj_helper.attachment_ids)

    def action_view_attachments(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Text Translations',
            'res_model': 'ir.attachment',
            'view_mode': 'kanban,tree,form',
            'view_type': 'form',
            'domain': [('id', 'in', self.attachment_ids.ids)]
        }