# Copyright 2024-TODAY Todooweb (www.todooweb.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from . import models
from . import wizards
from . import controllers

from odoo import api, SUPERUSER_ID


def create_data(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    companies = env['res.company'].search([])
    for company in companies:
        env['ir.sequence'].create({
            'name': 'OTs ({})'.format(company.name),
            'code': 'project.task',
            'padding': 5,
            'prefix': 'OT/%(y)s/',
            'use_date_range': True,
            'company_id': company.id
        })
