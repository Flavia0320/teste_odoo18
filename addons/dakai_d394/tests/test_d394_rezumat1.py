from odoo.tests.common import TransactionCase, tagged
from odoo import fields

@tagged('post_install', '-at_install')
class TestDeclaratiaD394Rezumat1(TransactionCase):

    def setUp(self):
        super().setUp()
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
            'code': 'SALES',
            'l10n_ro_sequence_type': 'normal',
            'refund_sequence': True,
            'company_id': self.company.id,
        })
        self.product_prod = self.env['product.product'].create({
            'name': 'Product Prod',
            'l10n_ro_anaf_code': 5678,
            'detailed_type': 'product',
        })
        representant = self.env['l10_romania.report.reprezentant'].search([], limit=1)
        if not representant:
            representant = self.env['l10_romania.report.reprezentant'].create({'name': 'Test Reprezentant'})
        self.d394 = self.env['l10_romania.report.d394'].create({
            'company_id': self.company.id,
            'name': 'Test D394',
            "reprezentant_id": representant.id,
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
        self.op1 = self.env['report.d394.op1'].create({
            'd394_id': self.d394.id,
            'l10n_ro_partner_type': '1',
            'l10n_ro_invoice_origin_d394': '1',
            'cota': 19,
            'l10n_ro_operation_type': 'L',
            'nrFact': 2,
            'baza': 100,
            'tva': 19,
        })

    def _test_create_invoice(self, move_type='out_invoice', price=100):
        invoice = self.env['account.move'].create({
            'move_type': move_type,
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'journal_id': self.journal.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [(0, 0, {
                'name': 'Line',
                'product_id': self.product.id,
                'quantity': 1,
                'price_unit': price,
                'tax_ids': [(6, 0, [self.tax.id])],
                'account_id': self.revenue_account.id,
                'company_id': self.company.id,
            })],
        })
        return invoice

    def test_compute_name(self):
        rez = self.env['report.d394.rezumat1'].create({
            'l10n_ro_partner_type': '1',
            'l10n_ro_invoice_origin_d394': '1',
            'cota': 19,
        })
        rez._compute_name()
        self.assertIn('Rezumat1_1 - 1 - 19%', rez.name)

    def test_computeL_fields(self):
        inv1 = self._test_create_invoice('out_invoice')
        inv2 = self._test_create_invoice('out_invoice')

        inv1.action_post()
        inv2.action_post()
        inv1.write({'payment_state': 'paid'})
        inv2.write({'payment_state': 'paid'})

        inv1.company_id.l10n_ro_caen_code = "1071"
        inv2.company_id.l10n_ro_caen_code = "1071"

        self.d394.invoice_ids = [(6, 0, [inv1.id, inv2.id])]
        self.env['report.d394.lista'].generate(self.d394)

        rez = self.env['report.d394.rezumat1'].create({})
        rez.op1_ids = [(6, 0, self.env['report.d394.lista'].search([('d394_id', '=', self.d394.id)]).ids)]

        self.assertEqual(rez.facturiL, 2)
        self.assertEqual(rez.bazaL, 200)
        self.assertEqual(rez.tvaL, 38)

def test_generate_creates_rezumat1_and_details(self):
        invoice = self._test_create_invoice()
        invoice.invoice_line_ids.write({'product_id': self.product.id})
        invoice.action_post()
        self.op1.write({'invoice_ids': [(4, invoice.id)]})
        self.product.write({'l10n_ro_anaf_code': 1234})
        self.d394.write({'op1_ids': [(4, self.op1.id)]})
        self.env['report.d394.rezumat1'].generate(self.d394)
        rezs = self.env['report.d394.rezumat1'].search([('d394_id', '=', self.d394.id)])
        self.assertEqual(len(rezs), 1)
        rez = rezs[0]
        self.assertEqual(rez.l10n_ro_partner_type, '1')
        self.assertEqual(rez.cota, 19)
        self.assertEqual(rez.l10n_ro_invoice_origin_d394, '1')