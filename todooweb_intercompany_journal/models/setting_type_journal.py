# Copyright 2022-TODAY Rapsodoo Iberia S.r.L. (www.rapsodoo.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, models, fields, tools, _
from odoo.exceptions import UserError


class SettingTypeJournal(models.Model):
    _name = "setting.type.journal"
    _description = "Setting Type Journal"

    name = fields.Char('Name', index=True, default='/')
    type_journal = fields.Selection([
        ('Convencional', 'Convencional'),
        ('Intercompany', 'Intercompany'),
    ], string='Journal type', default='Convencional', index=True, required=True)
    journal_id = fields.Many2one('account.journal', 'Journal', required=True, check_company=True)
    company_id = fields.Many2one('res.company', 'Company', required=True, default=lambda self: self.env.company)
    check_default = fields.Boolean('Default')
    type = fields.Selection(related='journal_id.type', store=True)

    _sql_constraints = [
        ('journal_type_unique', 'unique (type_journal, journal_id)',
         'This journal already has a related type journal!')
    ]

    @api.constrains('type_journal', 'company_id')
    def check_type_journal(self):
        for record in self:
            if record.type_journal:
                record.name = record.type_journal + '-' + record.company_id.name
