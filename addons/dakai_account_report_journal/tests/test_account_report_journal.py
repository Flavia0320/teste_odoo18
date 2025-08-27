from odoo.tests.common import TransactionCase, tagged
from datetime import date, timedelta

@tagged('post_install', '-at_install')
class TestAccountReportJournal(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref('base.main_company')
        cls.partner = cls.env['res.partner'].create({'name': 'Test Partner', 'vat': '30678383'})
        cls.journal_sale = cls.env['account.journal'].create({
            'name': 'Test Sales Journal',
            'type': 'sale',
            'code': 'TSTSALE',
            'company_id': cls.company.id,
        })
        cls.journal_purchase = cls.env['account.journal'].create({
            'name': 'Test Purchase Journal',
            'type': 'purchase',
            'code': 'TSTPUR',
            'company_id': cls.company.id,
        })

        revenue_account = cls.env['account.account'].search([('name', '=', 'Other Income')], limit=1)
        expense_account = cls.env['account.account'].search([('name', '=', 'Expenses')], limit=1)

        cls.invoice_sale = cls.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': cls.partner.id,
            'journal_id': cls.journal_sale.id,
            'date': date.today(),
            'company_id': cls.company.id,
            'invoice_date': date.today(),
        })

        cls.invoice_sale.write({
            'invoice_line_ids': [(0, 0, {
                'name': 'Test Product',
                'quantity': 1,
                'price_unit': 100.0,
                'account_id': revenue_account.id,
            })]
        })
        cls.invoice_sale.action_post()

        cls.invoice_purchase = cls.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': cls.partner.id,
            'journal_id': cls.journal_purchase.id,
            'date': date.today(),
            'company_id': cls.company.id,
            'invoice_date': date.today(),
        })

        cls.invoice_purchase.write({
            'invoice_line_ids': [(0, 0, {
                'name': 'Test Purchase',
                'quantity': 1,
                'price_unit': 200.0,
                'account_id': expense_account.id,
            })]
        })
        cls.invoice_purchase.action_post()

        cls.invoice_old = cls.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': cls.partner.id,
            'journal_id': cls.journal_sale.id,
            'date': date.today() - timedelta(days=30),
            'company_id': cls.company.id,
            'invoice_date': date.today() - timedelta(days=30),
        })

        cls.invoice_old.write({
            'invoice_line_ids': [(0, 0, {
                'name': 'Old Test Product',
                'quantity': 1,
                'price_unit': 50.0,
                'account_id': revenue_account.id,
            })]
        })
        cls.invoice_old.action_post()

        cls.report = cls.env['account.report.journal'].create({
            'company_id': cls.company.id,
            'type': 'sale',
            'start_date': date.today() - timedelta(days=5),
            'end_date': date.today() + timedelta(days=5),
        })
        cls.report_purchase = cls.env['account.report.journal'].create({
            'company_id': cls.company.id,
            'type': 'purchase',
            'start_date': date.today() - timedelta(days=5),
            'end_date': date.today() + timedelta(days=5),
        })

    def test_get_invoices_sale(self):
        invoices = self.report.get_invoices()
        self.assertIn(self.invoice_sale, invoices)
        self.assertNotIn(self.invoice_old, invoices)

    def test_get_invoices_purchase(self):
        invoices = self.report_purchase.get_invoices()
        self.assertIn(self.invoice_purchase, invoices)
        self.assertNotIn(self.invoice_old, invoices)

    def test_get_paid_invoices_empty(self):
        # No special fiscal position, should be empty
        paid_invoices = self.report.get_paid_invoices()
        self.assertEqual(len(paid_invoices), 0)

    def test_rebuild_creates_lines_and_totals(self):
        self.report.rebuild()
        self.assertTrue(self.report.account_report_journal_line_ids)
        self.assertIn(self.invoice_sale, self.report.invoice_ids)
        total = sum(self.report.account_report_journal_line_ids.mapped('invoice_total'))
        self.assertAlmostEqual(self.report.report_total_invoice_total, total)

    def test_purchase_rebuild_and_totals(self):
        self.report_purchase.rebuild()
        self.assertTrue(self.report_purchase.account_report_journal_line_ids)
        self.assertIn(self.invoice_purchase, self.report_purchase.invoice_ids)
        total = sum(self.report_purchase.account_report_journal_line_ids.mapped('invoice_total'))
        self.assertAlmostEqual(self.report_purchase.report_total_invoice_total, total)

    def test_export_creates_attachment(self):
        self.report.rebuild()
        result = self.report.export()
        self.assertIn('url', result)
        self.assertIn('ir.attachment', result['url'])

    def test_empty_domain(self):
        report = self.env['account.report.journal'].create({
            'company_id': self.company.id,
            'type': 'sale',
            'start_date': date.today() - timedelta(days=100),
            'end_date': date.today() - timedelta(days=90),
        })
        invoices = report.get_invoices()
        self.assertFalse(invoices)
        report.rebuild()
        self.assertFalse(report.account_report_journal_line_ids)