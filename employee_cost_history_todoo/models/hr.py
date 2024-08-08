# Copyright 2024-TODAY Todooweb (www.todooweb.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import models, fields, tools, api, _
from odoo.exceptions import UserError
from odoo.tools.misc import clean_context


from datetime import date


class Employee(models.Model):
    _inherit = "hr.employee"

    cost_history_ids = fields.One2many(
        comodel_name='employee.cost.history',
        inverse_name='employee_id',
        string='Employee Cost History'
    )
    history_analytic_ids = fields.Many2many(
        comodel_name='account.analytic.line'
    )
    count_affected = fields.Integer(
        string='Affected Lines',
        compute='_count_affected_lines',
        store=True
    )

    @api.depends('history_analytic_ids', 'history_analytic_ids.is_changed_cost')
    def _count_affected_lines(self):
        for obj_employee in self:
            obj_employee.count_affected = len(obj_employee.history_analytic_ids.filtered(lambda l: l.is_changed_cost)) \
                if obj_employee.history_analytic_ids else 0

    def calc_history_cost(self, hist_cost):
        env_cost_history = self.env['employee.cost.history']
        env_account_analytic = self.env['account.analytic.line']
        rate_start = hist_cost.rate_start
        for record in self:
            result = []
            # search if there is a history cost greater than history cost created
            obj_cost_history = env_cost_history.search([('employee_id', '=', record.id),
                                                        ('rate_start', '>', rate_start)], limit=1)
            if obj_cost_history:
                # limit the search in the timesheet between the history created and the next history
                result = env_account_analytic.search([('employee_id', '=', record.id),
                                                      ('date', '>=', rate_start),
                                                      ('date', '<', obj_cost_history.rate_start)])
            else:
                # Search the entire timesheet with a date greater than or equal to the history cost date.
                result = env_account_analytic.search([('employee_id', '=', record.id),
                                                      ('date', '>=', rate_start)])
            if result:
                result.update({'is_changed_cost': True})
            record.history_analytic_ids += result

    def action_view_analytic_line(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("hr_timesheet.timesheet_action_all")
        action.update({
            'context': {'create': False},
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.history_analytic_ids.ids), ('is_changed_cost', '=', True)]
        })
        return action

    @api.model
    def update_analytic_line_tree(self):
        for record in self:
            record.action_update_analytic_line()

    def action_update_analytic_line(self):
        for record in self:
            for item in record.history_analytic_ids:
                amount_unit = item._employee_timesheet_cost()
                amount = amount_unit * item.unit_amount or 0.0
                result = (item.currency_id.round(amount) if item.currency_id else round(amount, 2)) * -1
                item.update({
                    'amount': result,
                    'is_changed_cost': False
                })

    @api.constrains('hourly_cost')
    def check_timesheet_cost_change(self):
        env_cost_history = self.env['employee.cost.history']
        for record in self:
            if record.hourly_cost:
                obj_cost_by_employee = env_cost_history.search([('employee_id', '=', record.id)])
                if obj_cost_by_employee:
                    filter_check = obj_cost_by_employee.filtered(lambda e: e.current_cost == record.hourly_cost)
                    filter_no_check = obj_cost_by_employee.filtered(lambda e: e.current_cost != record.hourly_cost)
                    if filter_check:
                        filter_check.last_register = True
                    if filter_no_check:
                        filter_no_check.last_register = False


class EmployeeCostHistory(models.Model):
    _name = "employee.cost.history"
    _description = "Employee Cost History"
    _order = 'rate_start DESC'

    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Employee',
        index=True
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        related='employee_id.currency_id',
        readonly=True
    )
    previous_cost = fields.Monetary(
        string='Previous Cost',
        currency_field='currency_id'
    )
    current_cost = fields.Monetary(
        string='Current Cost',
        currency_field='currency_id',
        required=True
    )
    rate_start = fields.Date(
        string='Rate Start',
        required=True
    )
    last_register = fields.Boolean('Last register')

    @api.onchange('employee_id', 'rate_start')
    def onchange_employee_id(self):
        env_cost_history = self.env['employee.cost.history']
        employee = self._context.get('employee_id')
        if employee:
            obj_employee = self.env['hr.employee'].search([('id', '=', employee)], limit=1)
        else:
            obj_employee = self.employee_id
        if obj_employee:
            self.employee_id = obj_employee.id
            self.previous_cost = obj_employee.hourly_cost
            if self.rate_start:
                # Previous history before the rate start
                previous_history = env_cost_history.search([('employee_id', '=', obj_employee.id),
                                                            ('rate_start', '<', self.rate_start)],
                                                           order='rate_start desc', limit=1)
                # First history after the rate start
                first_history = env_cost_history.search([('employee_id', '=', obj_employee.id),
                                                         ('rate_start', '>', self.rate_start)],
                                                        order='rate_start asc', limit=1)
                if previous_history:
                    self.previous_cost = previous_history.current_cost
                    if first_history:
                        first_history.update({'previous_cost': self.current_cost})
                elif not previous_history and first_history:
                    self.previous_cost = first_history.previous_cost
                    if self.current_cost > 0:
                        first_history.update({'previous_cost': self.current_cost})
                else:
                    self.previous_cost = obj_employee.hourly_cost

    @api.model
    def create(self, vals_list):
        env_cost_history = self.env['employee.cost.history']
        obj_cost_by_employee = env_cost_history.search([('employee_id', '=', vals_list['employee_id'])])
        sum_cost = obj_cost_by_employee
        res = super(EmployeeCostHistory, self).create(vals_list)
        if res:
            employee = res.employee_id
            sum_cost += res
            current_cost = employee.hourly_cost
            value_update = sum_cost.sorted('rate_start', reverse=False)[-1].current_cost
            res.onchange_employee_id()
            employee.hourly_cost = value_update
            if current_cost != value_update:
                employee.message_post(body='Employee cost updated: {}' .format(round(value_update, 2)))
            employee.calc_history_cost(res)
        return res


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    is_changed_cost = fields.Boolean(
        string='Is changed cost'
    )

    def _employee_timesheet_cost(self):
        self.ensure_one()
        timesheet_date = self.date
        employee = self.employee_id
        cost_history_env = self.env['employee.cost.history']
        # find if there is a history cost with a date less than or equal to the timesheet date
        cost_history_before = cost_history_env.search([('employee_id', '=', employee.id),
                                                       ('rate_start', '<=', timesheet_date)],
                                                      order='rate_start desc', limit=1)
        # search if there is a history cost with a date greater than the timesheet date
        cost_history_after = cost_history_env.search([('employee_id', '=', employee.id),
                                                     ('rate_start', '>', timesheet_date)],
                                                     order='rate_start asc', limit=1)
        if cost_history_before:
            # Return the first current cost from the employee's cost history because this would be the hourly_cost
            # value to the timesheet date
            return cost_history_before.current_cost
        elif not cost_history_before and cost_history_after:
            # Return the first previous cost from the employee's cost history because this would be the hourly_cost
            # value to the timesheet date
            return cost_history_after.previous_cost
        else:
            # if there is no history cost, it means that there is no change in the hourly_cost, and we must take
            # the current value
            return self.employee_id.hourly_cost or 0.0

