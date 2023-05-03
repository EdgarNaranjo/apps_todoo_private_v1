# Copyright 2022-TODAY Rapsodoo Iberia S.r.L. (www.rapsodoo.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    'name': "Accounting: Intercompany journal",
    'version': '16.0.0.0.1',
    'category': 'Extra Tools',
    'summary': """Accounting: Journal configurator in intercompany sales""",
    'description': """Journal configurator in intercompany sales and purchase. Journals: Intercompany.""",
    'license': 'GPL-3',
    'author': "Todooweb (www.todooweb.com)",
    'website': "https://todooweb.com/",
    'contributors': [
        "Equipo Dev <devtodoo@gmail.com>",
        "Edgar Naranjo <edgarnaranjof@gmail.com>",
    ],
    'support': 'devtodoo@gmail.com',
    'depends': [
        'base',
        'base_vat',
        'mail',
        'account',
        'account_accountant',
        'sale',
        'sale_management',
        'todooweb_intercompany_journal'
    ],
    'data': [
        'security/groups.xml',
        'views/inherit_intercompany_journal_view.xml',
    ],
    'images': ['static/description/screenshot_intercompany.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
    'price': 10.99,
    'currency': 'EUR',
}
