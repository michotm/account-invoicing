# Copyright (C) 2021-TODAY Akretion
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _prepare_procurement_values(self, group_id=False):
        values = super()._prepare_procurement_values(group_id)
        if self.order_id.company_id.sale_create_invoice_policy == "stock_picking":
            values["invoice_state"] = "2binvoiced"

        return values

    # no trigger product_id.invoice_policy to avoid retroactively changing SO
    @api.depends("qty_invoiced", "qty_delivered", "product_uom_qty", "order_id.state")
    def _get_to_invoice_qty(self):
        """
        Compute the quantity to invoice. If the invoice policy is order,
        the quantity to invoice is calculated from the ordered quantity.
        Otherwise, the quantity delivered is used.
        """
        super()._get_to_invoice_qty()

        for line in self:
            if line.order_id.state in ["sale", "done"]:
                if line.product_id.invoice_policy == "order":
                    if (
                        line.order_id.company_id.sale_create_invoice_policy
                        == "stock_picking"
                        and line.product_id.type == "product"
                    ):
                        # HACK: To force create invoice for products in the
                        # stock picking, even when Product invoice_policy
                        # defined to 'order'.
                        # The button 'Create Invoice' in sale_order just
                        # work to create service lines in this case.
                        # TODO: The case of Product invoice_policy
                        #  defined to 'order' should be functional
                        #  in sale_order?
                        line.qty_to_invoice = 0
