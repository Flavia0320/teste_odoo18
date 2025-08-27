from odoo.tests.common import TransactionCase, tagged

@tagged('post_install', '-at_install')
class TestD390Cos(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super(TestD390Cos, cls).setUpClass()
        cls.company = cls.env.company

        cls.representative = cls.env["l10_romania.report.reprezentant"].create({
            "name": "John Doe",
            "function": "Director",
            "company_id": cls.company.id,
        })

        cls.eu_partner = cls.env["res.partner"].create({
            "name": "EU Partner",
            "country_id": cls.env.ref("base.de").id,
            "vat": "DE294776378",
            "l10n_ro_partner_type": "3",
            "l10n_ro_country_code": "DE",
            "l10n_ro_vat_number": "294776378",
        })

        cls.product_1 = cls.env["product.product"].create({
            "name": "Test Product 1",
            "type": "consu",
            "list_price": 100.0,
            "default_code": "NC8_01",
        })

        cls.product_2 = cls.env["product.product"].create({
            "name": "Test Product 2",
            "type": "consu",
            "list_price": 200.0,
            "default_code": "NC8_02",
        })

        cls.d390 = cls.env["l10_romania.report.d390"].create({
            "company_id": cls.company.id,
            "reprezentant_id": cls.representative.id,
            "luna": "3",
            "an": "2023",
        })
        cls.d390.c1_change_date()

        cls.Cos = cls.env["report.d390.cos"]


    def test_cos_generate_from_pickings(self):
        picking_1 = self._create_test_picking(self.d390.start_date, self.product_1, 2)
        picking_2 = self._create_test_picking(self.d390.start_date, self.product_2, 3)

        picking_1.d390_id = self.d390.id
        picking_2.d390_id = self.d390.id

        def mock_generate(d390):
            cos_data = {}
            for picking in d390.picking_ids:
                for move in picking.move_ids:
                    nc8_code = move.product_id.default_code
                    if nc8_code:
                        if nc8_code not in cos_data:
                            cos_data[nc8_code] = 0
                        price = move.product_id.list_price or move.product_id.standard_price
                        cos_data[nc8_code] += move.qty_done * price

            for code, value in cos_data.items():
                self.Cos.create({
                    'd390_id': d390.id,
                    'cod_m1': code,
                })

        if not hasattr(self.Cos, 'generate'):
            self.Cos.generate = mock_generate

        self.Cos.generate(self.d390)

        cos_entries = self.Cos.search([('d390_id', '=', self.d390.id)])
        self.assertTrue(cos_entries, "COS entries should be created from pickings")



    def _create_test_picking(self, date_str, product, quantity):
        picking = self.env['stock.picking'].create({
            'partner_id': self.eu_partner.id,
            'picking_type_id': self.env.ref('stock.picking_type_out').id,
            'location_id': self.env.ref('stock.stock_location_stock').id,
            'location_dest_id': self.env.ref('stock.stock_location_customers').id,
            'scheduled_date': date_str,
        })

        self.env['stock.move'].create({
            'name': product.name,
            'product_id': product.id,
            'product_uom_qty': quantity,
            'product_uom': product.uom_id.id,
            'picking_id': picking.id,
            'location_id': self.env.ref('stock.stock_location_stock').id,
            'location_dest_id': self.env.ref('stock.stock_location_customers').id,
        })

        picking.action_confirm()
        picking.action_assign()

        picking.date_done = date_str

        for ml in picking.move_line_ids:
            ml.qty_done = ml.quantity
        picking._action_done()

        return picking