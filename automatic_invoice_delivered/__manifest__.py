# Copyright 2024-TODAY Todooweb (www.todooweb.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    'name': 'Automatic Invoice Delivered',
    'version': "16.0.1.0.0",
    'summary': """Generate invoices automatically if deliveries are validated.""",
    'description': """This module automatically generates and posts invoices when deliveries are validated.""",
    'license': 'LGPL-3',
    'author': "ToDOO Web (www.todooweb.com)",
    'category': 'Accounting/Accounting',
    'website': "https://todooweb.com/",
    'contributors': [
        "Idayana Basterreche <idayana11@gmail.com>",
        "Equipo Dev <devtodoo@gmail.com>",
        "Edgar Naranjo <edgarnaranjof@gmail.com>",
    ],
    'support': 'devtodoo@gmail.com',
    'depends': [
        'base',
        'sale_management',
        'stock',
        'account'
    ],
    'data': ['views/res_config_settings_views.xml'],
    'images': [
       'static/description/screenshot_invoice.png'
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'price': 29.99,
    'currency': 'EUR',
}
