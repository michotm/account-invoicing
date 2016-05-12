# -*- coding: utf-8 -*-
# © 2016 Chafique DELLI @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Account Invoice Product Cost Price Update',
    'summary': 'From the supplier invoice, to automatic update all products '
               'whose unit price on the line is different from the cost price',
    'version': '8.0.1.0.0',
    'category': 'Accounting & Finance',
    'website': 'http://akretion.com',
    'author': 'Akretion, Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'application': False,
    'installable': True,
    'depends': [
        'account',
    ],
    'data': [
        'account_invoice_view.xml',
        'wizard/supplier_invoice_update_product_cost_price.xml'
    ]
}
