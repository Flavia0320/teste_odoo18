from odoo.tests.common import TransactionCase, tagged
from unittest.mock import patch

@tagged('post_install', '-at_install')
class TestDeclaratiaD394Facturi(TransactionCase):

    def setUp(self):
        super().setUp()
        self.country = self.env['res.country'].search([], limit=1)
        if not self.country:
            self.country = self.env['res.country'].create({'name': 'Test Country', 'code': 'TC'})
        self.company = self.env['res.company'].create({
            'name': 'Test Company',
            'country_id': self.country.id,
        })
        self.product = self.env['product.product'].create({
            'name': 'Produs',
            'l10n_ro_anaf_code': 1234,
        })
        representant = self.env['l10_romania.report.reprezentant'].search([], limit=1)
        if not representant:
            representant = self.env['l10_romania.report.reprezentant'].create({'name': 'Test Reprezentant'})
        self.journal_autoinv1 = self.env['account.journal'].create({
            'name': 'AutoInv1',
            'type': 'sale',
            'code': 'AI1',
            'l10n_ro_sequence_type': 'autoinv1',
            'company_id': self.company.id,
        })
        self.journal_autoinv2 = self.env['account.journal'].create({
            'name': 'AutoInv2',
            'type': 'sale',
            'code': 'AI2',
            'l10n_ro_sequence_type': 'autoinv2',
            'company_id': self.company.id,
        })
        self.journal_normal = self.env['account.journal'].create({
            'name': 'Normal',
            'type': 'sale',
            'code': 'NOR',
            'company_id': self.company.id,
        })
        self.tax_group = self.env['account.tax.group'].create({
            'name': 'VAT',
            'sequence': 1,
            'company_id': self.company.id,
            'country_id': self.country.id,
        })
        self.tax_19 = self.env['account.tax'].create({
            'name': 'TVA 19%',
            'amount': 19,
            'type_tax_use': 'sale',
            'company_id': self.company.id,
            'tax_group_id': self.tax_group.id,
            'country_id': self.country.id,
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

    def _test_create_invoice(self, move_type, state='posted', journal=None, tax=None):
        invoice = self.env['account.move'].create({
            'move_type': move_type,
            'partner_id': self.partner.id,
            'journal_id': journal.id if journal else self.journal_normal.id,
            'invoice_line_ids': [(0, 0, {
                'name': 'Line',
                'product_id': self.product.id,
                'quantity': 1,
                'price_unit': 100,
                'tax_ids': [(6, 0, [tax.id])] if tax else [],
                'account_id': self.revenue_account.id,
                'company_id': self.company.id,
            })],
        })
        if state == 'posted':
            invoice.action_post()
        elif state == 'cancel':
            invoice.action_post()
            invoice.button_cancel()
        return invoice

    def test_compute_name(self):
        invoice_test = self._test_create_invoice('out_invoice', journal=self.journal_normal, tax=self.tax_19)
        fact = self.env['report.d394.facturi'].create({
            'tip_factura': '1',
            'serie': 'A',
            'nr': 123,
            'invoice_id': invoice_test.id,
        })
        invoice_test.sequence_prefix = 'A'
        invoice_test.sequence_number = 123
        fact._compute_name()
        self.assertEqual(fact.name, 'Facturi_1 - A123')

    def test_get_values_autofactura(self):
        invoice = self._test_create_invoice(
            'out_invoice',
            journal=self.journal_autoinv1,
            tax=self.tax_19
        )

        fact = self.env['report.d394.facturi'].create({
            'tip_factura': '3',
            'invoice_id': invoice.id,
        })

        fact._get_values()

        self.assertEqual(fact.baza19, 100)
        self.assertEqual(fact.tva19, 19)
        self.assertEqual(fact.baza5, 0)
        self.assertEqual(fact.tva5, 0)
        self.assertEqual(fact.baza9, 0)
        self.assertEqual(fact.tva9, 0)
        self.assertEqual(fact.baza20, 0)
        self.assertEqual(fact.tva20, 0)
        self.assertEqual(fact.baza24, 0)
        self.assertEqual(fact.tva24, 0)

    def test_generate_creates_facturi(self):
        inv_cancel = self._test_create_invoice('out_invoice', state='cancel', journal=self.journal_autoinv1)
        inv_refund = self._test_create_invoice('out_refund')
        inv_autoinv1 = self._test_create_invoice('out_invoice', journal=self.journal_autoinv1)
        inv_autoinv2 = self._test_create_invoice('out_invoice', journal=self.journal_autoinv2)
        self.d394.invoice_ids = [(6, 0, [inv_cancel.id, inv_refund.id, inv_autoinv1.id, inv_autoinv2.id])]
        self.env['report.d394.facturi'].generate(self.d394)
        facturi = self.env['report.d394.facturi'].search([('d394_id', '=', self.d394.id)])
        print(f"Facturi found: {facturi.mapped('name')}")
        self.assertEqual(len(facturi), 3)
        types = set(facturi.mapped('tip_factura'))
        self.assertSetEqual(types, {'1', '2', '3'})

    def test_generate_unlinks_existing(self):
        inv = self._test_create_invoice('out_invoice', state='cancel')
        self.d394.invoice_ids = inv
        self.env['report.d394.facturi'].create({
            'd394_id': self.d394.id,
            'tip_factura': '2',
            'invoice_id': inv.id,
        })
        self.env['report.d394.facturi'].generate(self.d394)
        facturi = self.env['report.d394.facturi'].search([('d394_id', '=', self.d394.id)])
        self.assertEqual(len(facturi), 1)