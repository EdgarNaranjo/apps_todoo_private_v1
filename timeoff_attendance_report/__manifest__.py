# coding: utf-8
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2020 Todooweb
#    (<http://www.todooweb.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': "Time off and Attendance",
    'version': '16.0.1.0.2',
    'category': 'Project/Project',
    'summary': 'Time off and Attendance',
    'description': """Time off and Attendance by employee. View gantt and calendar""",
    'license': 'AGPL-3',
    'author': "Todooweb (www.todooweb.com)",
    'website': "https://todooweb.com/",
    'contributors': [
        "Equipo Dev <devtodoo@gmail.com>",
        "Edgar Naranjo <edgarnaranjof@gmail.com>",
    ],
    'support': 'devtodoo@gmail.com',
    'depends': [
        'base',
        'hr',
        'hr_holidays',
        'hr_skills',
        'hr_expense',
        'resource',
        'planning',
        'account',
        'account_accountant',
        'analytic',
        'timesheet_grid',
        'web_gantt'
    ],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'data/timeoff_data.xml',
        'report/hr_leave_attendance_report_calendar.xml'
    ],
    'images': ['static/description/time_screenshot.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
    'price': 11.99,
    'currency': 'EUR',
}
