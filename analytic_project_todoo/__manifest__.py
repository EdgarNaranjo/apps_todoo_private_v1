##############################################################################
#
#    # Copyright 2024-TODAY Todooweb (www.todooweb.com)
#    License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
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
    'name': "[Extended] Analytic Projects",
    'version': '17.0.1.0.0',
    'summary': """Analytic items from the "Project Overview" view.""",
    'description': """This module add Analytic items to the "Project Overview" view.""",
    'license': 'LGPL-3',
    'author': "ToDOO Web (www.todooweb.com)",
    'category': 'Project/Project',
    'website': "https://todooweb.com/",
    'contributors': [
        "Idayana Basterreche <idayana11@gmail.com>",
        "Equipo Dev <devtodoo@gmail.com>",
        "Edgar Naranjo <edgarnaranjof@gmail.com>",
    ],
    'support': 'devtodoo@gmail.com',
    'depends': ['base', 'project', 'account', 'analytic'],
    "data": [],
    'images': [
       'static/description/screenshot_project.png'
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'price': 5.99,
    'currency': 'EUR',
}
