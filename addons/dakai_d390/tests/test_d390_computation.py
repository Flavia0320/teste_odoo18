from odoo.tests.common import TransactionCase,  tagged
from dateutil.relativedelta import relativedelta

@tagged('post_install', '-at_install')
class TestD390Computation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super(TestD390Computation, cls).setUpClass()
        cls.company = cls.env.company

        cls.representative = cls.env["l10_romania.report.reprezentant"].create({
            "name": "John Doe",
            "function": "Director",
            "company_id": cls.company.id,
        })

        cls.eu_partner_1 = cls.env["res.partner"].create({
            "name": "EU Partner 1",
            "country_id": cls.env.ref("base.de").id,
            "vat": "DE294776378",
            "l10n_ro_partner_type": "3",
        })

        cls.eu_partner_2 = cls.env["res.partner"].create({
            "name": "EU Partner 2",
            "country_id": cls.env.ref("base.fr").id,
            "vat": "NL004983269B01",
            "l10n_ro_partner_type": "3",
        })

        cls.product = cls.env["product.product"].create({
            "name": "Test Product",
            "type": "product",
            "list_price": 100.0,
        })

        cls.tax_eu = cls.env["account.tax"].create({
            "name": "0% EU",
            "amount": 0,
            "amount_type": "percent",
            "type_tax_use": "sale",
        })

        cls.d390 = cls.env["l10_romania.report.d390"].create({
            "company_id": cls.company.id,
            "reprezentant_id": cls.representative.id,
            "luna": "3",
            "an": "2023",
        })
        cls.d390.c1_change_date()

        cls.Operatie = cls.env["report.d390.operatie"]
        cls.Cos = cls.env["report.d390.cos"]

        cls.operatie_types = {
            'L': cls._create_operatie(cls, 'L', 1000),  # Livrari
            'T': cls._create_operatie(cls, 'T', 2000),  # Triangulare
            'A': cls._create_operatie(cls, 'A', 3000),  # Achizitii
            'P': cls._create_operatie(cls, 'P', 4000),  # Prestari
            'S': cls._create_operatie(cls, 'S', 5000),  # Servicii
            'R': cls._create_operatie(cls, 'R', 6000),  # Regularizari
        }

        cls.cos_1 = cls._create_cos(cls, 'NC8_01', 1000)
        cls.cos_2 = cls._create_cos(cls, 'NC8_02', 2000)

    def _create_operatie(self, tip, baza):
        return self.Operatie.create({
            'd390_id': self.d390.id,
            'tip': tip,
            'tara': 'DE',
            'codO': '294776378',
            'denO': 'Test Partner',
            'baza': baza,
        })

    def _create_cos(self, cod, val):
        return self.Cos.create({
            'd390_id': self.d390.id,
            'cod_m1': cod,
        })

    def test_rezumat_nrOPI_computation(self):
        self.d390._compute_rezumat_data()

        self.assertEqual(self.d390.rezumat_nrOPI, 6,
                         "rezumat_nrOPI should equal the number of operatie records")

    def test_rezumat_baza_computations(self):
        self.d390._compute_rezumat_data()

        self.assertEqual(self.d390.rezumat_bazaL, 1000, "rezumat_bazaL should equal the sum of L operations")
        self.assertEqual(self.d390.rezumat_bazaT, 2000, "rezumat_bazaT should equal the sum of T operations")
        self.assertEqual(self.d390.rezumat_bazaA, 3000, "rezumat_bazaA should equal the sum of A operations")
        self.assertEqual(self.d390.rezumat_bazaP, 4000, "rezumat_bazaP should equal the sum of P operations")
        self.assertEqual(self.d390.rezumat_bazaS, 5000, "rezumat_bazaS should equal the sum of S operations")
        self.assertEqual(self.d390.rezumat_bazaR, 6000, "rezumat_bazaR should equal the sum of R operations")

    def test_rezumat_total_baza_computation(self):
        self.d390._compute_rezumat_data()

        expected_total = 1000 + 2000 + 3000 + 4000 + 5000 + 6000
        self.assertEqual(self.d390.rezumat_total_baza, expected_total,
                         "rezumat_total_baza should equal the sum of all baza values")

    def test_rezumat_nr_pag_computation(self):
        self.d390._compute_rezumat_data()

        expected_pages = 6 + 2
        self.assertEqual(self.d390.rezumat_nr_pag, expected_pages,
                         "rezumat_nr_pag should equal the number of operations plus COS entries")

    def test_totalPlata_A_computation(self):
        self.d390._compute_rezumat_data()

        expected_total = 6 + (1000 + 2000 + 3000 + 4000 + 5000 + 6000)  # nrOPI + total_baza
        self.assertEqual(self.d390.totalPlata_A, expected_total,
                         "totalPlata_A should equal rezumat_nrOPI + rezumat_total_baza")

