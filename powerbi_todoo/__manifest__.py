# coding: utf-8
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2024 Todooweb
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
    'name': 'Power BI Connector',
    'version': '16.0.1.0.1',
    'category': 'Tools/Tools',
    'summary': """Odoo Power BI Connector""",
    'description': """Connected odoo in Power BI: RRHH, Proyect, Sales, Purchase, Accounting""",
    'license': 'LGPL-3',
    'author': "Todooweb (www.todooweb.com)",
    'website': "https://todooweb.com/",
    'contributors': [
        "Equipo Dev <devtodoo@gmail.com>",
        "Edgar Naranjo <edgarnaranjof@gmail.com>",
    ],
    'support': 'devtodoo@gmail.com',
    'depends': [
        'base',
        'documents'
    ],
    'data': [
        'security/powerbi_security.xml',
        'security/ir.model.access.csv',
        'views/constructor_power_bi_views.xml',
        'data/powerbi_data.xml',
    ],
    'images': ['static/description/screenshot_bi.png'],
    'installable': True,
    'auto_install': False,
    'application': True,
    'price': 99.99,
    'currency': 'EUR',
}
