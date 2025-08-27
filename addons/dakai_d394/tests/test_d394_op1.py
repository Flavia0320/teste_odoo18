from odoo.tests.common import TransactionCase, tagged
from odoo import fields

@tagged('post_install', '-at_install')
class TestDeclaratiaD394Op1(TransactionCase):

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

        self.product = self.env['product.product'].create({
            'name': 'Produs',
            'l10n_ro_anaf_code': 1234,
        })

        tax_group = self.env['account.tax.group'].search([
            ('country_id', '=', self.country.id),
            ('company_id', '=', self.company.id)
        ], limit=1)
        if not tax_group:
            tax_group = self.env['account.tax.group'].create({'name': 'Test Group', 'sequence': 1, 'company_id': self.company.id, 'country_id': self.country.id})
        self.tax = self.env['account.tax'].create({
            'name': 'TVA 19%',
            'amount': 19,
            'type_tax_use': 'sale',
            'company_id': self.company.id,
            'tax_group_id': tax_group.id,
            'country_id': self.country.id,
        })
        representant = self.env['l10_romania.report.reprezentant'].search([], limit=1)
        if not representant:
            representant = self.env['l10_romania.report.reprezentant'].create({'name': 'Test Reprezentant'})
        self.d394 = self.env['l10_romania.report.d394'].create({
            'company_id': self.company.id,
            'name': 'Test D394',
            "reprezentant_id": representant.id,
        })
        self.journal = self.env['account.journal'].create({
            'name': 'Sales Journal',
            'type': 'sale',
            'code': 'SALES',
            'l10n_ro_sequence_type': 'normal',
            'refund_sequence': True,
            'company_id': self.company.id,
        })

    def _test_create_invoice(self, amount=100):
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'journal_id': self.journal.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [(0, 0, {
                'name': 'Line',
                'product_id': self.product.id,
                'quantity': 1,
                'price_unit': amount,
                'tax_ids': [(6, 0, [self.tax.id])],
                'account_id': self.revenue_account.id,
                'company_id': self.company.id,
            })],
        })
        return invoice

    def test_compute_name(self):
        partner = self.env['res.partner'].create({
            'name': 'TestDenP',
            'vat': 'RO1234567897',
            'country_id': self.env.ref('base.ro').id,
        })
        op1 = self.env['report.d394.op1'].create({
            'partner_id': partner.id,
            'l10n_ro_operation_type': 'A',
            'l10n_ro_invoice_origin_d394': '1',
            'cota': 19,
        })
        op1._compute_name()
        self.assertEqual(
            op1.name,
            "OP1_TestDenP - A - 1 - 19%"
        )

    def test_generate_creates_op1(self):
        invoice = self._test_create_invoice()
        invoice.action_post()
        invoice.write({'payment_state': 'paid'})
        invoice.company_id.l10n_ro_caen_code = "5630"
        invoice.l10n_ro_partner_type = "1"
        invoice.l10n_ro_operation_type = "C"
        invoice.l10n_ro_invoice_origin_d394 = "1"
        invoice.commercial_partner_id = self.partner
        self.d394.invoice_ids = [(6, 0, [invoice.id])]
        self.env['report.d394.op1'].generate(self.d394)
        op1s_count = self.env['report.d394.op1'].search_count([('d394_id', '=', self.d394.id)])
        op1s = self.env['report.d394.op1'].search([('d394_id', '=', self.d394.id)])
        self.assertEqual(op1s_count, 1)
        self.assertEqual(op1s.partner_id, self.partner)

