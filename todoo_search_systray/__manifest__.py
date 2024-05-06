# Copyright 2024-TODAY Todooweb (<http://www.todooweb.com>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    'name': 'Global Advanced Search',
    'version': '16.0.1.0.1',
    'category': 'Extra Tools',
    'summary': """Advanced Search: Activate search in all odoo models.""",
    'description': """Global Advanced Search: Activate search in all odoo models.""",
    'license': 'AGPL-3',
    'author': "Todooweb (www.todooweb.com)",
    'website': "https://todooweb.com/",
    'contributors': [
        "Idayana Basterreche <idayana11@gmail.com>",
        "Equipo Dev <devtodoo@gmail.com>",
        "Edgar Naranjo <edgarnaranjof@gmail.com>",
    ],
    'support': 'devtodoo@gmail.com',
    'depends': ['base', 'web', 'sale'],
    'data': [
        'views/views_inherits.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'todoo_search_systray/static/src/js/systray.js',
            'todoo_search_systray/static/src/css/systray.css',
            'todoo_search_systray/static/src/xml/systray.xml',
        ],
    },
    'images': ['static/description/screenshot_search.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
    'price': 29.99,
    'currency': 'EUR',
}