# Copyright 2024-TODAY Todooweb (www.todooweb.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    'name': 'Account Dashboard',
    'version': '16.0.1.0.6',
    'category': 'Accounting',
    'summary': 'Accounting Dashboard: Improved Accounting View.',
    'description': 'Accounting Dashboard: Enhanced accounting view to aid decision making.',
    'license': 'LGPL-3',
    'author': "Todooweb (www.todooweb.com)",
    'website': "https://todooweb.com/",
    'contributors': [
        "Antonio David <antoniodavid8@gmail.com>",
        "Equipo Dev <devtodoo@gmail.com>",
        "Edgar Naranjo <edgarnaranjof@gmail.com>",
    ],
    'support': 'devtodoo@gmail.com',
    'depends': ['account_accountant'],
    'data': [
        'data/ir.config_parameter.xml',
        'data/account_year_month_cron.xml',
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/account_year.xml',
        'views/dashboard.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'account_dashboard/static/src/**/*',
        ],
    },
    'images': ['static/description/screenshot_dash.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
    'price': 49.99,
    'currency': 'EUR',
}
