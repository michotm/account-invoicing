# Copyright (C) 2021-TODAY Akretion
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import Form, SavepointCase, tagged


@tagged("post_install", "-at_install")
class TestSaleStock(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.account_move_model = cls.env["account.move"]
        cls.invoice_wizard = cls.env["stock.invoice.onshipping"]
        cls.stock_return_picking = cls.env["stock.return.picking"]
        cls.stock_picking = cls.env["stock.picking"]

    def test_01_sale_stock_return(self):
        """
        Test a SO with a product invoiced on delivery. Deliver and invoice
        the SO, then do a return of the picking. Check that a refund
         invoice is well generated.
        """
        # intial so
        self.partner = self.env.ref(
            "sale_stock_picking_invoicing.res_partner_2_address"
        )
        self.product = self.env.ref("product.product_delivery_01")
        so_vals = {
            "partner_id": self.partner.id,
            "partner_invoice_id": self.partner.id,
            "partner_shipping_id": self.partner.id,
            "order_line": [
                (
                    0,
                    0,
                    {
                        "name": self.product.name,
                        "product_id": self.product.id,
                        "product_uom_qty": 3.0,
                        "product_uom": self.product.uom_id.id,
                        "price_unit": self.product.list_price,
                    },
                )
            ],
            "pricelist_id": self.env.ref("product.list0").id,
        }
        self.so = self.env["sale.order"].create(so_vals)

        # confirm our standard so, check the picking
        self.so.action_confirm()
        self.assertTrue(
            self.so.picking_ids,
            'Sale Stock: no picking created for "invoice on '
            'delivery" storable products',
        )

        # set stock.picking to be invoiced
        self.assertTrue(
            len(self.so.picking_ids) == 1,
            "More than one stock " "picking for sale.order",
        )
        self.so.picking_ids.set_to_be_invoiced()

        # validate stock.picking
        stock_picking = self.so.picking_ids

        # compare sale.order.line with stock.move
        stock_move = stock_picking.move_lines
        sale_order_line = self.so.order_line

        sm_fields = [key for key in self.env["stock.move"]._fields.keys()]
        sol_fields = [key for key in self.env["sale.order.line"]._fields.keys()]

        skipped_fields = [
            "id",
            "display_name",
            "state",
            # Price Unit in move is different from sale line
            # TODO: Should be equal? After Confirmed stock picking
            #  the value will be change based Stock Valuation
            #  configuration.
            "price_unit",
        ]
        common_fields = list(set(sm_fields) & set(sol_fields) - set(skipped_fields))

        for field in common_fields:
            self.assertEqual(
                stock_move[field],
                sale_order_line[field],
                "Field %s failed to transfer from "
                "sale.order.line to stock.move" % field,
            )

    def test_picking_sale_order_product_and_service(self):
        """
        Test Sale Order with product and service
        """

        sale_order_2 = self.env.ref(
            "sale_stock_picking_invoicing.main_so_sale_stock_picking_invoicing_2"
        )
        sale_order_2.action_confirm()
        self.assertTrue(sale_order_2.state == "sale")
        self.assertTrue(sale_order_2.invoice_status == "to invoice")
        # Method to create invoice in sale order should work only
        # for lines where products are of TYPE Service
        sale_order_2._create_invoices()
        # Should be exist one Invoice
        self.assertEqual(1, sale_order_2.invoice_count)
        for invoice in sale_order_2.invoice_ids:
            for line in invoice.invoice_line_ids:
                self.assertEqual(line.product_id.type, "service")
            # Invoice of Service
            invoice.action_post()
            self.assertEqual(
                invoice.state, "posted", "Invoice should be in state Posted"
            )

        picking = sale_order_2.picking_ids
        # Check product availability
        picking.action_assign()
        # Only the line of Type Product
        self.assertEqual(len(picking.move_ids_without_package), 1)
        self.assertEqual(picking.invoice_state, "2binvoiced")
        # Force product availability
        for move in picking.move_ids_without_package:
            move.quantity_done = move.product_uom_qty
            # Used to compare fields from sale.order.line
            # and invoice.line
            sale_order_line = move.sale_line_id

        picking.button_validate()
        self.assertEqual(picking.state, "done")
        wizard_obj = self.invoice_wizard.with_context(
            active_ids=picking.ids,
            active_model=picking._name,
            active_id=picking.id,
        )
        fields_list = wizard_obj.fields_get().keys()
        wizard_values = wizard_obj.default_get(fields_list)
        wizard = wizard_obj.create(wizard_values)
        wizard.onchange_group()
        wizard.action_generate()
        domain = [("picking_ids", "=", picking.id)]
        invoice = self.account_move_model.search(domain)
        self.assertEqual(picking.invoice_state, "invoiced")
        self.assertIn(invoice, picking.invoice_ids)
        self.assertIn(picking, invoice.picking_ids)
        # Picking with Partner Shipping from Sale Order
        self.assertEqual(picking.partner_id, sale_order_2.partner_shipping_id)
        # Invoice created with Partner Invoice from Sale Order
        self.assertEqual(invoice.partner_id, sale_order_2.partner_invoice_id)
        # Invoice created with Partner Shipping from Picking
        self.assertEqual(invoice.partner_shipping_id, picking.partner_id)
        # When informed Payment Term in Sale Orde should be
        # used instead of the default in Partner.
        self.assertEqual(invoice.invoice_payment_term_id, sale_order_2.payment_term_id)

        # Only the type of Product should be created
        self.assertEqual(len(invoice.invoice_line_ids), 1)

        # In the Sale Order should be exist two Invoices, one
        # for Product other for Service
        self.assertEqual(2, sale_order_2.invoice_count)

        # Confirm Invoice
        invoice.action_post()
        self.assertEqual(invoice.state, "posted", "Invoice should be in state Posted.")

        # Check Invoiced QTY
        for line in sale_order_2.order_line:
            # Check Product line
            if line.product_id.type == "product":
                self.assertEqual(line.product_uom_qty, line.qty_invoiced)

        # Check if the Sale Lines fields are equals to Invoice Lines
        sol_fields = [key for key in self.env["sale.order.line"]._fields.keys()]

        acl_fields = [key for key in self.env["account.move.line"]._fields.keys()]

        skipped_fields = [
            "id",
            "display_name",
            "state",
            "create_date",
            # By th TAX 15% automatic add in invoice the value change
            "price_total",
        ]

        common_fields = list(set(acl_fields) & set(sol_fields) - set(skipped_fields))
        invoice_lines = picking.invoice_ids.invoice_line_ids

        for field in common_fields:
            self.assertEqual(
                sale_order_line[field],
                invoice_lines[field],
                "Field %s failed to transfer from "
                "sale.order.line to account.invoice.line" % field,
            )

        # Return Picking
        return_wizard_form = Form(
            self.stock_return_picking.with_context(
                dict(active_id=picking.id, active_model="stock.picking")
            )
        )
        return_wizard_form.invoice_state = "2binvoiced"
        self.return_wizard = return_wizard_form.save()

        result_wizard = self.return_wizard.create_returns()
        self.assertTrue(result_wizard, "Create returns wizard fail.")
        picking_devolution = self.env["stock.picking"].browse(
            result_wizard.get("res_id")
        )

        self.assertEqual(picking_devolution.invoice_state, "2binvoiced")
        for line in picking_devolution.move_lines:
            self.assertEqual(line.invoice_state, "2binvoiced")

        picking_devolution.action_confirm()
        picking_devolution.action_assign()
        # Force product availability
        for move in picking_devolution.move_ids_without_package:
            move.quantity_done = move.product_uom_qty
        picking_devolution.button_validate()
        self.assertEqual(picking_devolution.state, "done", "Change state fail.")
        wizard_obj = self.invoice_wizard.with_context(
            active_ids=picking_devolution.ids,
            active_model=picking_devolution._name,
            active_id=picking_devolution.id,
        )
        fields_list = wizard_obj.fields_get().keys()
        wizard_values = wizard_obj.default_get(fields_list)
        wizard = wizard_obj.create(wizard_values)
        wizard.onchange_group()
        wizard.action_generate()
        domain = [("picking_ids", "=", picking_devolution.id)]
        invoice_devolution = self.account_move_model.search(domain)
        # Confirm Invoice
        invoice_devolution.action_post()
        self.assertEqual(
            invoice_devolution.state, "posted", "Invoice should be in state Posted"
        )
        # Check Invoiced QTY update after Refund
        for line in sale_order_2.order_line:
            # Check Product line
            if line.product_id.type == "product":
                # The Invoiced QTY should be Zero by Refund
                self.assertEqual(0.0, line.qty_invoiced)

    def test_picking_invoicing_partner_shipping_invoiced(self):
        """
        Test the invoice generation grouped by partner/product with 2
        picking and 2 moves per picking, but Partner to Shipping is
        different from Partner to Invoice.
        """
        sale_order_1 = self.env.ref(
            "sale_stock_picking_invoicing.main_so_sale_stock_picking_invoicing_1"
        )
        sale_order_1.action_confirm()
        picking = sale_order_1.picking_ids
        picking.action_confirm()
        # Check product availability
        picking.action_assign()
        # Force product availability
        for move in picking.move_ids_without_package:
            move.quantity_done = move.product_uom_qty
        picking.button_validate()

        sale_order_2 = self.env.ref(
            "sale_stock_picking_invoicing.main_so_sale_stock_picking_invoicing_2"
        )
        sale_order_2.action_confirm()
        picking2 = sale_order_2.picking_ids
        # Check product availability
        picking2.action_assign()
        # Force product availability
        for move in picking2.move_ids_without_package:
            move.quantity_done = move.product_uom_qty
        picking2.button_validate()
        self.assertEqual(picking.state, "done")
        self.assertEqual(picking2.state, "done")
        pickings = picking | picking2
        wizard_obj = self.invoice_wizard.with_context(
            active_ids=pickings.ids,
            active_model=pickings._name,
        )
        fields_list = wizard_obj.fields_get().keys()
        wizard_values = wizard_obj.default_get(fields_list)
        # One invoice per partner but group products
        wizard_values.update(
            {
                "group": "partner_product",
            }
        )
        wizard = wizard_obj.create(wizard_values)
        wizard.onchange_group()
        wizard.action_generate()
        domain = [("picking_ids", "in", (picking.id, picking2.id))]
        invoice = self.account_move_model.search(domain)
        # Groupping Invoice
        self.assertEqual(len(invoice), 1)
        self.assertEqual(picking.invoice_state, "invoiced")
        self.assertEqual(picking2.invoice_state, "invoiced")
        # Invoice should be create with the partner_invoice_id
        self.assertEqual(invoice.partner_id, sale_order_1.partner_invoice_id)
        # Invoice partner shipping should be the same of picking
        self.assertEqual(invoice.partner_shipping_id, picking.partner_id)
        self.assertIn(invoice, picking.invoice_ids)
        self.assertIn(picking, invoice.picking_ids)
        self.assertIn(invoice, picking2.invoice_ids)
        self.assertIn(picking2, invoice.picking_ids)

        # Grouping sale line with KEY
        self.assertEqual(len(invoice.invoice_line_ids), 2)
        for inv_line in invoice.invoice_line_ids:
            self.assertTrue(inv_line.tax_ids, "Error to map Sale Tax in invoice.line.")

    def test_ungrouping_pickings_partner_shipping_different(self):
        """
        Test the invoice generation grouped by partner/product with 3
        picking and 2 moves per picking, the 3 has the same Partner to
        Invoice but one has Partner to Shipping so shouldn't be grouping.
        """

        sale_order_1 = self.env.ref(
            "sale_stock_picking_invoicing.main_so_sale_stock_picking_invoicing_1"
        )
        sale_order_1.action_confirm()
        picking = sale_order_1.picking_ids
        picking.action_confirm()
        # Check product availability
        picking.action_assign()
        # Force product availability
        for move in picking.move_ids_without_package:
            move.quantity_done = move.product_uom_qty
        picking.button_validate()

        sale_order_3 = self.env.ref(
            "sale_stock_picking_invoicing.main_so_sale_stock_picking_invoicing_3"
        )
        sale_order_3.action_confirm()
        picking3 = sale_order_3.picking_ids
        # Check product availability
        picking3.action_assign()
        # Force product availability
        for move in picking3.move_ids_without_package:
            move.quantity_done = move.product_uom_qty
        picking3.button_validate()
        self.assertEqual(picking.state, "done")
        self.assertEqual(picking3.state, "done")

        sale_order_4 = self.env.ref(
            "sale_stock_picking_invoicing.main_so_sale_stock_picking_invoicing_4"
        )
        sale_order_4.action_confirm()
        picking4 = sale_order_4.picking_ids
        # Check product availability
        picking4.action_assign()
        # Force product availability
        for move in picking4.move_ids_without_package:
            move.quantity_done = move.product_uom_qty
        picking4.button_validate()
        self.assertEqual(picking.state, "done")
        self.assertEqual(picking3.state, "done")

        pickings = picking | picking3 | picking4
        wizard_obj = self.invoice_wizard.with_context(
            active_ids=pickings.ids,
            active_model=pickings._name,
        )
        fields_list = wizard_obj.fields_get().keys()
        wizard_values = wizard_obj.default_get(fields_list)
        # One invoice per partner but group products
        wizard_values.update(
            {
                "group": "partner_product",
            }
        )
        wizard = wizard_obj.create(wizard_values)
        wizard.onchange_group()
        wizard.action_generate()
        domain = [("picking_ids", "in", (picking.id, picking3.id, picking4.id))]
        invoices = self.account_move_model.search(domain)
        # Even with same Partner Invoice if the Partner Shipping
        # are different should not be Groupping
        self.assertEqual(len(invoices), 2)
        self.assertEqual(picking.invoice_state, "invoiced")
        self.assertEqual(picking3.invoice_state, "invoiced")
        self.assertEqual(picking4.invoice_state, "invoiced")

        # Invoice that has different Partner Shipping
        # should be not groupping
        invoice_pick_1 = invoices.filtered(
            lambda t: t.partner_shipping_id == picking.partner_id
        )
        # Invoice should be create with partner_invoice_id
        self.assertEqual(invoice_pick_1.partner_id, sale_order_1.partner_invoice_id)
        # Invoice create with Partner Shipping used in Picking
        self.assertEqual(invoice_pick_1.partner_shipping_id, picking.partner_id)

        # Groupping Invoice
        invoice_pick_3_4 = invoices.filtered(
            lambda t: t.partner_id == t.partner_shipping_id
        )
        self.assertIn(invoice_pick_3_4, picking3.invoice_ids)
        self.assertIn(invoice_pick_3_4, picking4.invoice_ids)
