# coding: utf-8
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2025 Todooweb
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
    'name': "[Advance] Workflow Repair",
    'version': '16.0.1.0.2',
    'category': 'Industry/Services',
    'summary': '[Mechanical workshop] Improvements to the repair process.',
    'description': """[Mechanical workshop] Add new functionality to the repair process. Advance workflow repair.""",
    'license': 'LGPL-3',
    'author': "Todooweb (www.todooweb.com)",
    'website': "https://todooweb.com/",
    'contributors': [
        "Equipo Dev <devtodoo@gmail.com>",
        "Edgar Naranjo <edgarnaranjof@gmail.com>",
    ],
    'support': 'devtodoo@gmail.com',
    'depends': ['base', 'stock', 'contacts', 'account', 'repair'],
    "data": [
        "security/repair_security.xml",
        "security/ir.model.access.csv",
        "views/mrp_repair_view.xml",
        "views/repair_reason_view.xml",
        "views/repair_type_view.xml",
        "views/internal_state_view.xml",
        "views/res_config_settings_view.xml",
        "views/product_view.xml",
        "views/vehicle_brand_views.xml",
        "views/vehicle_fuel_views.xml",
        "views/vehicle_type_views.xml",
        "views/vehicle_model_views.xml",
        "views/vehicle_serial_views.xml",
        "wizards/stock_picking_wizard_views.xml",
        "wizards/order_wizard_views.xml",
        "data/model_data.xml",
        "report/sample_repair_order.xml",
        "report/report_repair_order_with_client_info.xml",
        "report/report_repair_order.xml",
    ],
    'images': ['static/description/screenshot_repair.png'],
    'installable': True,
    'auto_install': False,
    'application': True,
    'price': 219.99,
    'currency': 'EUR',
}
