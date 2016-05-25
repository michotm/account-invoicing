# -*- coding: utf-8 -*-
# © 2016 Chafique DELLI @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, api, _


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.model
    def _check_product_supplierprice(self):
        lines = []
        for line in self.invoice_line:
            current_price_unit = [(6, 0, [])]
            suppinfo = self.env['product.supplierinfo'].search([
                ('product_id', '=', line.product_id.id),
                ('name', '=', self.partner_id.id),
            ])
            if not suppinfo:
                suppinfo = self.env['product.supplierinfo'].create({
                    'name': self.partner_id.id,
                    'product_id': line.product_id.id,
                    'min_qty': 0.0,
                    'delay': 1,
                })
            for pricelist in suppinfo.pricelist_ids:
                current_price_unit[0][2].append(pricelist.price)
            if line.price_unit not in current_price_unit[0][2]:
                lines.append((0, 0, {
                    'name': line.name,
                    'current_price_unit': suppinfo.unit_price_note,
                    'new_price_unit': line.price_unit,
                    'suppinfo_id': suppinfo.id,
                }))
        return lines

    @api.multi
    def invoice_open(self):
        self.ensure_one()
        lines_for_update = self._check_product_supplierprice()
        if lines_for_update:
            ctx = dict(
                default_wizard_line_ids=lines_for_update,
            )
            update_product_supplierprice_form = self.env.ref(
                'account_invoice_product_supplier_price_update.'
                'view_supplierinvoice_update_product_supplierprice_form')
            return {
                'name': _("Update product supplier price with unit price "
                          "of this supplier invoice."),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'supplierinvoice.update.product.supplierprice',
                'views': [(update_product_supplierprice_form.id, 'form')],
                'view_id': update_product_supplierprice_form.id,
                'target': 'new',
                'context': ctx,
            }
        else:
            self.signal_workflow('invoice_open')
