from odoo.tests.common import TransactionCase, tagged
from odoo import fields
from unittest.mock import patch
from datetime import date, timedelta

@tagged('post_install', '-at_install')
class TestDeclaratiaD394Rezumat2(TransactionCase):

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
        self.journal_purchase = self.env['account.journal'].create({
            'name': 'Purchase Journal',
            'type': 'purchase',
            'code': 'PURCHASE',
            'l10n_ro_sequence_type': 'normal',
            'refund_sequence': True,
            'company_id': self.company.id,
        })
        self.account = self.env['account.account'].create({
            'name': 'Test Revenue',
            'code': 'TESTREV',
            'reconcile': False,
            'company_ids': [(6, 0, [self.company.id])],
            'account_type': 'income',
        })
        self.fiscal_position = self.env['account.fiscal.position'].create({
            'name': 'Regim TVA la Incasare',
            'company_id': self.company.id,
        })
        representant = self.env['l10_romania.report.reprezentant'].search([], limit=1)
        if not representant:
            representant = self.env['l10_romania.report.reprezentant'].create({'name': 'Test Reprezentant'})
        self.company.l10n_ro_property_vat_on_payment_position_id = self.fiscal_position
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
        self.partner2 = self.env['res.partner'].create({
            'name': 'Test Partner2',
            'property_account_receivable_id': self.receivable_account.id,
            'property_account_payable_id': self.payable_account.id,
        })
        tax_group = self.env['account.tax.group'].search([
            ('country_id', '=', self.country.id),
            ('company_id', '=', self.company.id)
        ], limit=1)
        if not tax_group:
            tax_group = self.env['account.tax.group'].create({'name': 'Test Group', 'sequence': 1, 'company_id': self.company.id, 'country_id': self.country.id})

        self.tax_19 = self.env['account.tax'].create({
            'name': 'TVA 19%',
            'amount': 19,
            'type_tax_use': 'sale',
            'company_id': self.company.id,
            'tax_group_id': tax_group.id,
            'country_id': self.country.id,
        })
        self.tax_5 = self.env['account.tax'].create({
            'name': 'TVA 5%',
            'amount': 5,
            'type_tax_use': 'sale',
            'company_id': self.company.id,
            'tax_group_id': tax_group.id,
            'country_id': self.country.id,
        })
        self.op1_L = self.env['report.d394.op1'].create({
            'l10n_ro_operation_type': 'L',
            'nrFact': 2,
            'baza': 100,
            'tva': 19,
            'cota': 19,
        })
        self.op1_A = self.env['report.d394.op1'].create({
            'l10n_ro_operation_type': 'A',
            'nrFact': 1,
            'baza': 50,
            'tva': 5,
            'cota': 5,
        })
        self.d394.op1_ids = self.op1_L + self.op1_A

    def _test_create_invoice(self, move_type, cota, simple, has_vat, partner_type, fiscal_position=None, state='posted',
                        partner=None):
        tax = self.tax_19 if cota == 19 else self.tax_5
        journal = self.journal if move_type in ('out_invoice', 'out_refund', 'out_receipt') else self.journal_purchase
        invoice = self.env['account.move'].create({
            'move_type': move_type,
            'partner_id': partner.id,
            'company_id': self.company.id,
            'journal_id': journal.id,
            'invoice_date': date.today(),
            'l10n_ro_simple_invoice': simple,
            'l10n_ro_has_vat_number': has_vat,
            'l10n_ro_partner_type': partner_type,
            'fiscal_position_id': fiscal_position and fiscal_position.id or False,
            'invoice_line_ids': [(0, 0, {
                'name': 'Line',
                'quantity': 1,
                'price_unit': 100,
                'tax_ids': [(6, 0, [tax.id])],
                'account_id': self.revenue_account.id,
                'company_id': self.company.id,
            })],
        })

        def fake_agg_taxes():
            return {'tax_details': {
                {'tax': tax}: {'base_amount': 100, 'tax_amount': tax.amount, 'tax': tax}
            }}

        with patch.object(type(invoice), '_prepare_invoice_aggregated_taxes', fake_agg_taxes):
            if state == 'posted':
                invoice.action_post()
            return invoice

    def test_compute_name(self):
        rez = self.env['report.d394.rezumat2'].create({
            'cota': 19,
        })
        rez._compute_name()
        self.assertEqual(rez.name, 'Rezumat2 - 19%')

    def test_computeL_fields(self):
        invoice1 = self._test_create_invoice(
            move_type='out_invoice',
            cota=19,
            simple=True,
            has_vat=True,
            partner_type='1',
            partner=self.partner
        )
        invoice2 = self._test_create_invoice(
            move_type='out_invoice',
            cota=19,
            simple=True,
            has_vat=True,
            partner_type='1',
            partner=self.partner
        )
        self.op1_L.write({'invoice_ids': [(4, invoice1.id)]})
        self.op1_A.write({'invoice_ids': [(4, invoice2.id)]})
        rez = self.env['report.d394.rezumat2'].create({
            'op1_ids': [(6, 0, [self.op1_L.id, self.op1_A.id])],
        })
        rez._computeL()
        self.assertEqual(rez.nrFacturiL, 1)
        self.assertEqual(rez.bazaL, 100)
        self.assertEqual(rez.tvaL, 19)

    # def test_computeA_fields(self):
    #     rez = self.env['report.d394.rezumat2'].create({})
    #     rez.op1_ids = [(6, 0, [self.op1_L.id, self.op1_A.id])]
    #     rez._computeA()
    #     self.assertEqual(rez.nrFacturiA, 1)
    #     self.assertEqual(rez.bazaA, 50)
    #     self.assertEqual(rez.tvaA, 5)
    #
    # def test_computeAI_fields(self):
    #     op1_AI = self.env['report.d394.op1'].create({
    #         'l10n_ro_operation_type': 'AI',
    #         'nrFact': 3,
    #         'baza': 300,
    #         'tva': 57,
    #         'cota': 19,
    #     })
    #     rez = self.env['report.d394.rezumat2'].create({})
    #     rez.op1_ids = [(6, 0, [op1_AI.id])]
    #     rez._computeAI()
    #     print(f"rez.nrFacturiAI: {rez.nrFacturiAI}, rez.bazaAI: {rez.bazaAI}, rez.tvaAI: {rez.tvaAI}")
    #     self.assertEqual(rez.nrFacturiAI, 3)
    #     self.assertEqual(rez.bazaAI, 300)
    #     self.assertEqual(rez.tvaAI, 57)

    def test_generate_creates_one_per_cota(self):
        self.env['report.d394.rezumat2'].generate(self.d394)
        rezs = self.env['report.d394.rezumat2'].search([('d394_id', '=', self.d394.id)])
        cotas = set(rezs.mapped('cota'))
        self.assertSetEqual(cotas, {5, 9, 19, 20, 24})
        self.assertEqual(len(rezs), 5)

    def test_computeFSLcod_and_FSL(self):
        inv1 = self._test_create_invoice('out_receipt', 19, True, True, '1', partner=self.partner2)
        inv2 = self._test_create_invoice('out_receipt', 19, True, False, '1', partner=self.partner)
        self.d394.invoice_ids = inv1 + inv2
        rez = self.env['report.d394.rezumat2'].create({
            'd394_id': self.d394.id,
            'cota': 19,
        })
        rez._computeFSLcod()
        rez._computeFSL()
        self.assertEqual(rez.bazaFSLcod, 100)
        self.assertEqual(rez.TVAFSLcod, 19)
        self.assertEqual(rez.bazaFSL, 100)
        self.assertEqual(rez.TVAFSL, 19)

    def test_computeFSA_and_BFAI(self):
        inv_fsa = self._test_create_invoice('in_receipt', 19, True, True, '2', partner=self.partner)
        inv_bfai = self._test_create_invoice('in_receipt', 19, False, True, '2', fiscal_position=self.fiscal_position, partner=self.partner2)
        self.d394.invoice_ids = inv_fsa + inv_bfai
        rez = self.env['report.d394.rezumat2'].create({
            'd394_id': self.d394.id,
            'cota': 19,
        })
        rez._computeFSA()
        rez._computeBFAI()
        self.assertEqual(rez.bazaFSA, 100)
        self.assertEqual(rez.TVAFSA, 19)
        self.assertEqual(rez.bazaBFAI, 100)
        self.assertEqual(rez.TVABFAI, 19)

    def test_computeFSAI(self):
        inv_fsai = self._test_create_invoice('in_receipt', 19, True, True, '2', partner=self.partner, fiscal_position=self.fiscal_position)
        self.d394.invoice_ids = inv_fsai
        rez = self.env['report.d394.rezumat2'].create({
            'd394_id': self.d394.id,
            'cota': 19,
        })
        rez._computeFSAI()
        self.assertEqual(rez.bazaFSAI, 100)
        self.assertEqual(rez.TVAFSAI, 19)

    # def test_computeI1_and_I2(self):
    #     op2_i1 = self.env['report.d394.op2'].create({
    #         'tip_op2': 'i1',
    #         'baza19': 200,
    #         'tva19': 38,
    #     })
    #     op2_i2 = self.env['report.d394.op2'].create({
    #         'tip_op2': 'i2',
    #         'baza19': 150,
    #         'tva19': 28,
    #     })
    #     self.d394.op2_ids = op2_i2 + op2_i1
    #     rez = self.env['report.d394.rezumat2'].create({
    #         'd394_id': self.d394.id,
    #         'cota': 19,
    #     })
    #     rez._computeI1()
    #     rez._computeI2()
    #     print(f"rez.baza_incasari_i1: {rez.baza_incasari_i1}, rez.tva_incasari_i1: {rez.tva_incasari_i1}")
    #     print(f"rez.baza_incasari_i2: {rez.baza_incasari_i2}, rez.tva_incasari_i2: {rez.tva_incasari_i2}")
    #     self.assertEqual(rez.baza_incasari_i1, 200)
    #     self.assertEqual(rez.tva_incasari_i1, 38)
    #     self.assertEqual(rez.baza_incasari_i2, 150)
    #     self.assertEqual(rez.tva_incasari_i2, 28)