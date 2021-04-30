# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Customer/Supplier Statement',
    'version': '14.1.1.1',
    'description': """
        Module to generate a "statement" of client and suppliers.
Customer account statement, balance, general ledger report, printed account statement, accounting reports, account statement reports, customer report, account statement, customer balance report, customer ledger report, customer balance ledger. Odoo Account Customer / Vendor Account Statement, Odoo Account Customer Account Statement, Customer Account Past Due, Customer Amount Due, Customer Payment Due, Customer Total Due, Customer Balance, Customer Balance vendor, partner ledger, vendor payment, vendor remaining balance, vendor balance, customer status, customer status, customer status, customer account statement, supplier account statement, customer bank statement.
""",
    'license': 'AGPL-3',
    'author': "ToDOO (www.todooweb.com)",
    'website': "https://todooweb.com/",
    'contributors': [
        "Equipo Dev <devtodoo@gmail.com>",
        "Edgar Naranjo <edgarnaranjof@gmail.com>",
    ],
    'support': 'devtodoo@gmail.com',
    'depends': [
        'base',
        'account',
    ],
    'data': [
            'security/ir.model.access.csv',
            'views/report.xml',
             'views/customer_statement_report.xml',
             'views/supplier_statement_report.xml',
             'views/res_partner_view.xml',
    ],
    'images': [
       'static/description/screenshot_statement.png'
    ],
    'live_test_url': 'https://youtu.be/tjgn9REPpOs',
    'installable': True,
    'application': True,
    'auto_install': False,
    'price': 29.99,
    'currency': 'EUR',
}
