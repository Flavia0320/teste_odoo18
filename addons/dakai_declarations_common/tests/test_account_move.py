from odoo.tests.common import TransactionCase, tagged
from odoo import fields

@tagged('post_install', '-at_install')
class TestAccountMoveD394(TransactionCase):

    def setUp(self):
        super().setUp()
        self.company = self.env['res.company'].create({'name': 'Test Company'})
        self.partner_company = self.env['res.partner'].create({
            'name': 'Company Partner',
            'is_company': True,
            'type': 'invoice',
            'l10n_ro_partner_type': '2',
        })
        self.partner_child = self.env['res.partner'].create({
            'name': 'Child Partner',
            'parent_id': self.partner_company.id,
            'type': 'other',
            'is_company': False,
            'l10n_ro_partner_type': '3',
        })
        self.partner_invoice = self.env['res.partner'].create({
            'name': 'Invoice Partner',
            'type': 'invoice',
            'l10n_ro_partner_type': '1',
        })
        self.fiscal_position = self.env['account.fiscal.position'].create({
            'name': 'Normal',
            'company_id': self.company.id,
        })
        self.company.l10n_ro_affiliated_person_ids = [(6, 0, [self.partner_company.id])]
        self.company.l10n_ro_property_inverse_taxation_position_id = self.fiscal_position

    def test_l10n_ro_parse_vat_partner(self):
        move = self.env['account.move'].create({
            'partner_id': self.partner_company.id,
            'company_id': self.company.id,
        })
        result = move.l10n_ro_parse_vat_partner()
        self.assertEqual(result, self.partner_company)

        move2 = self.env['account.move'].create({
            'partner_id': self.partner_child.id,
            'company_id': self.company.id,
        })
        result2 = move2.l10n_ro_parse_vat_partner()
        self.assertEqual(result2, move2.commercial_partner_id)

        move3 = self.env['account.move'].create({
            'partner_id': self.partner_invoice.id,
            'company_id': self.company.id,
        })
        result3 = move3.l10n_ro_parse_vat_partner()
        self.assertEqual(result3, self.partner_invoice)

    def test_compute_l10n_ro_partner_type(self):
        move = self.env['account.move'].create({
            'partner_id': self.partner_company.id,
            'company_id': self.company.id,
            'is_l10n_ro_record': True,
        })
        move._compute_l10n_ro_partner_type()
        self.assertEqual(move.l10n_ro_partner_type, '2')

        move2 = self.env['account.move'].create({
            'partner_id': self.partner_invoice.id,
            'company_id': self.company.id,
            'is_l10n_ro_record': True,
        })
        move2._compute_l10n_ro_partner_type()
        self.assertEqual(move2.l10n_ro_partner_type, '1')

    def test_onchange_partner_id_affiliated(self):
        move = self.env['account.move'].new({
            'partner_id': self.partner_company.id,
            'company_id': self.company.id,
            'is_l10n_ro_record': True,
        })
        move._onchange_partner_id()
        self.assertEqual(move.fiscal_position_id, self.fiscal_position)

    def test_recompute_dynamic_lines_inverse_tax(self):
        self.env['ir.config_parameter'].sudo().set_param('l10n_ro_anaf_inv_tax_limit', '100')
        self.env['ir.config_parameter'].sudo().set_param('l10n_ro_anaf_inv_tax_date', fields.Date.today())
        categ = self.env['product.category'].create({'name': 'Cat', 'anaf_code': '29'})
        product = self.env['product.product'].create({
            'name': 'Prod',
            'categ_id': categ.id,
        })
        line = (0, 0, {
            'name': 'Line',
            'product_id': product.id,
            'quantity': 1,
            'price_unit': 200,
        })
        move = self.env['account.move'].create({
            'partner_id': self.partner_invoice.id,
            'company_id': self.company.id,
            'invoice_date': fields.Date.today(),
            'is_l10n_ro_record': True,
            'move_type': 'out_invoice',
            'invoice_line_ids': [line],
            'l10n_ro_partner_type': '1',
        })
        move._recompute_dynamic_lines()