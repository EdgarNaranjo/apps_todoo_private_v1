# Copyright 2022-TODAY Rapsodoo Iberia S.r.L. (www.rapsodoo.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    'name': "Sale: Intercompany journal",
    'version': '16.0.0.0.0',
    'category': 'Extra Tools',
    'summary': """Sale: Journal configurator in intercompany sales""",
    'description': """Sale Journal configurator in intercompany sales. Journals: Convencials or Intercompany.""",
    'license': 'AGPL-3',
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
        'contacts',
        'account',
        'sale',
        'sale_management',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/intercompany_journal_view.xml',
    ],
    'images': ['static/description/screenshot_intercompany.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
    'price': 5.99,
    'currency': 'EUR',
}
