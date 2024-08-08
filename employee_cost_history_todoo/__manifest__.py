# Copyright 2024-TODAY Todooweb (www.todooweb.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    'name': "Employee Cost History",
    'version': '16.0.1.0.0',
    'category': 'Human Resources/Employees',
    'summary': 'Allows to update employee costs and track change history.',
    'description': 'Cost History: Allows to update employee costs and track change history.',
    'license': 'LGPL-3',
    'author': "Todooweb (www.todooweb.com)",
    'website': "https://todooweb.com/",
    'contributors': [
        "Idayana Basterreche <idayana11@gmail.com>",
        "Equipo Dev <devtodoo@gmail.com>",
        "Edgar Naranjo <edgarnaranjof@gmail.com>",
    ],
    'support': 'devtodoo@gmail.com',
    'depends': [
        'base',
        'hr',
        'analytic',
        'hr_timesheet'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_view.xml',
    ],
    'images': ['static/description/screenshot_cost.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
    'price': 29.99,
    'currency': 'EUR',
}
