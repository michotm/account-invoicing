# -*- coding: utf-8 -*-
# © 2016 Chafique DELLI @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, api, fields
import openerp.addons.decimal_precision as dp


class SupplierinvoiceUpdateProductSupplierprice(models.TransientModel):
    _name = 'supplierinvoice.update.product.supplierprice'

    wizard_line_ids = fields.One2many(
        'supplierinvoice.update.product.supplierprice.line',
        'wizard_id',
        string='Wizard lines')

    @api.multi
    def update_product_supplierprice(self):
        invoice = self.env['account.invoice'].browse(
            self._context['active_id'])
        invoice.signal_workflow('invoice_open')
        for line in self.wizard_line_ids:
            pricelist_partnerinfos = self.env['pricelist.partnerinfo'].search([
                ('suppinfo_id', '=', line.suppinfo_id.id),
            ])
            if pricelist_partnerinfos:
                pricelist_partnerinfos[0].write({
                    'min_quantity': 0.0,
                    'price': line.new_price_unit,
                })
            else:
                vals = {
                    'suppinfo_id': line.suppinfo_id.id,
                    'min_quantity': 0.0,
                    'price': line.new_price_unit,
                }
                self.env['pricelist.partnerinfo'].create(vals)


class SupplierinvoiceUpdateProductSupplierpriceLine(models.TransientModel):
    _name = 'supplierinvoice.update.product.supplierprice.line'

    wizard_id = fields.Many2one(
        'supplierinvoice.update.product.supplierprice',
        string='Wizard Reference')
    name = fields.Text(string='Description', required=True)
    new_price_unit = fields.Float(string='New Unit Price',
                                  digits=dp.get_precision('Product Price'))
    current_price_unit = fields.Char(string='Current Unit Price')
    suppinfo_id = fields.Many2one('product.supplierinfo',
                                  string='Partner Information')
