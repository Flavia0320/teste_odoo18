from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import ValidationError
from unittest.mock import patch, MagicMock

@tagged('post_install', '-at_install')
class TestDeclaratiaD394(TransactionCase):

    def setUp(self):
        super().setUp()
        self.country = self.env['res.country'].search([], limit=1)
        if not self.country:
            self.country = self.env['res.country'].create({'name': 'Test Country', 'code': 'TC'})
        self.company = self.env['res.company'].create({
            'name': 'Test Company',
            'country_id': self.country.id,
        })
        representant = self.env['l10_romania.report.reprezentant'].search([], limit=1)
        if not representant:
            representant = self.env['l10_romania.report.reprezentant'].create({'name': 'Test Reprezentant'})
        self.template = self.env['report.d394.template'].create({
            'reprezentant_id': representant.id,
            'company_id': self.company.id,
        })
        self.d394 = self.env['l10_romania.report.d394'].create({
            'company_id': self.company.id,
            'template_id': self.template.id,
            'c1_tip_D394': 'L',
            'c1_luna': '1',
            'c1_an': '2024',
            'reprezentant_id': representant.id,
        })

    def test_compute_name(self):
        self.d394._compute_name()
        self.assertEqual(self.d394.name, 'D394_L - 1.2024')

    def test_c1_change_date_monthly(self):
        self.d394.c1_tip_D394 = 'L'
        self.d394.c1_luna = '2'
        self.d394.c1_an = '2023'
        self.d394.c1_change_date()
        self.assertIsNotNone(self.d394.start_date)
        self.assertIsNotNone(self.d394.end_date)

    def test_c1_change_date_yearly(self):
        self.d394.c1_tip_D394 = 'A'
        self.d394.c1_change_date()
        self.assertIsNotNone(self.d394.start_date)
        self.assertIsNotNone(self.d394.end_date)

    def test_get_invoices_empty(self):
        invoices = self.d394.get_invoices()
        self.assertEqual(len(invoices), 0)

    def test_get_paid_invoices_no_fp(self):
        self.company.l10n_ro_property_vat_on_payment_position_id = False
        result = self.d394.get_paid_invoices()
        self.assertEqual(len(result), 0)

    def test_compute_c1_sistemTVA(self):
        self.d394._compute_c1_sistemTVA()
        self.assertIn(self.d394.c1_sistemTVA, dict(self.d394.fields_get()['c1_sistemTVA']['selection']).keys())