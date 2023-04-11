# coding: utf-8
##############################################################################
#    OpenERP, Open Source Management Solution
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
    'name': '[Advanced] Status Session Users',
    'version': '16.0.0.1',
    'category': 'Tools',
    'description': """[Advanced] Status Session Users. Inactive, Active. Online or Offline. Notifications to managers.""",
    'author': "ToDOO Web (www.todooweb.com)",
    'support': 'devtodoo@gmail.com',
    'website': "https://todooweb.com/",
    'license': 'AGPL-3',
    'contributors': [
        "Equipo Dev <devtodoo@gmail.com>",
        "Edgar Naranjo <edgarnaranjof@gmail.com>",
    ],
    'depends': ['base', 'hr', 'hr_attendance', 'crm', 'sale', 'purchase', 'account', 'status_user_todoo'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/res_users_view.xml',
        'data/sessions_data.xml'
    ],
     'images': [
         'static/description/screenshot_status.png'
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'price': 9.0,
    'currency': 'EUR',

}
