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
    'name': 'Sale Commissions',
    'version': '13.0.1.0.0',
    'summary': 'Sales commissions for commercials',
    'description': """Sales commissions for commercials.""",
    'license': 'AGPL-3',
    'author': "ToDOO Web (www.todooweb.com)",
    'category': 'Sale',
    'website': "https://todooweb.com/",
    'contributors': [
        "Equipo Dev <devtodoo@gmail.com>",
        "Edgar Naranjo <edgarnaranjof@gmail.com>",
    ],
    'support': 'devtodoo@gmail.com',    
    'depends': ['base', 'sale'],
    'data': [
        'security/commission_security.xml',
        'security/ir.model.access.csv',
        'views/sale_commission_view.xml',
        'views/res_user_view.xml',
        'data/ir_sequence.xml',
        'data/ir_config_parameter.xml',
        'views/sale_order_view.xml',
    ],
    'images': [
       'static/description/screenshot_commision.png'
    ],
    'live_test_url': 'https://youtu.be/k0xzRVnY0cQ',
    'installable': True,
    'application': False,
    'auto_install': False,
    'price': 12.00,
    'currency': 'EUR',
}
