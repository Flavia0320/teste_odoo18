from odoo.tests.common import TransactionCase, tagged

@tagged('post_install', '-at_install')
class TestResPartnerD394(TransactionCase):

    def setUp(self):
        super().setUp()
        self.env['res.country'].search([]).unlink()
        self.country_ro = self.env['res.country'].create({'name': 'Romania', 'code': 'RO'})
        self.country_fr = self.env['res.country'].create({'name': 'France', 'code': 'FR'})
        self.country_gr = self.env['res.country'].create({'name': 'Greece', 'code': 'GR'})
        self.country_xi = self.env['res.country'].create({'name': 'Northern Ireland', 'code': 'XI'})
        self.country_de = self.env['res.country'].create({'name': 'Germany', 'code': 'DE'})
        self.europe_group = self.env['res.country.group'].create({
            'name': 'Europe',
            'country_ids': [(6, 0, [self.country_fr.id, self.country_gr.id, self.country_de.id, self.country_ro.id, self.country_xi.id])]
        })

    def test_l10n_ro_country_code_from_vat(self):
        partner = self.env['res.partner'].create({
            'name': 'Test RO',
            'vat': 'RO123456',
            'country_id': self.country_ro.id,
            'is_l10n_ro_record': True,
        })
        partner._get_l10n_ro_country_code()
        self.assertEqual(partner.l10n_ro_country_code, 'RO')

    def test_l10n_ro_country_code_from_country(self):
        partner = self.env['res.partner'].create({
            'name': 'Test FR',
            'vat': '',
            'country_id': self.country_fr.id,
            'is_l10n_ro_record': True,
        })
        partner._get_l10n_ro_country_code()
        self.assertEqual(partner.l10n_ro_country_code, 'FR')

    def test_l10n_ro_country_code_map(self):
        partner = self.env['res.partner'].create({
            'name': 'Test RE',
            'vat': 'RE123456',
            'country_id': self.country_fr.id,
            'is_l10n_ro_record': True,
        })
        partner._get_l10n_ro_country_code()
        self.assertEqual(partner.l10n_ro_country_code, 'FR')

        partner2 = self.env['res.partner'].create({
            'name': 'Test EL',
            'vat': 'EL123456',
            'country_id': self.country_gr.id,
            'is_l10n_ro_record': True,
        })
        partner2._get_l10n_ro_country_code()
        self.assertEqual(partner2.l10n_ro_country_code, 'GR')

    def test_l10n_ro_partner_type_domestic_vat(self):
        partner = self.env['res.partner'].create({
            'name': 'Test RO VAT',
            'vat': 'RO123456',
            'country_id': self.country_ro.id,
            'is_l10n_ro_record': True,
            'l10n_ro_vat_subjected': True,
        })
        partner._get_l10n_ro_country_code()
        partner._get_l10n_ro_partner_type()
        self.assertEqual(partner.l10n_ro_partner_type, '1')

    def test_l10n_ro_partner_type_domestic_no_vat(self):
        partner = self.env['res.partner'].create({
            'name': 'Test RO no VAT',
            'vat': 'RO123456',
            'country_id': self.country_ro.id,
            'is_l10n_ro_record': True,
            'l10n_ro_vat_subjected': False,
        })
        partner._get_l10n_ro_country_code()
        partner._get_l10n_ro_partner_type()
        self.assertEqual(partner.l10n_ro_partner_type, '2')

    def test_l10n_ro_partner_type_xi(self):
        partner = self.env['res.partner'].create({
            'name': 'Test XI',
            'vat': 'XI123456',
            'country_id': self.country_xi.id,
            'is_l10n_ro_record': True,
        })
        partner._get_l10n_ro_country_code()
        partner._get_l10n_ro_partner_type()
        self.assertEqual(partner.l10n_ro_partner_type, '3')

    def test_l10n_ro_partner_type_eu(self):
        partner = self.env['res.partner'].create({
            'name': 'Test DE',
            'vat': 'DE123456',
            'country_id': self.country_de.id,
            'is_l10n_ro_record': True,
        })
        partner._get_l10n_ro_country_code()
        partner._get_l10n_ro_partner_type()
        self.assertEqual(partner.l10n_ro_partner_type, '3')

    def test_l10n_ro_partner_type_non_eu(self):
        country_us = self.env['res.country'].create({'name': 'United States', 'code': 'US'})
        partner = self.env['res.partner'].create({
            'name': 'Test US',
            'vat': 'US123456',
            'country_id': country_us.id,
            'is_l10n_ro_record': True,
        })
        partner._get_l10n_ro_country_code()
        partner._get_l10n_ro_partner_type()
        self.assertEqual(partner.l10n_ro_partner_type, '4')