# -*- coding: utf-8 -*-
# © 2016 Chafique DELLI @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.tests.common import TransactionCase


class TestSupplierInvoiceUpdateProductSupplierPrice(TransactionCase):
    def test_update_product_supplierprice_from_supplier_invoice(self):
        # supplier invoice with products to update
        invoice_0 = self.env.ref('account.demo_invoice_0')
        result = invoice_0.invoice_open()
        # open new form when products to update
        self.assertEquals(result['view_type'], 'form')
        self.assertEquals(result['res_model'],
                          'supplierinvoice.update.product.supplierprice')
        self.assertEquals(len(result['context']['default_wizard_line_ids']), 2)
        self.assertEquals(result['context']['default_wizard_line_ids'][0][2]
                          ['current_price_unit'], '-')
        self.assertEquals(result['context']['default_wizard_line_ids']
                          [0][2]['new_price_unit'], 10.0)
        self.assertEquals(result['context']['default_wizard_line_ids'][1][2]
                          ['current_price_unit'], '-')
        self.assertEquals(result['context']['default_wizard_line_ids'][1][2]
                          ['new_price_unit'], 4.0)
        self.assertEquals(result['type'], 'ir.actions.act_window')
        self.assertEquals(result['target'], 'new')
        vals = {
            'wizard_line_ids': result['context']['default_wizard_line_ids'],
        }
        wizard = (self.env['supplierinvoice.update.product.supplierprice'].
                  create(vals))
        # update supplier price of product
        (wizard.with_context(active_id=invoice_0.id).
         update_product_supplierprice())
        for line in wizard.wizard_line_ids:
            pricelist_partnerinfos = self.env['pricelist.partnerinfo'].search([
                ('suppinfo_id', '=', line.suppinfo_id.id),
                ('min_quantity', '=', 0.0),
                ('price', '=', line.new_price_unit)
            ])
            self.assertNotEquals(pricelist_partnerinfos, False)
