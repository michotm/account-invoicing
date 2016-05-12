# -*- coding: utf-8 -*-
# © 2016 Chafique DELLI @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, api, fields, _


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.model
    def _check_product_costprice(self):
        lines = []
        for line in self.invoice_line:
            if line.price_unit != line.product_id.standard_price:
                lines.append(line.id)
        return lines

    @api.multi
    def invoice_open(self):
        self.ensure_one()
        lines_for_update = []
        lines_for_update = self._check_product_costprice()
        if lines_for_update:
            ctx = dict(
                default_invoice_line_ids=[(6, 0, lines_for_update)],
            )
            update_product_costprice_form = self.env.ref(
                'account_invoice_product_cost_price_update.'
                'view_supplierinvoice_update_product_costprice_form', False)
            return {
                'name': _("Update product cost price with unit price "
                          "of this supplier invoice."),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'supplierinvoice.update.product.costprice',
                'views': [(update_product_costprice_form.id, 'form')],
                'view_id': update_product_costprice_form.id,
                'target': 'new',
                'context': ctx,
            }
        else:
            self.signal_workflow('invoice_open')


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    standard_price = fields.Float(related='product_id.standard_price',
                                  string='Product cost price')
