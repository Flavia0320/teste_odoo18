from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import ValidationError
from unittest.mock import patch
from lxml import etree
from datetime import datetime
from dateutil.relativedelta import relativedelta

@tagged('post_install', '-at_install')
class TestD300Report(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super(TestD300Report, cls).setUpClass()
        cls.company = cls.env.company
        cls.company.l10n_ro_property_vat_on_payment_position_id = cls.env["account.fiscal.position"].create({
            "name": "Regim TVA la Incasare",
            "company_id": cls.company.id,
        })

        cls.account_4423 = cls.env["account.account"].create({
            "code": "442300",
            "name": "TVA collected",
            "company_id": cls.company.id,
        })
        cls.account_4424 = cls.env["account.account"].create({
            "code": "442400",
            "name": "TVA deductible",
            "company_id": cls.company.id,
        })

        cls.tax_19 = cls.env["account.tax"].create({
            "name": "TVA 19%",
            "amount": 19,
            "amount_type": "percent",
            "type_tax_use": "sale",
            "company_id": cls.company.id,
        })

        cls.tax_tags = {
            "01_base": cls._create_tax_tag("01 - TAX BASE"),
            "05_base": cls._create_tax_tag("05 - TAX BASE"),
            "05_vat": cls._create_tax_tag("05 - VAT"),
            "20_base": cls._create_tax_tag("20 - TAX BASE"),
            "20_vat": cls._create_tax_tag("20 - VAT"),
            "27_1_base": cls._create_tax_tag("27_1 - TAX BASE"),
            "27_1_vat": cls._create_tax_tag("27_1 - VAT"),
            "27_2_base": cls._create_tax_tag("27_2 - TAX BASE"),
            "27_2_vat": cls._create_tax_tag("27_2 - VAT"),
            "27_3_base": cls._create_tax_tag("27_3 - TAX BASE"),
            "27_3_vat": cls._create_tax_tag("27_3 - VAT"),
        }

        cls.tax_19 = cls._create_tax("TVA 19%", 19, "sale", cls.tax_tags["05_base"], cls.tax_tags["05_vat"])
        cls.tax_19_purchase = cls._create_tax("TVA 19% Purchase", 19, "purchase",
                                              cls.tax_tags["20_base"], cls.tax_tags["20_vat"])

        cls._link_tag_to_tax(cls.tax_19, cls.tax_tags['05_base'], cls.tax_tags['05_vat'])

        cls.partner = cls.env["res.partner"].create({
            "name": "Test Partner",
            "country_id": cls.env.ref("base.ro").id,
        })

    @classmethod
    def _create_tax_tag(cls, name):
        return cls.env["account.account.tag"].create({
            "name": name,
            "applicability": "taxes",
            "country_id": cls.env.ref("base.ro").id,
        })

    @classmethod
    def _create_tax(cls, name, amount, type_tax_use, base_tag, tax_tag):
        tax = cls.env["account.tax"].search([
            ("name", "=", name),
            ("type_tax_use", "=", type_tax_use),
            ("company_id", "=", cls.company.id)
        ], limit=1)
        if tax:
            return tax
        tax = cls.env["account.tax"].create({
            "name": name,
            "amount": amount,
            "amount_type": "percent",
            "type_tax_use": type_tax_use,
            "company_id": cls.company.id,
        })
        for line in tax.invoice_repartition_line_ids:
            if line.repartition_type == 'base':
                line.tag_ids = [(4, base_tag.id)]
            elif line.repartition_type == 'tax':
                line.tag_ids = [(4, tax_tag.id)]
        return tax

    @classmethod
    def _link_tag_to_tax(cls, tax, base_tag, tax_tag):
        repartition_lines = tax.invoice_repartition_line_ids
        for line in repartition_lines:
            if line.repartition_type == 'base':
                line.tag_ids = [(4, base_tag.id)]
            elif line.repartition_type == 'tax':
                line.tag_ids = [(4, tax_tag.id)]

    def test_d300_field_computations(self):
        invoice = self._create_test_invoice()
        invoice.action_post()
        self.env['res.partner.bank'].create({
            'acc_number': 'RO49AAAA1B31007593840000',
            'partner_id': self.company.partner_id.id,
            'bank_id': self.env['res.bank'].create({'name': 'Banca Test'}).id,
        })
        representant = self.env['l10_romania.report.reprezentant'].search([], limit=1)
        if not representant:
            representant = self.env['l10_romania.report.reprezentant'].create({'name': 'Test Reprezentant'})
        d300 = self.env["l10_romania.report.d300"].create({
            "an": str(invoice.date.year),
            "luna": str(invoice.date.month),
            "company_id": self.company.id,
            "name": "D300_TEST",
            "tip_D300": "L",
            "pro_rata": 100,
            "bifa_cereale": "N",
            "bifa_mob": "N",
            "bifa_disp": "N",
            "bifa_cons": "N",
            "solicit_ramb": "N",
            "nr_evid": "12345678901234567890123",
            "reprezentant_id": representant.id,
            "end_date": datetime(invoice.date.year, invoice.date.month, 1).replace(day=1) + relativedelta(months=1, days=-1),
            "start_date": datetime(invoice.date.year, invoice.date.month, 1),
        })
        d300.rebuild_declaration()
        self.assertEqual(d300.R5_1, 0)
        self.assertEqual(d300.R5_2, 0)
        self.assertEqual(d300.R17_1, d300.R5_1)
        self.assertEqual(d300.R17_2, d300.R5_2)

    def test_get_balance(self):
        invoice = self._create_test_invoice()
        invoice.action_post()
        self.env['res.partner.bank'].create({
            'acc_number': 'RO49AAAA1B31007593840000',
            'partner_id': self.company.partner_id.id,
            'bank_id': self.env['res.bank'].create({'name': 'Banca Test'}).id,
        })
        representant = self.env['l10_romania.report.reprezentant'].search([], limit=1)
        if not representant:
            representant = self.env['l10_romania.report.reprezentant'].create({'name': 'Test Reprezentant'})
        d300 = self.env["l10_romania.report.d300"].create({
            "an": str(invoice.date.year),
            "luna": str(invoice.date.month),
            "company_id": self.company.id,
            "name": "D300_TEST",
            "tip_D300": "L",
            "pro_rata": 100,
            "bifa_cereale": "N",
            "bifa_mob": "N",
            "bifa_disp": "N",
            "bifa_cons": "N",
            "solicit_ramb": "N",
            "nr_evid": "12345678901234567890123",
            "reprezentant_id": representant.id,
            "end_date": datetime(invoice.date.year, invoice.date.month, 1).replace(day=1) + relativedelta(months=1, days=-1),
            "start_date": datetime(invoice.date.year, invoice.date.month, 1),
        })
        d300.rebuild_declaration()
        balance_05_base = d300.get_balance("05 - TAX BASE")
        balance_05_vat = d300.get_balance("05 - VAT")
        self.assertEqual(balance_05_base, 0)
        self.assertEqual(balance_05_vat, 0)


    def _create_test_invoice(self):
        invoice = self.env["account.move"].create({
            "move_type": "out_invoice",
            "partner_id": self.partner.id,
            "invoice_date": datetime.today(),
            "invoice_line_ids": [(0, 0, {
                "name": "Product Test",
                "quantity": 1,
                "price_unit": 1000,
                "tax_ids": [(6, 0, [self.tax_19.id])],
            })],
        })
        return invoice
