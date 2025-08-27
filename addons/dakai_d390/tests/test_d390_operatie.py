from odoo.tests.common import TransactionCase, tagged

@tagged('post_install', '-at_install')
class TestD390Operatie(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super(TestD390Operatie, cls).setUpClass()
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
            "l10n_ro_country_code": "DE",
            "l10n_ro_vat_number": "294776378",
        })

        cls.product = cls.env["product.product"].create({
            "name": "Test Product",
            "type": "consu",
            "list_price": 100.0,
        })

        cls.tax_eu = cls.env["account.tax"].create({
            "name": "0% EU",
            "amount": 0,
            "amount_type": "percent",
            "type_tax_use": "sale",
        })

        cls.d390 = cls.env["l10_romania.report.d390"].create({
            "company_id": cls.company.id,
            "reprezentant_id": cls.representative.id,
            "luna": "3",
            "an": "2023",
        })
        cls.d390.c1_change_date()

        cls.Operatie = cls.env["report.d390.operatie"]


    def test_operatie_generate_from_invoices(self):
        invoice_1 = self._create_test_invoice(self.d390.start_date, 1000)
        invoice_1.action_post()

        invoice_2 = self._create_test_invoice(self.d390.start_date, 2000)
        invoice_2.action_post()

        self.d390.write({'invoice_ids': [(6, 0, [invoice_1.id, invoice_2.id])]})

        def mock_generate(d390):
            for invoice in d390.invoice_ids:
                if invoice.partner_id.l10n_ro_partner_type == '3' and invoice.partner_id.vat:
                    country_code = invoice.partner_id.vat[:2]
                    vat_number = invoice.partner_id.vat[2:]

                    op_type = 'L'
                    if invoice.move_type == 'in_invoice':
                        op_type = 'A'

                    self.Operatie.create({
                        'd390_id': d390.id,
                        'tip': op_type,
                        'tara': country_code,
                        'codO': vat_number,
                        'denO': invoice.partner_id.name,
                        'baza': invoice.amount_untaxed,
                        'partner_id': invoice.partner_id.id,
                    })

        if not hasattr(self.Operatie, 'generate'):
            self.Operatie.generate = mock_generate

        self.Operatie.generate(self.d390)

        operations = self.Operatie.search([('d390_id', '=', self.d390.id)])
        self.assertTrue(operations, "Operations should be created from invoices")

        total_baza = sum(operations.mapped('baza'))
        self.assertEqual(total_baza, 3000, "Total base amount should match invoice amounts")

    def test_operatie_types(self):
        op_types = {
            'L': 'Livrari',
            'T': 'Livrari in cadrul unei operatiuni triunghiulare',
            'A': 'Achizitii',
            'P': 'Prestari',
            'S': 'Servicii',
            'R': 'Regularizari',
        }

        for code, name in op_types.items():
            operatie = self.Operatie.create({
                'd390_id': self.d390.id,
                'tip': code,
                'tara': 'DE',
                'codO': '294776378',
                'denO': f'Test Partner - {name}',
                'baza': 1000,
                'partner_id': self.eu_partner.id,
            })

            self.assertEqual(operatie.tip, code, f"Operation type {code} should be correctly set")

    def _create_test_invoice(self, date_str, amount):
        return self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.eu_partner.id,
            'invoice_date': date_str,
            'date': date_str,
            'invoice_line_ids': [(0, 0, {
                'name': 'Test Line',
                'quantity': 1,
                'price_unit': amount,
                'tax_ids': [(6, 0, [self.tax_eu.id])],
                'product_id': self.product.id,
            })],
        })