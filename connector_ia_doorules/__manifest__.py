# coding: utf-8
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2026 Todooweb
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
    'name': 'DooRules AI Connector',
    'version': '18.0.1.0.0',
    'category': 'Administration',
    'summary': 'Connector for DooRules AI Rules Engine',
    'description': """
        This module adds a systray icon to quickly access DooRules AI
        for configuring rules based on the current Odoo context.
    """,
    'license': 'LGPL-3',
    'author': "Todooweb (www.todooweb.com)",
    'website': "https://todooweb.com/",
    'contributors': [
        "Equipo Dev <devtodoo@gmail.com>",
        "Edgar Naranjo <edgarnaranjof@gmail.com>",
    ],
    'support': 'devtodoo@gmail.com',
    'depends': ['web'],
    'data': [],
    'assets': {
        'web.assets_backend': [
            'connector_ia_doorules/static/src/systray/doorules_systray.js',
            'connector_ia_doorules/static/src/systray/doorules_systray.xml',
        ],
    },
    'images': ['static/description/screenshot_ia.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
    'price': 4.99,
    'currency': 'EUR',
}
