# Copyright 2025-TODAY Todooweb (<http://www.todooweb.com>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, models, fields, _
from odoo.exceptions import AccessError
import logging

_logger = logging.getLogger(__name__)

class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def search_terms(self, term):
        """
        Global search in models marked with 'allow_search'.
        Optimized for Odoo 19 with error handling per model.
        """
        if not term or len(term) < 3:
            return []

        res = []
        LIMIT = 5
        
        # Search for models that have 'allow_search' active
        # We use sudo() to find the models, but we search records with user environment
        searchable_models = self.env['ir.model'].sudo().search([('allow_search', '=', True)])
        
        for model_rec in searchable_models:
            model_name = model_rec.model
            
            # 1. Check if model exists in current registry
            if model_name not in self.env:
                continue
                
            # 2. Check if user has read access to this model
            if not self.env[model_name].check_access_rights('read', raise_exception=False):
                continue
            
            try:
                # 3. Perform the search
                # We use name_search which is the standard for autocomplete/m2o
                records = self.env[model_name].name_search(term, limit=LIMIT + 1)
                
                if records:
                    has_more = len(records) > LIMIT
                    records = records[:LIMIT]
                    res.append({
                        'model': model_name,
                        'name': model_rec.name,
                        'records': records,
                        'total_count': len(records),
                        'has_more': has_more,
                    })
            except Exception as e:
                # Log the error but don't break the whole search
                _logger.warning("Global Search: Error searching in model %s: %s", model_name, str(e))
                continue
                
        return res


class IrModel(models.Model):
    _inherit = 'ir.model'

    allow_search = fields.Boolean(
        string='Allow Search',
        help="If checked, this model will be included in the Global Advanced Search."
    )
