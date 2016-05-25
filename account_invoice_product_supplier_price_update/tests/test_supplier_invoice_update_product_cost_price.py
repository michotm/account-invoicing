# -*- coding: utf-8 -*-
# © 2016 Chafique DELLI @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.tests.common import TransactionCase


class TestSupplierInvoiceUpdateProductSupplierPrice(TransactionCase):
    def test_update_product_supplierprice_from_supplier_invoice(self):
        # supplier invoice with products to update
        invoice_0 = self.env.ref('account.demo_invoice_0')
        result = invoice_0.purchase_confirm()
        # open new form when products to update
        self.assertEquals(result['view_type'], 'form')
        self.assertEquals(result['res_model'],
                          'supplierinvoice.update.product.supplierprice')
        self.assertEquals(result['context']['default_invoice_line_ids'][0][2],
                          [39, 43])
        self.assertEquals(result['type'], 'ir.actions.act_window')
        self.assertEquals(result['target'], 'new')
        vals = {
            'invoice_line_ids': result['context']['default_invoice_line_ids'],
        }
        wizard = self.env['supplierinvoice.update.product.supplierprice'].create(
            vals)
        # update supplier price of product
        wizard.with_context(active_id=invoice_0.id).update_product_supplierprice()
        
        supplierinfo_ids = self.env['product.supplierinfo'].search([
            ('product_id', 'in',
             result['context']['default_product_ids'][0][2]),
            ('name', '=', purchase_7.partner_id.id)])
        self.assertNotEquals(supplierinfo_ids, False)
