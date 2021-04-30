# -*- coding: utf-8 -*

from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    check_location = fields.Boolean('Location', help='Location registered?', defaulf=False)


    def attendance_manual(self, next_action, entered_pin=False, location=None):
        res = super(HrEmployee, self.with_context(attendance_location=location)).attendance_manual(next_action, None)
        return res
    

    def attendance_action_change(self):
        res = super(HrEmployee, self).attendance_action_change()
        location = self.env.context.get('attendance_location', False)
        
        if location:
            if self.attendance_state == 'checked_in':
                res.write({
                    'latitude': location[0],
                    'longitude': location[1],
                })
            if self.attendance_state == 'checked_out':
                res.write({
                    'latitude': location[0],
                    'longitude': location[1],
                })
        return res
