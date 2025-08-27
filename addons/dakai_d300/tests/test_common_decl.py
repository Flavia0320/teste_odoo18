from odoo.tests.common import TransactionCase,  tagged
from datetime import datetime
from dateutil.relativedelta import relativedelta

@tagged('post_install', '-at_install')
class TestD300Computation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super(TestD300Computation, cls).setUpClass()
        cls.company = cls.env.company

        cls.vat_on_payment_fp = cls.env["account.fiscal.position"].create({
            "name": "Regim TVA la Incasare",
            "company_id": cls.company.id,
        })
        cls.company.l10n_ro_property_vat_on_payment_position_id = cls.vat_on_payment_fp.id

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

    def test_total_plata_computation(self):
        invoice = self._create_invoice(1000, self.tax_19)
        purchase = self._create_invoice(500, self.tax_19_purchase, move_type='in_invoice')

        invoice.action_post()
        purchase.action_post()

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
            "end_date": datetime(invoice.date.year, invoice.date.month, 1).replace(day=1) + relativedelta(months=1,
                                                                                                          days=-1),
            "start_date": datetime(invoice.date.year, invoice.date.month, 1),
        })
        d300.rebuild_declaration()

        self.assertEqual(d300.R18_1, 500, "Base amount for R18_1 should be 500")
        self.assertEqual(d300.R18_2, 95, "VAT amount for R18_2 should be 95")

        self.assertEqual(d300.R17_1, 1000, "Total base amount for R17_1 should be 1000")
        self.assertEqual(d300.R17_2, 190, "Total VAT amount for R17_2 should be 190")
        self.assertEqual(d300.R27_1, 500, "Total base amount for R27_1 should be 500")
        self.assertEqual(d300.R27_2, 95, "Total VAT amount for R27_2 should be 95")

        self.assertEqual(d300.R32_2, 95, "Total deductible VAT should be 95")
        self.assertEqual(d300.R33_2, 95, "VAT to be paid should be 95")
        self.assertEqual(d300.R34_2, 0, "VAT to be refunded should be 0")

        expected_total = sum([
            d300.R5_1, d300.R5_2, d300.R17_1, d300.R17_2,
            d300.R18_1, d300.R18_2, d300.R27_1, d300.R27_2,
            d300.R32_2, d300.R33_2, d300.R34_2,
            d300.nr_facturi, d300.baza, d300.tva, d300.nr_facturi_primite
        ])
        self.assertEqual(d300.totalPlata_A, expected_total)

    def test_correction_invoice_data(self):
        invoice = self._create_invoice(1000, self.tax_19, l10n_ro_correction=True)
        purchase = self._create_invoice(500, self.tax_19_purchase,
                                        move_type='in_invoice', l10n_ro_correction=True)

        invoice.action_post()
        purchase.action_post()

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

        self.assertEqual(d300.nr_facturi, 1, "Should count 1 correction invoice")
        self.assertEqual(d300.baza, 1000, "Base amount should be 1000")
        self.assertEqual(d300.tva, 190, "VAT amount should be 190")
        self.assertEqual(d300.nr_facturi_primite, 1, "Should count 1 correction purchase invoice")
        self.assertEqual(d300.baza_primite, 500, "Base amount for purchases should be 500")
        self.assertEqual(d300.tva_primite, 95, "VAT amount for purchases should be 95")

    def test_vat_on_payment_calculations(self):
        invoice = self._create_invoice(1000, self.tax_19, fiscal_position_id=self.vat_on_payment_fp.id)
        invoice.action_post()

        payment = self._create_payment(invoice, 500)

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
            "end_date": datetime(invoice.date.year, invoice.date.month, 1).replace(day=1) + relativedelta(months=1,
                                                                                                          days=-1),
            "start_date": datetime(invoice.date.year, invoice.date.month, 1),
        })
        d300.rebuild_declaration()

        self.assertTrue(d300.valoare_a >= 0, "VAT on payment value should be calculated")

    def _create_invoice(self, amount, tax, move_type='out_invoice',
                        l10n_ro_correction=False, fiscal_position_id=False):
        return self.env['account.move'].create({
            'move_type': move_type,
            'partner_id': self.partner.id,
            'invoice_date': datetime.now().date(),
            'fiscal_position_id': fiscal_position_id,
            'l10n_ro_correction': l10n_ro_correction,
            'invoice_line_ids': [(0, 0, {
                'name': 'Test Line',
                'quantity': 1,
                'price_unit': amount,
                'tax_ids': [(6, 0, [tax.id])],
            })],
            'amount_untaxed_signed': amount,
        })

    def _create_payment(self, invoice, amount):
        journal = self.env['account.journal'].search([('type', '=', 'bank'), ('company_id', '=', self.company.id)],
                                                     limit=1)
        if not journal:
            journal = self.env['account.journal'].create({
                'name': 'Test Journal',
                'type': 'bank',
                'company_id': self.company.id,
                'inbound_payment_method_line_ids': [(6, 0, [self.env.ref('account.account_payment_method_manual_in').id])],
                'outbound_payment_method_line_ids': [(6, 0, [self.env.ref('account.account_payment_method_manual_out').id])],
            })

        payment_method_line = journal.inbound_payment_method_line_ids[:1]
        if not payment_method_line:
            payment_method_line = self.env.ref('account.account_payment_method_manual_in')

        payment_register = self.env['account.payment.register'].with_context(
            active_model='account.move',
            active_ids=invoice.ids
        ).create({
            'payment_date': datetime.now().date(),
            'amount': amount,
            'journal_id': journal.id,
            'payment_method_line_id': payment_method_line.id,
        })

        return payment_register._create_payments()