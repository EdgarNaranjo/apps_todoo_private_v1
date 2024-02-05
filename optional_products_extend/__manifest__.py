# Copyright 2024-TODAY Todooweb (www.todooweb.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    'name': '[Extended] Optional Products',
    'version': '16.0.1.0.0',
    'summary': 'Improvements to the Optional Products view.',
    'description': """Improvements to the Optional Products view: Margin, Margin (%), Cost and Subtotal""",
    'license': 'AGPL-3',
    'author': "ToDOO Web (www.todooweb.com)",
    'category': 'Sales',
    'website': "https://todooweb.com/",
    'contributors': [
        "Equipo Dev <devtodoo@gmail.com>",
        "Edgar Naranjo <edgarnaranjof@gmail.com>",
    ],
    'support': 'devtodoo@gmail.com',
    'depends': [
        'base',
        'sale',
        'sale_management'
    ],
    'data': [
        'views/views_inherit.xml',
        'reports/order_report.xml'
    ],
    'images': [
       'static/description/screenshot_ftp.png'
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'price': 4.99,
    'currency': 'EUR',
}
