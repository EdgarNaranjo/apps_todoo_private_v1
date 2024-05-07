# Copyright 2024-TODAY Todooweb (<http://www.todooweb.com>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).


from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HolidaysRequest(models.Model):
    _inherit = "hr.leave"

    @api.constrains('state', 'employee_ids', 'date_from', 'date_to')
    def check_leave_by_employee(self):
        env_report = self.env['hr.leave.attendance.report']
        for record in self:
            if record.employee_ids and record.state in ['validate', 'validate1', 'refuse']:
                for employee in record.employee_ids:
                    obj_report_ids = env_report.search([('employee_id', '=', employee.id),
                                                        ('start_datetime', '>=', record.date_from),
                                                        ('start_datetime', '<=', record.date_to)])
                    if obj_report_ids:
                        for report in obj_report_ids:
                            if record.state in ['validate', 'validate1']:
                                report.write({'on_holiday': True, 'on_attendance': False})
                            if record.state == 'refuse':
                                report.write({'on_holiday': False, 'on_attendance': True})

