# Copyright 2025-TODAY Todooweb (<http://www.todooweb.com>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    'name': 'Global Advanced Search',
    'version': '19.0.1.0.2',
    'category': 'Extra Tools',
    'summary': 'Advanced Search: Activate search in all odoo models.',
    'sequence': 10,
    'description': """
Global Advanced Search for Odoo 19
==================================
This module provides a powerful search bar in the Odoo Systray (top bar).
Features:
---------
* Search in any Odoo model.
* Fast response using OWL framework.
* Search history.
* Keyboard shortcuts (Ctrl+K).
    """,
    'author': "Todooweb (www.todooweb.com)",
    'website': "https://todooweb.com/",
    'license': 'AGPL-3',
    'depends': [
        'base',
        'web',
    ],
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
    'application': False,
    'auto_install': False,
    'price': 35.99,
    'currency': 'EUR',
}
