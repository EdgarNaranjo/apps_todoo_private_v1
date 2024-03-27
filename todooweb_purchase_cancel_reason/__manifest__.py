# Copyright 2024-TODAY Todooweb (www.todooweb.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    'name': 'Purchase Cancel Reason',
    'version': '17.0.1.0.0',
    'summary': 'Purchase Cancel Reason',
    'description': """Cancel Reasons in Purchase Order""",
    'license': 'AGPL-3',
    'author': "ToDOO Web (www.todooweb.com)",
    'maintainer': 'ToDOO Web (www.todooweb.com)',
    'category': 'Purchase',
    'website': "https://todooweb.com/",
    'complexity': 'normal',
    'contributors': [
        "Equipo Dev <devtodoo@gmail.com>",
        "Edgar Naranjo <edgarnaranjof@gmail.com>",
    ],
    'support': 'devtodoo@gmail.com',
    'depends': [
         'purchase'
    ],
    'data': [
        'data/purchase_order_cancel_reason.xml',
        'security/ir.model.access.csv',
        'wizard/purchase_cancel_reason_view.xml',
        'views/purchase_order.xml',
        'report/purchase_report_views.xml',
    ],
    'images': [
       'static/description/purchase_screenshot.png'
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'price': 5.99,
    'currency': 'EUR',
 }
