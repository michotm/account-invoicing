# -*- coding: utf-8 -*-
# © 2016 Chafique DELLI @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, api, fields


class SupplierinvoiceUpdateProductCostprice(models.TransientModel):
    _name = 'supplierinvoice.update.product.costprice'
    _description = 'Update Product Cost Price from Supplier Invoice'

    invoice_line_ids = fields.Many2many(comodel_name='account.invoice.line',
                                        relation='invoice_line_update_product',
                                        string='Invoice lines')

    @api.multi
    def update_product_costprice(self):
        invoice = self.env['account.invoice'].browse(
            self._context['active_id'])
        invoice.signal_workflow('invoice_open')
        for line in self.invoice_line_ids:
            line.product_id.write({'standard_price': line.price_unit})
