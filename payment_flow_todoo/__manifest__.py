# -*- coding: utf-8 -*-

{
    'name': 'Flow Payment Provider',
    'version': "17.0.1.0.1",
    'summary': 'Chilean Flow Payment Provider',
    'description': """Payment Provider: Chilean Flow Payment Provider""",
    'license': 'AGPL-3',
    'author': "ToDOO Web (www.todooweb.com)",
    'category': 'Website/Website',
    'website': "https://todooweb.com/",
    'contributors': [
        "Antonio David <antoniodavid8@gmail.com>",
        "Equipo Dev <devtodoo@gmail.com>",
        "Edgar Naranjo <edgarnaranjof@gmail.com>",
    ],
    'support': 'devtodoo@gmail.com',
    'depends': [
        'website',
        'account',
        'base',
        'payment_flow_currency_todoo',
    ],
    'external_dependencies': {
        'python': [
            'payflow',
        ],
    },
    'data': [
        'views/payment_flow_templates.xml',
        'views/payment_provider.xml',
        'views/payment_transaction.xml',
        'data/payment_provider_data.xml',
    ],
    'images': [
       'static/description/screenshot_pay.png'
    ],
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'installable': True,
    'application': True,
    'auto_install': False,
    'price': 59.99,
    'currency': 'EUR',
}
