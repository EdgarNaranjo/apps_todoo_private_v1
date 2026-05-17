# Copyright 2025-TODAY Todooweb (www.todooweb.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    check_location = fields.Boolean(
        'Location', help='Location registered?', default=False,
    )
