##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2013 OpenERP S.A. (<http://openerp.com>).
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
    'name': 'Restrict Multiple Sign in for Same User',
    'version': '13.0.0.1',
    'category': 'Tools',
    'description': """Restrict Multiple Sign in for Same User""",
    'author': "ToDOO Web (www.todooweb.com)",
    'support': 'devtodoo@gmail.com',
    'website': "https://todooweb.com/",
    'license': 'AGPL-3',
    'contributors': [
        "Equipo Dev <devtodoo@gmail.com>",
        "Edgar Naranjo <edgarnaranjof@gmail.com>",
    ],
    'depends': ['base', 'resource', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_users_view.xml',
        'views/webclient_templates.xml',
        'data/scheduler.xml'
    ],
    'images': [
        'static/description/screenshot_user.png'
    ],
    'live_test_url': 'https://youtu.be/qyO_jEj6dBY',
    'installable': True,
    'application': False,
    'auto_install': False,
    'price': 9.99,
    'currency': 'EUR',
}
