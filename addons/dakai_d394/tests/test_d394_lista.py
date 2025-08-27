from odoo.tests.common import TransactionCase, tagged
from odoo import fields

@tagged('post_install', '-at_install')
class TestDeclaratiaD394Lista(TransactionCase):

    def setUp(self):
        super().setUp()
        self.country = self.env['res.country'].search([], limit=1)
        if not self.country:
            self.country = self.env['res.country'].create({'name': 'Test Country', 'code': 'TC'})
        self.company = self.env['res.company'].create({
            'name': 'Test Company',
            'l10n_ro_caen_code': '1071',
            'country_id': self.env['res.country'].search([], limit=1).id,
        })
        representant = self.env['l10_romania.report.reprezentant'].search([], limit=1)
        if not representant:
            representant = self.env['l10_romania.report.reprezentant'].create({'name': 'Test Reprezentant'})
        self.currency = self.company.currency_id
        self.journal = self.env['account.journal'].create({
            'name': 'Sales Journal',
            'type': 'sale',
            'code': 'SALES',
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
        self.product_bun = self.env['product.product'].create({
            'name': 'Produs',
            'type': 'product',
        })
        self.product_serv = self.env['product.product'].create({
            'name': 'Serviciu',
            'type': 'service',
        })
        self.tax_group = self.env['account.tax.group'].create({
            'name': 'VAT',
            'sequence': 1,
            'company_id': self.company.id,
            'country_id': self.country.id,
        })
        self.tax = self.env['account.tax'].create({
            'name': 'TVA 19%',
            'amount': 19,
            'type_tax_use': 'sale',
            'company_id': self.company.id,
            'tax_group_id': self.tax_group.id,
            'country_id': self.country.id,
        })
        self.d394 = self.env['l10_romania.report.d394'].create({
            'company_id': self.company.id,
            'name': 'Test D394',
            "reprezentant_id": representant.id,
        })

    def _test_create_invoice(self, product, payment_state='paid'):
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'journal_id': self.journal.id,
            'payment_state': payment_state,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [(0, 0, {
                'name': 'Line',
                'product_id': product.id,
                'quantity': 1,
                'price_unit': 100,
                'tax_ids': [(6, 0, [self.tax.id])],
                'account_id':self.revenue_account.id,
                'company_id': self.company.id,
            })],
        })
        return invoice

    def test_compute_name(self):
        lista = self.env['report.d394.lista'].create({
            'caen': 1071,
            'cota': 19,
            'operat': '1',
        })
        lista._compute_name()
        self.assertEqual(lista.name, 'Lista_1071 - 1- 19%')

    def test_compute_value(self):
        invoice = self._test_create_invoice(self.product_bun)
        line = invoice.invoice_line_ids[0]
        lista = self.env['report.d394.lista'].create({
            'invoice_line_ids': [(6, 0, [line.id])],
        })
        lista._compute_value()
        self.assertEqual(lista.valoare, 100)
        #invoice._recompute_dynamic_lines()
        lista._compute_value()
        self.assertTrue(lista.tva >= 0)

    def test_generate_creates_lista_bunuri(self):
        invoice = self._test_create_invoice(self.product_bun)
        invoice.action_post()
        invoice.write({'payment_state': 'paid'})
        self.d394.invoice_ids = [(6, 0, [invoice.id])]
        self.env['report.d394.lista'].generate(self.d394)
        lista = self.env['report.d394.lista'].search([('d394_id', '=', self.d394.id)])
        lista_count = self.env['report.d394.lista'].search_count([('d394_id', '=', self.d394.id)])
        self.assertEqual(lista_count, 1)
        self.assertEqual(lista.operat, '1')
        self.assertEqual(lista.caen, '1071')

    def test_generate_creates_lista_servicii(self):
        invoice = self._test_create_invoice(self.product_serv)
        invoice.action_post()
        invoice.write({'payment_state': 'paid'})
        invoice.company_id.l10n_ro_caen_code = "5630"
        self.d394.invoice_ids = [(6, 0, [invoice.id])]
        self.env['report.d394.lista'].generate(self.d394)
        lista = self.env['report.d394.lista'].search([('d394_id', '=', self.d394.id)])
        lista_count = self.env['report.d394.lista'].search_count([('d394_id', '=', self.d394.id)])
        self.assertEqual(lista_count, 1)
        self.assertEqual(lista.operat, "2")

    def test_generate_unlinks_existing(self):
        invoice = self._test_create_invoice(self.product_bun)
        invoice.action_post()
        self.d394.invoice_ids = [(6, 0, [invoice.id])]
        lista = self.env['report.d394.lista'].create({
            'd394_id': self.d394.id,
            'caen': 1071,
            'cota': 19,
            'operat': '1',
        })
        initial_count = self.env['report.d394.lista'].search_count([('d394_id', '=', self.d394.id)])
        self.assertEqual(initial_count, 1)