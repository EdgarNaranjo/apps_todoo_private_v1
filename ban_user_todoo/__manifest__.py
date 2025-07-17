# Copyright 2025-TODAY Todooweb (https://todooweb.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
{
    'name': "Ban/Block Users",
    'version': '17.0.1.0.0',
    'summary': """Ban/Block Users Configurable""",
    'description': """Ban/Block Users from Backend.""",
    'license': 'LGPL-3',
    'author': "ToDOO Web (www.todooweb.com)",
    'category': 'Extra Tools',
    'website': "https://todooweb.com/",
    'contributors': [
        "Equipo Dev <devtodoo@gmail.com>",
        "Edgar Naranjo <edgarnaranjof@gmail.com>",
    ],
    'support': 'devtodoo@gmail.com',
    'depends': [
        'base',
        'mail',
        'web',
        'bus'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/res_users_views.xml',
        'wizard/ban_user_wizard_views.xml',
    ],
    'images': [
      'static/description/screenshot_blocked.png'
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'price': 19.99,
    'currency': 'EUR',
}

