# Copyright 2024-TODAY Todooweb (<http://www.todooweb.com>).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    'name': "Inventory Adjustment on Past Date",
    'version': '17.0.1.0.0',
    'category': 'Inventory/Inventory',
    'summary': """Module to set an inventory adjustment to a past date.""",
    'description': """This module allows you to create an inventory adjustment to a past date.""",
    'license': 'LGPL-3',
    'author': "Todooweb (www.todooweb.com)",
    'website': "https://todooweb.com/",
    'contributors': [
        "Idayana Basterreche <idayana11@gmail.com>",
        "Equipo Dev <devtodoo@gmail.com>",
        "Edgar Naranjo <edgarnaranjof@gmail.com>",
    ],
    'support': 'devtodoo@gmail.com',
    'depends': ['base', 'stock'],
    'data': [
        'views/stock_quant_views.xml',
    ],
    'images': ['static/description/screenshot_inventory.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
    'price': 9.99,
    'currency': 'EUR',
}
