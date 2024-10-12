# Copyright 2024-TODAY Todooweb (www.todooweb.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    'name': "Scheduled Employee Changes",
    'version': "17.0.1.0.0",
    'summary': """Scheduled Changes to employee's record by a RH Manager.""",
    'description': """[Automation] Scheduled changes to employee's record: Company, Department, Job by a RH Manager.""",
    'license': 'LGPL-3',
    'author': "ToDOO Web (www.todooweb.com)",
    'category': 'Employee/Employee',
    'website': "https://todooweb.com/",
    'contributors': [
        "Equipo Dev <devtodoo@gmail.com>",
        "Edgar Naranjo <edgarnaranjof@gmail.com>",
    ],
    'support': 'devtodoo@gmail.com',
    'depends': [
        'base',
        'hr',
        'hr_skills',
        'planning',
        'hr_contract'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_view.xml',
        'data/change_data.xml',
    ],
    'images': [
       'static/description/screenshot_changes.png'
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'price': 39.99,
    'currency': 'EUR',
}
