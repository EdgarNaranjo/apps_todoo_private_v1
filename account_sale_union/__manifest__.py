# Copyright 2025-TODAY Todooweb (https://todooweb.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
{
    'name': "Autocomplete in Invoice",
    'version': '19.0.1.0.0',
    'summary': """Union Invoice and Sale order""",
    'description': """[Add functionality] Module Union Invoice and Sale order""",
    'license': 'LGPL-3',
    'author': "ToDOO Web (www.todooweb.com)",
    'category': 'Extra Tools',
    'website': "https://todooweb.com/",
    'contributors': [
        "Idayana Basterreche <idayana11@gmail.com>",
        "Equipo Dev <devtodoo@gmail.com>",
        "Edgar Naranjo <edgarnaranjof@gmail.com>",
    ],
    'support': 'devtodoo@gmail.com',
    'depends': [
        'base',
        'mail',
        'account',
        'sale',
        'sale_management'
    ],
    'data': [
        'security/ir.model.access.csv',
        'report/sale_invoice_views.xml',
        'views/account_move_view.xml',
    ],
    'images': [
       'static/description/screen_invoice.png'
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'price': 49.99,
    'currency': 'EUR',
}
