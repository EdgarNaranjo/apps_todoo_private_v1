# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import api, fields, models, tools, SUPERUSER_ID, _

_logger = logging.getLogger(__name__)

DICT_LANG = {
    'AR': 'es_AR',
    'BO': 'es_BO',
    'ES': 'es_ES',
    'CL': 'es_ES',
    'BE': 'fr_BE',
    'AU': 'en_AU',
    'BG': 'bg_BG',
    'BR': 'pt_BR',
    'CA': 'en_CA',
    'CN': 'zh_HK',
    'CO': 'es_CO',
    'CR': 'es_CR',
    'CU': 'es_ES',
    'CZ': 'cs_CZ',
    'DE': 'de_DE',
    'DK': 'da_DK',
    'DO': 'es_ES',
    'EC': 'es_EC',
    'EE': 'et_EE',
    'EG': 'ar_SY',
    'EH': 'ar_SY',
    'FR': 'fr_FR',
    'GF': 'fr_CH',
    'GR': 'el_GR',
    'GT': 'es_GT',
    'HK': 'zh_HK',
    'HN': 'es_ES',
    'HR': 'hr_HR',
    'HU': 'hu_HU',
    'ID': 'id_ID',
    'IN': 'hi_IN',
    'IT': 'it_IT',
    'JP': 'ja_JP',
    'KP': 'ko_KP',
    'KR': 'ko_KR',
    'LA': 'lo_LA',
    'LT': 'lt_LT',
    'LU': 'lb_LU',
    'LV': 'lv_LV',
    'MF': 'fr_FR',
    'MN': 'mn_MN',
    'MX': 'es_MX',
    'NO': 'nb_NO',
    'PA': 'es_PA',
    'PE': 'es_PE',
    'PF': 'fr_CH',
    'PM': 'fr_CH',
    'PL': 'pl_PL',
    'PN': 'fr_CH',
    'PT': 'pt_PT',
    'PY': 'es_PY',
    'RE': 'fr_FR',
    'RO': 'ro_RO',
    'SE': 'sv_SE',
    'SI': 'sl_SI',
    'SK': 'sk_SK',
    'TH': 'th_TH',
    'TR': 'tr_TR',
    'GB': 'en_GB',
    'UY': 'es_UY',
    'UY': 'es_UY',
    'VE': 'es_VE',
    'VN': 'vi_VN',
}


class Partner(models.Model):
    _inherit = "res.partner"

    @api.constrains('country_id')
    def _constrain_language(self):
        env_lang = self.env['res.lang']
        env_install = self.env['base.language.install']
        for record in self:
            if record.country_id:
                country = record.country_id
                keys_list = DICT_LANG.keys()
                lang_value = [DICT_LANG.get(key) for key in keys_list if country.code in keys_list and key == country.code]
                if lang_value:
                    for lang in lang_value:
                        obj_lang_inactive_id = env_lang.search([('code', '=', lang), ('active', '=', False)], limit=1)
                        if obj_lang_inactive_id:
                            lang_install = env_install.create({'lang_ids': obj_lang_inactive_id.ids, 'overwrite': True})
                            lang_install.lang_install()
                            val_lang = lang_install.first_lang_id.code
                        else:
                            obj_lang_active_id = env_lang.search([('code', '=', lang), ('active', '=', True)], limit=1)
                            if obj_lang_active_id:
                                val_lang = obj_lang_active_id.code
                else:
                    val_lang = 'en_US'
                record.lang = val_lang
                record.message_post(body="Lang: {}" .format(val_lang))
