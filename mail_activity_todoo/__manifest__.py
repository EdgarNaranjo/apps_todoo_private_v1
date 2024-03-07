# Copyright 2024-TODAY Todooweb (<http://www.todooweb.com>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    'name': 'Management Mass Activities',
    'version': '17.0.1.0.0',
    'category': 'CRM',
    'summary': """Management Mass Activities: Activities by user and channels.""",
    'description': """Management Mass Activities: Activities by users and channels. Activities related to each other.""",
    'license': 'AGPL-3',
    'author': "Todooweb (www.todooweb.com)",
    'website': "https://todooweb.com/",
    'contributors': [
        "Idayana Basterreche <idayana11@gmail.com>",
        "Equipo Dev <devtodoo@gmail.com>",
        "Edgar Naranjo <edgarnaranjof@gmail.com>",
    ],
    'support': 'devtodoo@gmail.com',
    'depends': ['base', 'mail'],
    'data': [
        'views/mail_channel_views.xml',
    ],
    'images': ['static/description/screenshot_activity.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
    'price': 29.99,
    'currency': 'EUR',
}
