from odoo.tests.common import TransactionCase, tagged
from odoo import fields

@tagged('post_install', '-at_install')
class TestAccountMoveD394(TransactionCase):

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
        self.tax_group = self.env['account.tax.group'].search([
            ('country_id', '=', self.country.id),
            ('company_id', '=', self.company.id)
        ], limit=1)
        if not self.tax_group:
            self.tax_group = self.env['account.tax.group'].create(
                {'name': 'Test Group', 'sequence': 1, 'company_id': self.company.id, 'country_id': self.country.id})
        self.tax_19 = self.env['account.tax'].create({
            'name': 'TVA 19%',
            'amount': 19,
            'type_tax_use': 'sale',
            'company_id': self.company.id,
            'tax_group_id': self.tax_group.id,
            'country_id': self.country.id,
        })
        self.tax_5 = self.env['account.tax'].create({
            'name': 'TVA 5%',
            'amount': 5,
            'type_tax_use': 'sale',
            'company_id': self.company.id,
            'tax_group_id': self.tax_group.id,
            'country_id': self.country.id,
        })
        self.revenue_account = self.env['account.account'].search([('name', '=', 'Other Income')], limit=1)
        self.revenue_account.write({'company_ids': self.company.id})
        if not self.revenue_account:
            self.revenue_account = self.env['account.account'].create({
                'name': 'Other Income',
                'code': 'OTHINC',
                'company_ids': self.company.id,
                'active': True,
                'account_type': 'income',
            })

        self.receivable_account = self.env['account.account'].create({
            'name': 'Receivable',
            'code': 'CUSTREC',
            'company_ids': self.company.id,
            'account_type': 'asset_receivable',
        })
        self.payable_account = self.env['account.account'].create({
            'name': 'Payable',
            'code': 'CUSTPAY',
            'company_ids': self.company.id,
            'account_type': 'liability_payable',
        })
        self.parent_partner = self.env['res.partner'].create({
            'name': 'Parent Partner',
            'vat': 'RO10455220',
            'is_company': True,
            'type': 'invoice',
        })
        self.child_partner = self.env['res.partner'].create({
            'name': 'Child Partner',
            'parent_id': self.parent_partner.id,
            'vat': 'RO23422586',
            'is_company': False,
            'type': 'contact',
        })
        self.journal = self.env['account.journal'].create({
            'name': 'Test Sale Journal',
            'type': 'sale',
            'code': 'TST',
            'company_id': self.company.id,
        })
        self.journal_purchase = self.env['account.journal'].create({
            'name': 'Test Purchase Journal',
            'type': 'purchase',
            'code': 'TSTP',
            'company_id': self.company.id,
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner',
            'vat': 'RO30678383',
            'is_company': True,
            'type': 'invoice',
            'property_account_receivable_id': self.receivable_account.id,
            'property_account_payable_id': self.payable_account.id,
            'l10n_ro_partner_type': '1',
        })
        self.partner.l10n_ro_partner_type = '1'
        self.fiscal_position = self.env['account.fiscal.position'].create({
            'name': 'Regim Taxare Inversa',
            'company_id': self.company.id,
        })
        self.tva_fp = self.env['account.fiscal.position'].create({
            'name': 'Regim TVA la Incasare',
            'company_id': self.company.id,
        })
        self.fiscal_position2 = self.env['account.fiscal.position'].create({
            'name': 'Alta Fiscal Position',
            'company_id': self.company.id,
        })

        self.company.l10n_ro_property_inverse_taxation_position_id = self.fiscal_position
        self.company.l10n_ro_property_vat_on_payment_position_id = self.tva_fp

    def test_l10n_ro_parse_vat_partner_parent(self):
        move = self.env['account.move'].create({
            'partner_id': self.child_partner.id,
            'company_id': self.company.id,
            'move_type': 'out_invoice',
            'is_l10n_ro_record': True,
            'journal_id': self.journal.id,
        })
        partner = move.l10n_ro_parse_vat_partner()
        self.assertEqual(partner, move.commercial_partner_id)

    def test_l10n_ro_parse_vat_partner_no_parent(self):
        move = self.env['account.move'].create({
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'move_type': 'out_invoice',
            'is_l10n_ro_record': True,
            'journal_id': self.journal.id,
        })
        partner = move.l10n_ro_parse_vat_partner()
        self.assertEqual(partner, self.partner)

    def test_compute_l10n_ro_invoice_partner_display_vat_no_vat(self):
        partner = self.env['res.partner'].create({'name': 'No VAT Partner'})
        move = self.env['account.move'].create({
            'partner_id': partner.id,
            'company_id': self.company.id,
            'move_type': 'out_invoice',
            'is_l10n_ro_record': True,
            'journal_id': self.journal.id,
        })
        move._compute_l10n_ro_invoice_partner_display_vat()
        self.assertEqual(move.l10n_ro_invoice_partner_display_vat, '')

    def test_onchange_l10n_ro_simple_invoice_false(self):
        move = self.env['account.move'].create({
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'move_type': 'out_invoice',
            'is_l10n_ro_record': True,
            'l10n_ro_simple_invoice': False,
            'journal_id': self.journal.id,
        })
        move._onchange_l10n_ro_simple_invoice()
        self.assertFalse(move.l10n_ro_has_vat_number)

    def test_compute_l10n_ro_operation_type_special_regim(self):
        self.partner.l10n_ro_partner_type = '2'
        move = self.env['account.move'].create({
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'move_type': 'out_invoice',
            'is_l10n_ro_record': True,
            'l10n_ro_special_regim': True,
            'fiscal_position_id': self.fiscal_position2.id,
            'l10n_ro_partner_type': '2',
            'journal_id': self.journal.id,
        })
        self.env['account.move.line'].create({
            'move_id': move.id,
            'product_id': self.product.id,
            'quantity': 1,
            'price_unit': 100,
            'account_id': self.revenue_account.id,
            'display_type': 'product',
            'tax_ids': [(6, 0, [self.tax_19.id])],
            'company_id': self.company.id,
        })
        move._compute_l10n_ro_operation_type()
        self.assertIn(move.l10n_ro_operation_type, ['LS', 'V', 'L'])

    def test_compute_l10n_ro_operation_type_in_receipt(self):
        expense_account = self.env['account.account'].create({
            'name': 'Expense Account',
            'code': 'EXPACC',
            'company_ids': self.company.id,
            'account_type': 'expense',
        })
        move = self.env['account.move'].create({
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'move_type': 'in_receipt',
            'is_l10n_ro_record': True,
            'l10n_ro_simple_invoice': False,
            'l10n_ro_has_vat_number': False,
            'l10n_ro_partner_type': '1',
            'journal_id': self.journal_purchase.id,
            'commercial_partner_id': self.partner.id,
        })
        self.env['account.move.line'].create({
            'name': 'Receipt Line',
            'move_id': move.id,
            'product_id': self.product.id,
            'quantity': 1,
            'price_unit': 100,
            'account_id': expense_account.id,
            'company_id': self.company.id,
            'display_type': 'product',
            'credit': 119.0,
            'debit': 0.0,
            'tax_ids': [(6, 0, [self.tax_19.id])],
        })
        move._compute_l10n_ro_operation_type()
        self.assertIn(move.l10n_ro_operation_type, ['AS', 'A'])

    def test_compute_l10n_ro_operation_type_tva_fp(self):
        expense_account = self.env['account.account'].create({
            'name': 'Expense Account 2',
            'code': 'EXPACC2',
            'company_ids': self.company.id,
            'account_type': 'expense',
        })
        move = self.env['account.move'].create({
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'move_type': 'in_invoice',
            'is_l10n_ro_record': True,
            'fiscal_position_id': self.tva_fp.id,
            'l10n_ro_partner_type': '1',
            'journal_id': self.journal_purchase.id,
            'commercial_partner_id': self.partner.id,
        })
        self.env['account.move.line'].create({
            'move_id': move.id,
            'product_id': self.product.id,
            'quantity': 1,
            'price_unit': 100,
            'account_id': expense_account.id,
            'company_id': self.company.id,
            'display_type': 'product',
            'credit': 119.0,
            'debit': 0.0,
            'tax_ids': [(6, 0, [self.tax_19.id])],
        })
        move._compute_l10n_ro_operation_type()
        self.assertIn(move.l10n_ro_operation_type, ['AI', 'A'])