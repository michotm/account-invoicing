# Copyright (C) 2021-TODAY Akretion
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # Make Invisible Invoice Button
    button_create_invoice_invisible = fields.Boolean(
        compute="_compute_get_button_create_invoice_invisible"
    )

    @api.depends("state", "order_line.invoice_status")
    def _compute_get_button_create_invoice_invisible(self):
        button_create_invoice_invisible = False

        lines = self.order_line.filtered(lambda l: l.invoice_status == "to invoice")

        # Only after Confirmed Sale Order the button appear
        if self.state != "sale":
            button_create_invoice_invisible = True
        else:
            if self.company_id.sale_create_invoice_policy == "stock_picking":
                # The creation of Invoice to Services should
                # be possible in Sale Order
                if not any(line.product_id.type == "service" for line in lines):
                    button_create_invoice_invisible = True
            else:
                # In the case of Sale Create Invoice Policy based on Sale Order
                # when the Button to Create Invoice clicked will be create
                # automatic Invoice for Products and Services
                if not lines:
                    button_create_invoice_invisible = True

        self.button_create_invoice_invisible = button_create_invoice_invisible
