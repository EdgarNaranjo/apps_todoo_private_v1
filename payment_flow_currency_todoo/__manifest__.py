# -*- coding: utf-8 -*-

{
    'name': 'Payment Provider Currencies',
    'version': "16.0.1.0.1",
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
        'payment',
    ],
    'external_dependencies': {
        'python': [],
    },
    'data': [
        'views/payment_provider.xml',
    ],
    'images': [
       'static/description/screenshot_pay.png'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'price': 9.99,
    'currency': 'EUR',
}
