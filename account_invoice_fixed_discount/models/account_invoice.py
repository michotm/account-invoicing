# -*- coding: utf-8 -*-
# Copyright 2017 Eficent Business and IT Consulting Services S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _
import openerp.addons.decimal_precision as dp
from openerp.exceptions import ValidationError


class AccountInvoiceTax(models.Model):
    _inherit = "account.invoice.tax"

    @api.model
    def compute(self, invoice):
        invoice.ensure_one()
        vals = {}
        for line in invoice.invoice_line.filtered('discount_fixed'):
            vals[line] = {
                'price_unit': line.price_unit,
                'discount_fixed': line.discount_fixed,
            }
            price_unit = line.price_unit - line.discount_fixed
            line.update({
                'price_unit': price_unit,
                'discount_fixed': 0.0,
            })
        tax_grouped = super(AccountInvoiceTax, self).compute(invoice)
        for line in vals.keys():
            line.update(vals[line])
        return tax_grouped


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    discount_fixed = fields.Float(
        string="Discount (Fixed)",
        digits=dp.get_precision('Product Price'),
        help="Fixed amount discount.")

    @api.onchange('discount')
    def _onchange_discount(self):
        if self.discount:
            self.discount_fixed = 0.0

    @api.onchange('discount_fixed')
    def _onchange_discount_fixed(self):
        if self.discount_fixed:
            self.discount = 0.0

    @api.multi
    @api.constrains('discount', 'discount_fixed')
    def _check_only_one_discount(self):
        for line in self:
            if line.discount and line.discount_fixed:
                raise ValidationError(
                    _("You can only set one type of discount per line."))

    @api.one
    @api.depends('price_unit', 'discount', 'invoice_line_tax_id', 'quantity',
                 'product_id', 'invoice_id.partner_id',
                 'invoice_id.currency_id', 'invoice_id.company_id',
                 'discount_fixed')
    def _compute_price(self):
        prev_price_unit = self.price_unit
        prev_discount_fixed = self.discount_fixed
        price_unit = self.price_unit - self.discount_fixed
        self.update({
            'price_unit': price_unit,
            'discount_fixed': 0.0,
        })
        super(AccountInvoiceLine, self)._compute_price()
        self.update({
            'price_unit': prev_price_unit,
            'discount_fixed': prev_discount_fixed,
        })

    @api.model
    def move_line_get(self, invoice_id):
        inv = self.env['account.invoice'].browse(invoice_id)
        vals = {}
        for line in inv.invoice_line.filtered('discount_fixed'):
            vals[line] = {
                'price_unit': line.price_unit,
                'discount_fixed': line.discount_fixed,
            }
            price_unit = line.price_unit - line.discount_fixed
            line.update({
                'price_unit': price_unit,
                'discount_fixed': 0.0,
            })
        res = super(AccountInvoiceLine, self).move_line_get(invoice_id)
        for line in vals.keys():
            line.update(vals[line])
        return res
