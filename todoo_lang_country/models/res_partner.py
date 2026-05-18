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
    'VE': 'es_VE',
    'VN': 'vi_VN',
}


class Partner(models.Model):
    _inherit = "res.partner"

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            if record.country_id:
                record._apply_lang_from_country()
        return records

    def write(self, vals):
        res = super().write(vals)
        if 'country_id' in vals:
            for record in self:
                if record.country_id:
                    record._apply_lang_from_country()
        return res

    def _apply_lang_from_country(self):
        """Set partner language based on country and install it if needed."""
        env_lang = self.env['res.lang']
        env_install = self.env['base.language.install']
        country = self.country_id
        if country.code in DICT_LANG:
            lang = DICT_LANG[country.code]
            obj_lang_id = env_lang.search([('code', '=', lang)], limit=1)
            if obj_lang_id:
                if not obj_lang_id.active:
                    lang_install = env_install.create({'lang_ids': obj_lang_id.ids, 'overwrite': True})
                    lang_install.lang_install()
                    val_lang = lang_install.first_lang_id.code
                else:
                    val_lang = obj_lang_id.code
            else:
                val_lang = 'en_US'
        else:
            val_lang = 'en_US'
        self.lang = val_lang
        self.message_post(body=_('Lang: %s') % val_lang)
