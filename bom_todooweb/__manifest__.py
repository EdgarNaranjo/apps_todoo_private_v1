# coding: utf-8
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2021 Todooweb
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
    'name': 'Bill of materials (Parents & childrens)',
    'version': '15.0.1.0.0',
    'summary': 'MRP BoM: Bill of materials (Parents & childrens)',
    'description': """Bill of materials: Modify the stock of parent products when the stock of the children is modified.""",
    'license': 'AGPL-3',
    'author': "ToDOO Web (www.todooweb.com)",
    'category': 'Manufacturing',
    'website': "https://todooweb.com/",
    'contributors': [
        "Equipo Dev <devtodoo@gmail.com>",
        "Edgar Naranjo <edgarnaranjof@gmail.com>",
    ],
    'support': 'devtodoo@gmail.com',    
    'depends': ['base', 'stock', 'mrp'],
    'data': [
        'views/mrp_bom_views.xml'
    ],
    'images': [
       'static/description/screenshot_bom.png'
    ],
    'live_test_url': 'https://cutt.ly/bcTOKcl',
    'installable': True,
    'application': False,
    'auto_install': False,
    'price': 10.99,
    'currency': 'EUR',
}
