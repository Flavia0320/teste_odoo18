from odoo.tests.common import TransactionCase,  tagged
from odoo.exceptions import ValidationError
from unittest.mock import patch
from lxml import etree

@tagged('post_install', '-at_install')
class TestD390Report(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super(TestD390Report, cls).setUpClass()
        cls.company = cls.env.company

        cls.representative = cls.env["l10_romania.report.reprezentant"].create({
            "name": "John Doe",
            "function": "Director",
            "company_id": cls.company.id,
        })

        cls.eu_partner = cls.env["res.partner"].create({
            "name": "EU Partner",
            "country_id": cls.env.ref("base.de").id,
            "vat": "DE294776378",
            "l10n_ro_partner_type": "3",
        })

        cls.product = cls.env["product.product"].create({
            "name": "Test Product",
            "type": "product",
            "list_price": 100.0,
        })

        cls.tax_eu = cls.env["account.tax"].create({
            "name": "0% EU",
            "amount": 0,
            "amount_type": "percent",
            "type_tax_use": "sale",
        })

    def test_d390_name_computation(self):
        d390 = self.env["l10_romania.report.d390"].create({
            "company_id": self.company.id,
            "reprezentant_id": self.representative.id,
            "luna": "3",
            "an": "2023",
        })

        self.assertEqual(d390.name, "D390 - 3.2023",
                         "Name should be correctly computed as D390 - month.year")

    def test_reprezentant_data_computation(self):
        d390 = self.env["l10_romania.report.d390"].create({
            "company_id": self.company.id,
            "reprezentant_id": self.representative.id,
            "luna": "3",
            "an": "2023",
        })

        self.assertEqual(d390.nume_declar, "John", "First name should be correctly extracted")
        self.assertEqual(d390.prenume_declar, "Doe", "Last name should be correctly extracted")
        self.assertEqual(d390.functie_declar, "Director", "Function should be correctly copied")

    def test_company_data_computation(self):
        self.company.vat = "RO123456789"

        d390 = self.env["l10_romania.report.d390"].create({
            "company_id": self.company.id,
            "reprezentant_id": self.representative.id,
            "luna": "3",
            "an": "2023",
        })

        self.assertEqual(d390.cui, "123456789", "VAT should be correctly extracted without country code")
        self.assertEqual(d390.den, self.company.name, "Company name should be correctly copied")
        self.assertTrue(d390.adresa, "Address should be computed")
        self.assertEqual(d390.telefon, self.company.phone, "Phone should be correctly copied")
        self.assertEqual(d390.mail, self.company.email, "Email should be correctly copied")

    def test_date_computation(self):
        d390 = self.env["l10_romania.report.d390"].create({
            "company_id": self.company.id,
            "reprezentant_id": self.representative.id,
            "luna": "3",
            "an": "2023",
        })

        d390.c1_change_date()

        self.assertEqual(d390.start_date.strftime("%Y-%m-%d"), "2023-03-01",
                         "Start date should be first day of month")
        self.assertEqual(d390.end_date.strftime("%Y-%m-%d"), "2023-03-31",
                         "End date should be last day of month")

    def test_rebuild_declaration(self):
        d390 = self.env["l10_romania.report.d390"].create({
            "company_id": self.company.id,
            "reprezentant_id": self.representative.id,
            "luna": "3",
            "an": "2023",
        })
        d390.c1_change_date()

        invoice = self._create_test_invoice(d390.start_date)
        invoice.action_post()
        picking = self._create_test_picking(d390.start_date)

        d390.rebuild_declaration()

        self.assertEqual(invoice.d390_id.id, d390.id, "Invoice should be linked to the declaration")
        self.assertEqual(picking.d390_id.id, d390.id, "Picking should be linked to the declaration")

    def _create_test_invoice(self, date_str):
        return self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.eu_partner.id,
            'invoice_date': date_str,
            'date': date_str,
            'invoice_line_ids': [(0, 0, {
                'name': 'Test Line',
                'quantity': 1,
                'price_unit': 100,
                'tax_ids': [(6, 0, [self.tax_eu.id])],
                'product_id': self.product.id,
            })],
        })

    def _create_test_picking(self, date_str):
        picking = self.env['stock.picking'].create({
            'partner_id': self.eu_partner.id,
            'picking_type_id': self.env.ref('stock.picking_type_out').id,
            'location_id': self.env.ref('stock.stock_location_stock').id,
            'location_dest_id': self.env.ref('stock.stock_location_customers').id,
            'scheduled_date': date_str,
        })

        self.env['stock.move'].create({
            'name': self.product.name,
            'product_id': self.product.id,
            'product_uom_qty': 1,
            'product_uom': self.product.uom_id.id,
            'picking_id': picking.id,
            'location_id': self.env.ref('stock.stock_location_stock').id,
            'location_dest_id': self.env.ref('stock.stock_location_customers').id,
        })

        picking.action_confirm()
        picking.action_assign()

        picking.date_done = date_str

        for ml in picking.move_line_ids:
            ml.qty_done = ml.product_uom_qty
        picking._action_done()

        return picking