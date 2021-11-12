# Copyright (C) 2021-TODAY Akretion
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Sales Stock Picking Invocing",
    "category": "Warehouse Management",
    "license": "AGPL-3",
    "author": "Akretion, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-invoicing",
    "version": "14.0.1.0.0",
    "maintainers": ["mbcosta"],
    "depends": [
        "sale_management",
        "stock_picking_invoicing",
    ],
    "data": [
        "views/res_company_view.xml",
        "views/res_config_settings_view.xml",
        "views/sale_order_view.xml",
    ],
    "demo": [
        "demo/sale_order_demo.xml",
    ],
    "installable": True,
    "auto_install": True,
}
