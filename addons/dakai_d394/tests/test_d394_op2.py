from odoo.tests.common import TransactionCase, tagged
from odoo import fields
from unittest.mock import patch

@tagged('post_install', '-at_install')
class TestDeclaratiaD394Op2(TransactionCase):

    def setUp(self):
        super().setUp()
        self.country = self.env['res.country'].search([], limit=1)
        if not self.country:
            self.country = self.env['res.country'].create({'name': 'Test Country', 'code': 'TC'})

        self.company = self.env['res.company'].create({
            'name': 'Test Company',
            'country_id': self.country.id,
        })
        self.revenue_account = self.env['account.account'].search([('name', '=', 'Other Income')], limit=1)
        self.revenue_account.write({'company_ids': [(6, 0, [self.company.id])]})
        if not self.revenue_account:
            self.revenue_account = self.env['account.account'].create({
                'name': 'Other Income',
                'code': 'OTHINC',
                'company_ids': [(6, 0, [self.company.id])],
                'active': True,
                'account_type': 'income',
            })

        self.receivable_account = self.env['account.account'].create({
            'name': 'Receivable',
            'code': 'CUSTREC',
            'company_ids': [(6, 0, [self.company.id])],
            'account_type': 'asset_receivable',
        })
        self.payable_account = self.env['account.account'].create({
            'name': 'Payable',
            'code': 'CUSTPAY',
            'company_ids': [(6, 0, [self.company.id])],
            'account_type': 'liability_payable',
        })

        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner',
            'property_account_receivable_id': self.receivable_account.id,
            'property_account_payable_id': self.payable_account.id,
        })
        self.partner2 = self.env['res.partner'].create({
            'name': 'Test Partner2',
            'property_account_receivable_id': self.receivable_account.id,
            'property_account_payable_id': self.payable_account.id,
        })
        representant = self.env['l10_romania.report.reprezentant'].search([], limit=1)
        tax_group = self.env['account.tax.group'].search([
            ('country_id', '=', self.country.id),
            ('company_id', '=', self.company.id)
        ], limit=1)
        if not tax_group:
            tax_group = self.env['account.tax.group'].create({'name': 'Test Group', 'sequence': 1, 'company_id': self.company.id, 'country_id': self.country.id})
        if not representant:
            representant = self.env['l10_romania.report.reprezentant'].create({'name': 'Test Reprezentant'})
        self.journal = self.env['account.journal'].create({
            'name': 'POS Journal',
            'type': 'sale',
            'code': 'POS',
            'l10n_ro_fiscal_receipt': True,
            'company_id': self.company.id,
        })
        self.tax_19 = self.env['account.tax'].create({
            'name': 'TVA 19%',
            'amount': 19,
            'type_tax_use': 'sale',
            'company_id': self.company.id,
            'country_id': self.country.id,
            'tax_group_id': tax_group.id,
        })
        self.tax_5 = self.env['account.tax'].create({
            'name': 'TVA 5%',
            'amount': 5,
            'type_tax_use': 'sale',
            'company_id': self.company.id,
            'country_id': self.country.id,
            'tax_group_id': tax_group.id,
        })
        self.d394 = self.env['l10_romania.report.d394'].create({
            'company_id': self.company.id,
            'name': 'Test D394',
            "reprezentant_id": representant.id,
        })

    def _test_create_invoice(self, date, tax=None, move_type='out_receipt', state='posted', pos_order_ids=None, partner=None):
        invoice = self.env['account.move'].create({
            'move_type': move_type,
            'partner_id': partner.id,
            'company_id': self.company.id,
            'journal_id': self.journal.id,
            'invoice_date': date,
            'invoice_line_ids': [(0, 0, {
                'name': 'Line',
                'quantity': 1,
                'price_unit': 100,
                'tax_ids': [(6, 0, [tax.id])] if tax else [],
                'account_id': self.revenue_account.id,
                'company_id': self.company.id,
            })],
        })
        if state == 'posted':
            invoice.action_post()
        if pos_order_ids:
            invoice.pos_order_ids = [(6, 0, pos_order_ids)]
        return invoice

    def test_compute_name(self):
        op2 = self.env['report.d394.op2'].create({
            'tip_op2': 'i1',
            'luna': 5,
        })
        op2._compute_name()
        self.assertEqual(op2.name, 'OP2_i1 - 5')

    def test_compute_nr(self):
        invoice1 = self._test_create_invoice('2024-05-01', tax=self.tax_19, partner=self.partner)
        invoice2 = self._test_create_invoice('2024-05-02', tax=self.tax_5, partner=self.partner2)
        op2 = self.env['report.d394.op2'].create({
            'invoice_ids': [(6, 0, [invoice1.id, invoice2.id])],
        })
        op2._compute_nr()
        self.assertEqual(op2.nrAMEF, 1)
        self.assertEqual(op2.nrBF, 2)

    def test_generate_creates_op2(self):
        invoice = self._test_create_invoice('2024-04-15', tax=self.tax_19, partner=self.partner)
        invoice.write({'payment_state': 'paid'})
        invoice.company_id.l10n_ro_caen_code = "5630"
        invoice.l10n_ro_partner_type = "1"
        invoice.l10n_ro_operation_type = "C"
        invoice.l10n_ro_invoice_origin_d394 = "1"
        invoice.commercial_partner_id = self.partner
        self.d394.invoice_ids = [(6, 0, [invoice.id])]
        self.env['report.d394.op2'].generate(self.d394)
        op2s = self.env['report.d394.op2'].search([('d394_id', '=', self.d394.id)])
        op2s_count = self.env['report.d394.op2'].search_count([('d394_id', '=', self.d394.id)])
        self.assertEqual(op2s_count, 1)
        self.assertEqual(op2s[0].luna, 4)
        self.assertEqual(op2s[0].tip_op2, 'i1')
