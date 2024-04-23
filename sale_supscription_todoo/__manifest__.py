# Copyright 2024-TODAY Todooweb (www.todooweb.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': '[Extended] Sale Subscription',
    'version': '17.0.1.0.0',
    'summary': 'Improvements in subscriptions.',
    'description': """Improvements in subscriptions: Invoice automation. Recurring invoices in draft status.""",
    'license': 'LGPL-3',
    'author': "ToDOO Web (www.todooweb.com)",
    'category': 'Sales/Sales',
    'website': "https://todooweb.com/",
    'contributors': [
        "Equipo Dev <devtodoo@gmail.com>",
        "Edgar Naranjo <edgarnaranjof@gmail.com>",
    ],
    'support': 'devtodoo@gmail.com',
    'depends': [
        'base',
        'sale',
        'sale_management',
        'sale_subscription'
    ],
    'images': [
       'static/description/screenshot_sale.png'
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'price': 4.99,
    'currency': 'EUR',
}
