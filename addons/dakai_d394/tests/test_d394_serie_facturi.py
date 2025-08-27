from odoo.tests.common import TransactionCase, tagged
from odoo import fields
from datetime import date, timedelta
import types

@tagged('post_install', '-at_install')
class TestDeclaratiaD394SerieFacturi(TransactionCase):

    def setUp(self):
        super().setUp()
        representant = self.env['l10_romania.report.reprezentant'].search([], limit=1)
        if not representant:
            representant = self.env['l10_romania.report.reprezentant'].create({'name': 'Test Reprezentant'})
        self.country = self.env['res.country'].search([], limit=1)
        if not self.country:
            self.country = self.env['res.country'].create({'name': 'Test Country', 'code': 'TC'})
        self.company = self.env['res.company'].create({
            'name': 'Test Company',
            'country_id': self.country.id,
        })
        self.journal = self.env['account.journal'].create({
            'name': 'Sales Journal',
            'type': 'sale',
            'code': 'SFA',
            'l10n_ro_sequence_type': 'normal',
            'refund_sequence': True,
            'company_id': self.company.id,
        })
        self.revenue_account = self.env['account.account'].search([('name', '=', 'Other Income')], limit=1)
        self.revenue_account.write({'company_id': self.company.id})
        if not self.revenue_account:
            self.revenue_account = self.env['account.account'].create({
                'name': 'Other Income',
                'code': 'OTHINC',
                'company_id': self.company.id,
                'active': True,
                'account_type': 'income',
            })

        self.receivable_account = self.env['account.account'].create({
            'name': 'Receivable',
            'code': 'CUSTREC',
            'company_id': self.company.id,
            'account_type': 'asset_receivable',
        })
        self.payable_account = self.env['account.account'].create({
            'name': 'Payable',
            'code': 'CUSTPAY',
            'company_id': self.company.id,
            'account_type': 'liability_payable',
        })

        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner',
            'property_account_receivable_id': self.receivable_account.id,
            'property_account_payable_id': self.payable_account.id,
        })
        self.d394 = self.env['l10_romania.report.d394'].create({
            'company_id': self.company.id,
            'name': 'Test D394',
            "reprezentant_id": representant.id,
        })
        self.tax_group = self.env['account.tax.group'].search([('company_id', '=', self.company.id)], limit=1)
        if not self.tax_group:
            self.tax_group = self.env['account.tax.group'].create({
                'name': 'Test Group',
                'company_id': self.company.id,
            })
        self.tax = self.env['account.tax'].create({
            'name': 'Tax 19%',
            'amount_type': 'percent',
            'amount': 19,
            'type_tax_use': 'sale',
            'company_id': self.company.id,
            'tax_group_id': self.tax_group.id,
        })

    def _test_create_invoice(self, move_type='out_invoice', seq_prefix='SFA/2025/', seq_number=1):
        invoice = self.env['account.move'].create({
            'move_type': move_type,
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'journal_id': self.journal.id,
            'invoice_date': date.today(),
            'sequence_prefix': seq_prefix,
            'sequence_number': seq_number,
            'invoice_line_ids': [(0, 0, {
                'name': 'Test Line',
                'quantity': 1,
                'price_unit': 100,
                'tax_ids': [(6, 0, [self.tax.id])],
                'account_id': self.revenue_account.id,
                'company_id': self.company.id,
            })],
        })

        invoice.action_post()
        return invoice

    def test_compute_name(self):
        serie = self.env['report.d394.serie_facturi'].create({
            'serieI': 'ABC',
        })
        serie._compute_name()
        self.assertEqual(serie.name, 'SerieFacturi - ABC%')

    def test_get_journal_type(self):
        serie = self.env['report.d394.serie_facturi'].create({
            'journal_id': self.journal.id,
        })
        serie._get_journal_type()
        self.assertEqual(serie.l10n_ro_sequence_type, 2)

    def test_get_serie_nr(self):
        inv1 = self._test_create_invoice(seq_prefix='SFA/2025/', seq_number=10)
        inv2 = self._test_create_invoice(seq_prefix='SFA/2025', seq_number=2)
        serie = self.env['report.d394.serie_facturi'].create({
            'invoice_ids': [(6, 0, [inv1.id, inv2.id])],
        })
        serie._get_serie_nr()
        print(f"Serie: {serie.serieI}, NrI: {serie.nrI}, NrF: {serie.nrF}")
        self.assertEqual(serie.serieI, 'SFA/2025/')
        self.assertEqual(serie.nrI, '1')
        self.assertEqual(serie.nrF, '2')

    def test_generate_creates_records(self):
        inv1 = self._test_create_invoice(move_type='out_invoice', seq_number=1)
        inv2 = self._test_create_invoice(move_type='out_refund', seq_number=2)
        self.d394.invoice_ids = inv1 + inv2
        self.env['report.d394.serie_facturi'].generate(self.d394)
        series = self.env['report.d394.serie_facturi'].search([('d394_id', '=', self.d394.id)])
        self.assertTrue(series)
        self.assertGreaterEqual(len(series), 4)
        refund_series = series.filtered(lambda s: any(i.move_type == 'out_refund' for i in s.invoice_ids))
        self.assertTrue(refund_series)