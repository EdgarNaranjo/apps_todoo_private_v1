# Copyright 2024-TODAY Todooweb (www.todooweb.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': 'Procurement provision',
    'version': '17.0.1.0.0',
    'summary': 'Procurement provision: Purchase forecast for a given period.',
    'description': """[Automated] Procurement provision: Purchase forecast for a given period.""",
    'license': 'AGPL-3',
    'author': "ToDOO Web (www.todooweb.com)",
    'category': 'Purchase/Purchase',
    'website': "https://todooweb.com/",
    'contributors': [
        "Equipo Dev <devtodoo@gmail.com>",
        "Edgar Naranjo <edgarnaranjof@gmail.com>",
    ],
    'support': 'devtodoo@gmail.com',
    'depends': [
        'base',
        'purchase',
        'stock'
    ],
    'data': [
        'views/res_config_settings_views.xml'
    ],
    'images': [
       'static/description/screenshot_prevision.png'
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'price': 6.99,
    'currency': 'EUR',
}
