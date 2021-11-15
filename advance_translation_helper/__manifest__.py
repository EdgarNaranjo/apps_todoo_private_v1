# coding: utf-8
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2020 Todooweb
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
    'name': '[Advanced] Tool Translation: File ".po"',
    'version': '15.1.1.0.0',
    'category': 'Extra Tools',
    'summary': """Translate base odoo file '.po' with the help of Google Translate.""",
    'description': """Translate the base odoo file '.po' with the help of Google Translate, in all necessary languages.""",
    'license': 'AGPL-3',
    'author': "Todooweb (www.todooweb.com)",
    'website': "https://todooweb.com/",
    'contributors': [
        "Equipo Dev <devtodoo@gmail.com>",
        "Edgar Naranjo <edgarnaranjof@gmail.com>",
    ],
    'support': 'devtodoo@gmail.com',
    'depends': ['base', 'mail', 'todoo_translation_helper'],
    'external_dependencies': {'python': ['googletrans', 'unidecode']},
    'data': [
        'views/advance_todoo_translation_helper.xml',
    ],
    'images': ['static/description/translate_screenshot.png'],
    'live_test_url': 'https://cutt.ly/iRkZanw',
    'installable': True,
    'auto_install': False,
    'application': True,
    'price': 8.99,
    'currency': 'EUR',
}