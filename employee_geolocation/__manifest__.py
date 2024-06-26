# coding: utf-8
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2023 Todooweb
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
    'name': '[Attendance] Employee geolocation',
    'version': '16.0.1.0.0',
    'category': 'Human Resources',
    'summary': """Employee geolocation from attendance control.""",
    'description': """Employee geolocation from attendance control, every time I check in and out.""",
    'license': 'AGPL-3',
    'author': "Todooweb (www.todooweb.com)",
    'website': "https://todooweb.com/",
    'contributors': [
        "Equipo Dev <devtodoo@gmail.com>",
        "Edgar Naranjo <edgarnaranjof@gmail.com>",
    ],
    'external_dependencies': {
        'python': ['geocoder', 'device_detector', 'folium'],
    },
    'support': 'devtodoo@gmail.com',
    'depends': ['base', 'hr', 'hr_attendance'],
    'data': [
        'security/ir.model.access.csv',
        'security/employee_geolocation_security.xml',
        'views/hr_attendance_view.xml'
    ],
    # 'images': ['static/description/screenshot_lang.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
    'price': 39.99,
    'currency': 'EUR',
}
