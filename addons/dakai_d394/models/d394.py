from odoo import api, fields, models, Command, _
from .common_decl import months, period, sistemTVA, tipPersoana
from dateutil.relativedelta import relativedelta
from datetime import datetime, date
import requests
from lxml import etree
from odoo.modules.module import get_module_resource
from odoo.exceptions import ValidationError

class DeclaratiaD394(models.Model):
    _name = "l10_romania.report.d394"
    _inherit = ['mail.thread', 'mail.activity.mixin', "l10n.ro.mixin"]
    _description = "Declaratia D394"

    name = fields.Char(string="Nume", compute="_compute_name", store=True)
    state = fields.Selection([('draft','Draft'),('done','Reported')], default='draft', string="State")

    @api.depends('c1_tip_D394', 'c1_luna', 'c1_an')
    def _compute_name(self):
        for s in self:
            s.name = f"D394_{s.c1_tip_D394} - {s.c1_luna}.{s.c1_an}"

    version = fields.Selection([('v4', 'Versiunea 4')], string="Versiune", default="v4", required=True)
    company_id = fields.Many2one("res.company", string="Companie", required=True)
    template_id = fields.Many2one("report.d394.template", string="Sablon D394")

    reprezentant_id = fields.Many2one("l10_romania.report.reprezentant", string="Reprezentant Declaratie", required=True)

    # declaratie section
    c1_luna = fields.Selection(
        selection=months(),
        default=str(datetime.now().month),
        string="Luna",
        required=True,
        help="Perioada de raportare - Luna"
    )
    c1_an = fields.Selection(
        selection=[(str(num), str(num)) for num in range(2022, ((datetime.now().year)+2))],
        default=str(datetime.now().year),
        string="An",
        required=True,
        help="Perioada de raportare - An"
    )
    c1_tip_D394 = fields.Selection(selection=period(), string="Tip D394", required=True, default="L")
    start_date = fields.Date("Start Date")
    end_date = fields.Date("End Date")

    @api.onchange("c1_luna", "c1_an", "c1_tip_D394")
    def c1_change_date(self):
        if self.c1_tip_D394 == 'L':
            input_dt = datetime(int(self.c1_an), int(self.c1_luna), 1)
            self.start_date = input_dt + relativedelta(day=1)
            self.end_date = input_dt + relativedelta(day=1, days=-1, months=1)
        if self.c1_tip_D394 == 'T':
            if 1 <= int(self.c1_luna) <= 3:
                luna = 3
            if 4 <= int(self.c1_luna) <= 6:
                luna = 6
            if 7 <= int(self.c1_luna) <= 9:
                luna = 9
            if 10 <= int(self.c1_luna) <= 12:
                luna = 12
            input_dt = datetime(int(self.c1_an), int(luna), 1)
            self.start_date = input_dt + relativedelta(day=1, months=-2)
            self.end_date = input_dt + relativedelta(day=1, days=-1, months=1)
        if self.c1_tip_D394 == 'S':
            if 1 <= int(self.c1_luna) <= 6:
                luna = 6
            if 7 <= int(self.c1_luna) <= 12:
                luna = 12
            input_dt = datetime(int(self.c1_an), int(luna), 1)
            self.start_date = input_dt + relativedelta(day=1, months=-5)
            self.end_date = input_dt + relativedelta(day=1, days=-1, months=1)
        if self.c1_tip_D394 == 'A':
            input_dt = datetime(int(self.c1_an), int(12), 1)
            self.start_date = input_dt + relativedelta(day=1, months=-11)
            self.end_date = input_dt + relativedelta(day=1, days=-1, months=1)

    invoice_ids = fields.One2many("account.move", "d394_id")

    def get_invoices(self):
        types = [
            "out_invoice",
            "out_refund",
            "in_invoice",
            "in_refund",
            "out_receipt",
            "in_receipt",
        ]
        invoices = self.env['account.move'].search([
            ('move_type', 'in', types),
            ("date", ">=", self.start_date),
            ("date", "<=", self.end_date),
            ("state", "in", ("posted", "cancel")),
            "|",
            ("company_id", "=", self.company_id.id),
            ("company_id", "in", self.company_id.child_ids.ids)
        ])
        cancel_supp_inv = invoices.filtered(
            lambda i: i.move_type in ["in_invoice", "in_refund", "in_receipt"]
            and i.state == "cancel"
        )
        invoices -= cancel_supp_inv
        return invoices

    paid_invoice_ids = fields.Many2many("account.move")

    def get_paid_invoices(self):
        fp = self.company_id.l10n_ro_property_vat_on_payment_position_id
        if not fp:
            fp = self.env["account.fiscal.position"].search(
                [
                    ("company_id", "=", self.company_id.id),
                    ("name", "=", "Regim TVA la Incasare"),
                ]
            )
        invoices = self.env["account.move"]
        if fp:
            vatp_invoices = self.env["account.move"].search(
                [
                    ("state", "in", ["posted", "cancel"]),
                    ("move_type", "in", ["out_invoice", "out_refund", "in_invoice", "in_refund"]),
                    ("date", ">=", self.company_id.account_opening_date),
                    ("date", "<=", self.end_date),
                    ("fiscal_position_id", "=", fp.id),
                    "|",
                    ("company_id", "=", self.company_id.id),
                    ("company_id", "in", self.company_id.child_ids.ids),
                ]
            )
            for inv in vatp_invoices:

                if inv.payment_state not in ["paid", "reversed", "invoicing_legacy"]:
                    invoices |= inv
                elif inv.payment_state == "paid":
                    for itemrec in inv._get_reconciled_invoices_partials():
                        if not itemrec:
                            continue
                        partial, amount, counterpart_line = itemrec[0]
                        if counterpart_line.date >= self.start_date and counterpart_line.date <= self.end_date:
                            invoices |= inv

        cancel_supp_inv = invoices.filtered(
            lambda i: i.move_type in ["in_invoice", "in_refund", "in_receipt"]
            and i.state == "cancel"
        )
        invoices -= cancel_supp_inv
        return invoices

    # op
    op1_ids = fields.One2many("report.d394.op1", "d394_id")
    op2_ids = fields.One2many("report.d394.op2", "d394_id")

    # rezumat
    rezumat1_ids = fields.One2many("report.d394.rezumat1", "d394_id")
    rezumat2_ids = fields.One2many("report.d394.rezumat2", "d394_id")

    # serie_facturi
    serie_facturi_ids = fields.One2many("report.d394.serie_facturi", "d394_id")

    # facturi
    facturi_ids = fields.One2many("report.d394.facturi", "d394_id")

    # lista
    lista_ids = fields.One2many("report.d394.lista", "d394_id")

    def rebuild_declaration(self):
        for s in self:
            s.invoice_ids.d394_id = False
            invoices = s.get_invoices()
            invoices.d394_id = s.id
            paid_invoices = s.get_paid_invoices()
            s.paid_invoice_ids = [Command.set(paid_invoices.ids)]
            self.env['report.d394.op1'].generate(self)
            self.env['report.d394.op2'].generate(self)
            self.env['report.d394.rezumat1'].generate(self)
            self.env['report.d394.rezumat2'].generate(self)
            self.env['report.d394.serie_facturi'].generate(self)
            self.env['report.d394.facturi'].generate(self)
            self.env['report.d394.lista'].generate(self)
            s._compute_c1_sistemTVA()
            s._get_company_data()
            s._get_reprezentant_data()
            s._compute_intocmit_data()


    c1_sistemTVA = fields.Selection(selection=sistemTVA(), store=True, compute="_compute_c1_sistemTVA", string="Sistemul TVA")

    @api.depends("company_id")
    def _compute_c1_sistemTVA(self):
        for s in self:
            s.c1_sistemTVA = s.company_id.partner_id.l10n_ro_vat_on_payment and "1" or "0"

    c1_op_efectuate = fields.Boolean(string="OP Efectuate", compute="_compute_c1_op_efectuate", store=True)

    @api.depends("rezumat1_ids", "rezumat2_ids")
    def _compute_c1_op_efectuate(self):
        for s in self:
            rulajL = rulajA = 0
            rez_list = s.rezumat1_ids.mapped(lambda x: (x.bazaL, x.bazaA))
            rez_list += s.rezumat2_ids.mapped(lambda x: (x.bazaL, x.bazaA))
            for rL, rA in rez_list:
                rulajL += rL
                rulajA += rA
            s.c1_op_efectuate = rulajL+rulajA > 0

    c1_prsAfiliat = fields.Boolean(string="Operatiuni cu persoane afiliate")

    c1_cui = fields.Char(string="Cod de înregistrare", compute="_get_company_data", store=True)
    c1_den = fields.Char(string="Nume Companie", compute="_get_company_data", store=True)
    c1_adresa = fields.Char(string="Adresă", compute="_get_company_data", store=True)
    c1_telefon = fields.Char(string="Telefon", compute="_get_company_data", store=True)
    c1_caen = fields.Char(string="Cod caen", compute="_get_company_data", store=True)
    c1_mail = fields.Char(string="E-mail", compute="_get_company_data", store=True)

    @api.depends("company_id")
    def _get_company_data(self):
        for s in self:
            s.c1_cui = s.company_id.vat and self.env['res.partner']._split_vat(s.company_id.vat)[1] or False
            s.c1_den = s.company_id.name
            s.c1_adresa = "%s %s %s %s %s" % (
                s.company_id.street or "",
                s.company_id.street2 or "",
                s.company_id.state_id and s.company_id.state_id.name or "",
                s.company_id.zip or "",
                s.company_id.country_id and s.company_id.country_id.name or "",
            )
            s.c1_telefon = s.company_id.phone
            s.c1_caen = s.company_id.l10n_ro_caen_code
            s.c1_mail = s.company_id.email

    c1_totalPlata_A = fields.Integer(string="Suma de control", store=True, compute="_compute_c1_totalPlata_A")

    @api.depends('i_nrCui1', 'i_nrCui2', 'i_nrCui3', 'i_nrCui4',
                 'rezumat2_ids.bazaL', 'rezumat2_ids.bazaA', 'rezumat2_ids.bazaAI')
    def _compute_c1_totalPlata_A(self):
        for s in self:
            s.c1_totalPlata_A = (s.i_nrCui1 + s.i_nrCui2 + s.i_nrCui3 + s.i_nrCui4 +
                                 sum(s.rezumat2_ids.mapped(lambda x: x.bazaL + x.bazaA + x.bazaAI))
                                 )

    c1_cifR = fields.Char(string="Cod de Identificare Reprezentant", compute="_get_reprezentant_data", store=True)
    c1_denR = fields.Char(string="Nume Reprezentant", compute="_get_company_data", store=True)
    c1_functie_reprez = fields.Char(string="Calitatea Reprezentantului", compute="_get_reprezentant_data", store=True)
    c1_adresaR = fields.Char(string="Adresă Reprezentant", compute="_get_reprezentant_data", store=True)
    c1_telefonR = fields.Char(string="Telefon Reprezentant", compute="_get_reprezentant_data", store=True)
    c1_mailR = fields.Char(string="E-mail Reprezentant", compute="_get_reprezentant_data", store=True)

    @api.depends("reprezentant_id")
    def _get_reprezentant_data(self):
        for s in self:
            s.c1_cifR = s.reprezentant_id.is_company and (s.reprezentant_id.vat and self.env['res.partner']._split_vat(s.reprezentant_id.vat)[1] or False) or s.reprezentant_id.cnp
            s.c1_denR = s.reprezentant_id.name
            s.c1_functie_reprez = s.reprezentant_id.function
            s.c1_adresaR = "%s %s %s %s %s" % (
                s.reprezentant_id.street or "",
                s.reprezentant_id.street2 or "",
                s.reprezentant_id.state_id and s.reprezentant_id.state_id.name or "",
                s.reprezentant_id.zip or "",
                s.reprezentant_id.country_id and s.reprezentant_id.country_id.name or "",
            )
            s.c1_telefonR = s.reprezentant_id.phone
            s.c1_mailR = s.reprezentant_id.email

    c1_tip_intocmit = fields.Selection(selection=tipPersoana(), string="Tip Reprezentant", compute="_compute_intocmit_data", store=True)
    c1_den_intocmit = fields.Char(string="Nume Reprezentant", compute="_compute_intocmit_data", store=True)
    c1_cif_intocmit = fields.Char(string="Cod de identificare", compute="_compute_intocmit_data", store=True)
    c1_functie_intocmit = fields.Char(string="Functie intocmit", compute="_compute_intocmit_data", store=True)
    c1_calitate_intocmit = fields.Char(string="Calitate intocmit", compute="_compute_intocmit_data", store=True)

    @api.depends("reprezentant_id")
    def _compute_intocmit_data(self):
        for s in self:
            s.c1_tip_intocmit = s.reprezentant_id.is_company and "0" or "1"
            s.c1_den_intocmit = s.reprezentant_id.name
            s.c1_cif_intocmit = s.reprezentant_id.is_company and (s.reprezentant_id.vat and self.env['res.partner']._split_vat(s.reprezentant_id.vat)[1] or False) or s.reprezentant_id.cnp
            s.c1_functie_intocmit = False
            s.c1_calitate_intocmit = s.reprezentant_id.function

    c1_optiune = fields.Boolean(string="Optiune", help="""
        Optiune referitoare la consultarea de catre
        persoana impozabila a tranzactiilor derulate
        cu aceasta prin intermediul aplicatiilor puse
        la dispozitie de ANAF
    """, default=True)

    # Informatii Section
    i_nrCui1 = fields.Integer(string="Nr parteneri tip [1]", compute="_compute_i_nrcui", store=True)
    i_nrCui2 = fields.Integer(string="Nr parteneri tip [2]", compute="_compute_i_nrcui", store=True)
    i_nrCui3 = fields.Integer(string="Nr parteneri tip [3]", compute="_compute_i_nrcui", store=True)
    i_nrCui4 = fields.Integer(string="Nr parteneri tip [4]", compute="_compute_i_nrcui", store=True)

    @api.depends('op1_ids')
    def _compute_i_nrcui(self):
        for s in self:
            # vars = [("{i.typ_p}_{i.cota}", partner_id) for i in s.op1_ids]
            # nrcui1 = len(set(map(lambda x: '1_' in x[0], vars)))
            # sum(s.op1_ids.filtered(type=1 and cota = 19).mapped(""))
            s.i_nrCui1 = len(s.op1_ids.filtered(lambda x: x.l10n_ro_partner_type == "1").mapped('partner_id'))
            s.i_nrCui2 = len(s.op1_ids.filtered(lambda x: x.l10n_ro_partner_type == "2").mapped('partner_id'))
            s.i_nrCui3 = len(s.op1_ids.filtered(lambda x: x.l10n_ro_partner_type == "3").mapped('partner_id'))
            s.i_nrCui4 = len(s.op1_ids.filtered(lambda x: x.l10n_ro_partner_type == "4").mapped('partner_id'))

    i_nr_BF_i1 = fields.Integer(compute="_compute_i_nrbf11", string="Nr. Bonuri Fiscale I1", help="""
        Total nr bonuri fiscale – incasari in perioada
        de raportare prin intermediul AMEF inclusiv
        incasarile prin intermediul bonurilor fiscale
        care indeplinesc conditiile unei facturi
        simplificate
    """, store=True)

    @api.depends("op2_ids")
    def _compute_i_nrbf11(self):
        for s in self:
            s.i_nr_BF_i1 = sum(s.op2_ids.filtered(lambda x: x.tip_op2 == 'i1').mapped('nrBF'))

    i_incasari_i1 = fields.Integer(compute="_compute_i_incasari", string="Incasari I1", help="""
        Total incasari in perioada de raportare prin
        intermediul AMEF inclusiv incasarile prin
        intermediul bonurilor fiscale care indeplinesc
        conditiile unei facturi simplificate
    """, store=True)
    i_incasari_i2 = fields.Integer(compute="_compute_i_incasari", string="Incasari I2", help="""
        Total incasari in perioada de raportare
        efectuate din activitati exceptate de la
        obligatia utilizarii AMEF
    """, store=True)

    @api.depends("op2_ids")
    def _compute_i_incasari(self):
        for s in self:
            s.i_incasari_i1 = sum(s.op2_ids.filtered(lambda x: x.tip_op2 == 'i1').mapped('total'))
            s.i_incasari_i2 = sum(s.op2_ids.filtered(lambda x: x.tip_op2 == 'i2').mapped('total'))

    i_nrFacturi_terti = fields.Integer(compute="_compute_i_nrFacturi", string="Nr. Facuri Terti", help="""
        Nr total facturi emise in perioada de
        raportare, de terti în numele persoanei
        impozabile
    """, store=True)
    i_nrFacturi_benef = fields.Integer(compute="_compute_i_nrFacturi", string="Nr. Facuri Beneficiari", help="""
        Nr total facturi emise in perioada de
        raportare, de beneficiari în numele persoanei
        impozabile
    """, store=True)
    i_nrFacturi = fields.Integer(compute="_compute_i_nrFacturi", string="Nr total facturi emise", store=True)
    i_nrFacturiL_PF = fields.Integer(compute="_compute_i_nrFacturi", string="Numar facturi emise L", help="""
        Numar facturi emise tip L către persoane
        fizice, cu valoare individuala/persoana mai
        mica sau egala cu 10000 lei - Obligatoriu 0 începând cu 01.01.2017
    """, store=True)
    i_nrFacturiLS_PF = fields.Integer(compute="_compute_i_nrFacturi", string="Numar facturi emise LS", help="""
        Numar facturi emise tip LS către persoane
        fizice, cu valoare individuala/persoana mai
        mica sau egala cu 10000 lei - Obligatoriu 0 începând cu 01.01.2017
    """, store=True)
    i_val_LS_PF = fields.Integer(compute="_compute_i_nrFacturi", string="Valoare livrari LS", help="""
        Valoare livrari tip LS către persoane fizice, cu
        valoare individuala/persoana mai mica sau
        egala cu 10000 lei - Obligatoriu 0 începând cu 01.01.2017
    """, store=True)

    @api.depends('invoice_ids')
    def _compute_i_nrFacturi(self):
        for s in self:
            invoices = s.invoice_ids
            s.i_nrFacturi_terti = len(set(
                    invoices.filtered(
                        lambda r: r.journal_id.l10n_ro_sequence_type == "autoinv2"
                    )
                )
            )
            s.i_nrFacturi_benef = len(
                set(
                    invoices.filtered(
                        lambda r: r.journal_id.l10n_ro_sequence_type == "autoinv1"
                    )
                )
            )
            s.i_nrFacturi = len(
                set(
                    invoices.filtered(
                        lambda r: r.move_type in ("out_invoice", "out_refund")
                    )
                )
            )
            s.i_nrFacturiL_PF = 0 # Obligatoriu 0 începând cu 01.01.2017
            s.i_nrFacturiLS_PF = 0 # Obligatoriu 0 începând cu 01.01.2017
            s.i_val_LS_PF = 0 # Obligatoriu 0 începând cu 01.01.2017

    i_tvaDed24 = fields.Integer(compute="_compute_i_tva", string="TVA Normal Deductibil 24", help="""
        Tva deductibila aferenta facturilor achitate in
        perioada de raportare indiferent de data in
        care acestea au fost primite de la persoane
        impozabile care aplica sistemul normal de
        TVA pt cota TVA=24
    """, store=True)
    i_tvaDed19 = fields.Integer(compute="_compute_i_tva", string="TVA Normal Deductibil 19", help="""
        Tva deductibila aferenta facturilor achitate in
        perioada de raportare indiferent de data in
        care acestea au fost primite de la persoane
        impozabile care aplica sistemul normal de
        TVA pt cota TVA=19
    """,  store=True)
    i_tvaDed20 = fields.Integer(compute="_compute_i_tva", string="TVA Normal Deductibil 20", help="""
        Tva deductibila aferenta facturilor achitate in
        perioada de raportare indiferent de data in
        care acestea au fost primite de la persoane
        impozabile care aplica sistemul normal de
        TVA pt cota TVA=20
    """,  store=True)
    i_tvaDed9 = fields.Integer(compute="_compute_i_tva", string="TVA Normal Deductibil 9", help="""
        Tva deductibila aferenta facturilor achitate in
        perioada de raportare indiferent de data in
        care acestea au fost primite de la persoane
        impozabile care aplica sistemul normal de
        TVA pt cota TVA=9
    """,  store=True)
    i_tvaDed5 = fields.Integer(compute="_compute_i_tva", string="TVA Normal Deductibil 5", help="""
        Tva deductibila aferenta facturilor achitate in
        perioada de raportare indiferent de data in
        care acestea au fost primite de la persoane
        impozabile care aplica sistemul normal de
        TVA pt cota TVA=5
    """,  store=True)

    i_tvaDedAI24 = fields.Integer(compute="_compute_i_tva", string="TVA La Incasare Deductibil 24", help="""
        Tva deductibila aferenta facturilor achitate in
        perioada de raportare indiferent de data in
        care acestea au fost primite de la persoane
        impozabile care aplica sistemul de TVA la
        incasare pt cota TVA = 24
    """,  store=True)
    i_tvaDedAI20 = fields.Integer(compute="_compute_i_tva", string="TVA La Incasare Deductibil 20", help="""
        Tva deductibila aferenta facturilor achitate in
        perioada de raportare indiferent de data in
        care acestea au fost primite de la persoane
        impozabile care aplica sistemul de TVA la
        incasare pt cota TVA = 20
    """,  store=True)
    i_tvaDedAI19 = fields.Integer(compute="_compute_i_tva", string="TVA La Incasare Deductibil 19", help="""
        Tva deductibila aferenta facturilor achitate in
        perioada de raportare indiferent de data in
        care acestea au fost primite de la persoane
        impozabile care aplica sistemul de TVA la
        incasare pt cota TVA = 19
    """,  store=True)
    i_tvaDedAI9 = fields.Integer(compute="_compute_i_tva", string="TVA La Incasare Deductibil 9", help="""
        Tva deductibila aferenta facturilor achitate in
        perioada de raportare indiferent de data in
        care acestea au fost primite de la persoane
        impozabile care aplica sistemul de TVA la
        incasare pt cota TVA = 9
    """,  store=True)
    i_tvaDedAI5 = fields.Integer(compute="_compute_i_tva", string="TVA La Incasare Deductibil 5", help="""
        Tva deductibila aferenta facturilor achitate in
        perioada de raportare indiferent de data in
        care acestea au fost primite de la persoane
        impozabile care aplica sistemul de TVA la
        incasare pt cota TVA = 5
    """,  store=True)

    i_tvaCol24 = fields.Integer(compute="_compute_i_tva", string="TVA Colectata 24", help="""
        Tva colectata aferenta facturilor incasate in
        perioada de raportare indiferent de data la
        care acestea au fost emise de catre
        persoana impozabila care aplica sistemul de
        TVA la incasare pt cota de TVA=24
    """,  store=True)
    i_tvaCol19 = fields.Integer(compute="_compute_i_tva", string="TVA Colectata 19", help="""
        Tva colectata aferenta facturilor incasate in
        perioada de raportare indiferent de data la
        care acestea au fost emise de catre
        persoana impozabila care aplica sistemul de
        TVA la incasare pt cota de TVA=19
    """,  store=True)
    i_tvaCol20 = fields.Integer(compute="_compute_i_tva", string="TVA Colectata 20", help="""
        Tva colectata aferenta facturilor incasate in
        perioada de raportare indiferent de data la
        care acestea au fost emise de catre
        persoana impozabila care aplica sistemul de
        TVA la incasare pt cota de TVA=20
    """,  store=True)
    i_tvaCol9 = fields.Integer(compute="_compute_i_tva", string="TVA Colectata 9", help="""
        Tva colectata aferenta facturilor incasate in
        perioada de raportare indiferent de data la
        care acestea au fost emise de catre
        persoana impozabila care aplica sistemul de
        TVA la incasare pt cota de TVA=9
    """,  store=True)
    i_tvaCol5 = fields.Integer(compute="_compute_i_tva", string="TVA Colectata 5", help="""
        Tva colectata aferenta facturilor incasate in
        perioada de raportare indiferent de data la
        care acestea au fost emise de catre
        persoana impozabila care aplica sistemul de
        TVA la incasare pt cota de TVA=5
    """,  store=True)

    @api.depends('paid_invoice_ids')
    def _compute_i_tva(self):
        for s in self:
            tvaDedAI24 = tvaDedAI20 = tvaDedAI19 = tvaDedAI9 = tvaDedAI5 = 0
            for i in s.paid_invoice_ids.filtered(lambda x: x.move_type in ["in_invoice", "in_refund"]):
                sign = 1
                if "refund" in i.move_type:
                    sign = -1
                taxes = i._prepare_invoice_aggregated_taxes()
                for tax, details in taxes['tax_details'].items():
                    if tax['tax'].amount == 24:
                        tvaDedAI24 += sign * details['tax_amount']
                    if tax['tax'].amount == 20:
                        tvaDedAI20 += sign * details['tax_amount']
                    if tax['tax'].amount == 19:
                        tvaDedAI19 += sign * details['tax_amount']
                    if tax['tax'].amount == 9:
                        tvaDedAI9 += sign * details['tax_amount']
                    if tax['tax'].amount == 5:
                        tvaDedAI5 += sign * details['tax_amount']
            s.i_tvaDedAI24 = int(round(tvaDedAI24))
            s.i_tvaDedAI20 = int(round(tvaDedAI20))
            s.i_tvaDedAI19 = int(round(tvaDedAI19))
            s.i_tvaDedAI9 = int(round(tvaDedAI9))
            s.i_tvaDedAI5 = int(round(tvaDedAI5))

            tvaCol24 = tvaCol20 = tvaCol19 = tvaCol9 = tvaCol5 = 0
            for i in s.paid_invoice_ids.filtered(lambda x: x.move_type in ["out_invoice", "out_refund"]):
                sign = 1
                if "refund" in i.move_type:
                    sign = -1
                taxes = i._prepare_invoice_aggregated_taxes()
                for tax, details in taxes['tax_details'].items():
                    if tax['tax'].amount == 24 and self.c1_sistemTVA == 1:
                        tvaCol24 += sign * details['tax_amount']
                    if tax['tax'].amount == 20 and self.c1_sistemTVA == 1:
                        tvaCol20 += sign * details['tax_amount']
                    if tax['tax'].amount == 19 and self.c1_sistemTVA == 1:
                        tvaCol19 += sign * details['tax_amount']
                    if tax['tax'].amount == 9 and self.c1_sistemTVA == 1:
                        tvaCol9 += sign * details['tax_amount']
                    if tax['tax'].amount == 5 and self.c1_sistemTVA == 1:
                        tvaCol5 += sign * details['tax_amount']
            s.i_tvaCol24 = tvaCol24
            s.i_tvaCol20 = tvaCol20
            s.i_tvaCol19 = tvaCol19
            s.i_tvaCol9 = tvaCol9
            s.i_tvaCol5 = tvaCol5

            s.i_tvaDed24 = 0
            s.i_tvaDed20 = 0
            s.i_tvaDed19 = 0
            s.i_tvaDed9 = 0
            s.i_tvaDed5 = 0

    i_solicit = fields.Boolean("Solicitare rambursare TVA")
    i_achizitiiPE = fields.Boolean(
        "Achzitii Parcuri Eoliene",
        help="Achizitii de bunuri si servicii legate direct de"
        " bunurile imobile: Parcuri Eoliene",
    )
    i_achizitiiCR = fields.Boolean(
        "Achzitii Constructii Rezidentiale",
        help="Achizitii de bunuri si servicii legate direct de"
        " bunurile imobile: constructii rezidentiale",
    )
    i_achizitiiCB = fields.Boolean(
        "Achzitii Cladiri de Birouri",
        help="Achizitii de bunuri si servicii legate direct de"
        " bunurile imobile: cladiri de birouri",
    )
    i_achizitiiCI = fields.Boolean(
        "Achzitii Constructii Industriale",
        help="Achizitii de bunuri si servicii legate direct de"
        " bunurile imobile: constructii industriale",
    )
    i_achizitiiA = fields.Boolean(
        "Alte Achzitii",
        help="Achizitii de bunuri si servicii legate direct de"
        " bunurile imobile: altele",
    )

    i_achizitiiB24 = fields.Boolean(
        "Achzitii Bunuri 24% TVA",
        help="Achizitii de bunuri, cu exceptia celor legate direct"
        " de bunuri imobile cu cota 24%",
    )
    i_achizitiiB20 = fields.Boolean(
        "PAchzitii Bunuri 20% TVA",
        help="Achizitii de bunuri, cu exceptia celor legate direct"
        " de bunuri imobile cu cota 20%",
    )
    i_achizitiiB19 = fields.Boolean(
        "Achzitii Bunuri 19% TVA",
        help="Achizitii de bunuri, cu exceptia celor legate direct"
        " de bunuri imobile cu cota 19%",
    )
    i_achizitiiB9 = fields.Boolean(
        "Achzitii Bunuri 9% TVA",
        help="Achizitii de bunuri, cu exceptia celor legate direct"
        " de bunuri imobile cu cota 9%",
    )
    i_achizitiiB5 = fields.Boolean(
        "PAchzitii Bunuri 5% TVA",
        help="Achizitii de bunuri, cu exceptia celor legate direct"
        " de bunuri imobile cu cota 5%",
    )

    i_achizitiiS24 = fields.Boolean(
        "Achzitii Servicii 24% TVA",
        help="Achizitii de servicii, cu exceptia celor legate direct"
        " de bunuri imobile cu cota 24%",
    )
    i_achizitiiS20 = fields.Boolean(
        "Achzitii Servicii 20% TVA",
        help="Achizitii de servicii, cu exceptia celor legate direct"
        " de bunuri imobile cu cota 20%",
    )
    i_achizitiiS19 = fields.Boolean(
        "Achzitii Servicii 19% TVA",
        help="Achizitii de servicii, cu exceptia celor legate direct"
        " de bunuri imobile cu cota 19%",
    )
    i_achizitiiS9 = fields.Boolean(
        "Achzitii Servicii 9% TVA",
        help="Achizitii de servicii, cu exceptia celor legate direct"
        " de bunuri imobile cu cota 9%",
    )
    i_achizitiiS5 = fields.Boolean(
        "Achzitii Servicii 5% TVA",
        help="Achizitii de servicii, cu exceptia celor legate direct"
        " de bunuri imobile cu cota 5%",
    )
    i_importB = fields.Boolean(
        "Achzitii Bunuri - Importuri",
        help="Importuri de bunuri",
    )
    i_acINecorp = fields.Boolean(
        "Achizitii Imobilizari Necorporale",
        help="Achizitii imobilizari necorporale",
    )

    i_livrariBI = fields.Boolean(
        "Livrari Bunuri imobile",
        help="Livrari de bunuri imobile",
    )
    i_BUN24 = fields.Boolean(
        "Livrari Bunuri 24% TVA",
        help="Livrari de bunuri, cu exceptia bunurilor" " imobile cu cota de 24%",
    )
    i_BUN20 = fields.Boolean(
        "Livrari Bunuri 20% TVA",
        help="Livrari de bunuri, cu exceptia bunurilor" " imobile cu cota de 20%",
    )
    i_BUN19 = fields.Boolean(
        "Livrari Bunuri 19% TVA",
        help="Livrari de bunuri, cu exceptia bunurilor" " imobile cu cota de 19%",
    )
    i_BUN9 = fields.Boolean(
        "Livrari Bunuri 9% TVA",
        help="Livrari de bunuri, cu exceptia bunurilor" " imobile cu cota de 9%",
    )
    i_BUN5 = fields.Boolean(
        "Livrari Bunuri 5% TVA",
        help="Livrari de bunuri, cu exceptia bunurilor" " imobile cu cota de 5%",
    )
    i_valoareScutit = fields.Boolean(
        "Livrari Bunuri Scutite TVA",
        help="Livrari de bunuri scutite de TVA",
    )
    i_BunTI = fields.Boolean(
        "Livrari Bunuri/Servicii - Taxare Inversa",
        help="Livrari de bunuri/prestari de servicii pt care"
        " se aplica taxarea inversa",
    )

    i_Prest24 = fields.Boolean(
        "Prestari Servicii 24% TVA",
        help="Prestari de servicii cu cota de 24%",
    )
    i_Prest20 = fields.Boolean(
        "Prestari Servicii 20% TVA",
        help="Prestari de servicii cu cota de 20%",
    )
    i_Prest19 = fields.Boolean(
        "Prestari Servicii 19% TVA",
        help="Prestari de servicii cu cota de 19%",
    )
    i_Prest9 = fields.Boolean(
        "Prestari Servicii 9% TVA",
        help="Prestari de servicii cu cota de 9%",
    )
    i_Prest5 = fields.Boolean(
        "Prestari servicii 5% TVA",
        help="Prestari de servicii cu cota de 5%",
    )
    i_PrestScutit = fields.Boolean(
        "Prestari Servicii Scutite TVA",
        help="Prestari de servicii scutite de TVA",
    )

    i_LIntra = fields.Boolean(
        "Livrari Bunuri Intracomunitare",
        help="Livrari intracomunitare de bunuri",
    )
    i_PrestIntra = fields.Boolean(
        "Prestari Sericii Intracomunitare",
        help="Prestari intracomunitare de servicii",
    )
    i_Export = fields.Boolean(
        "Exporturi Bunuri",
        help="Exporturi de bunuri",
    )
    i_livINecorp = fields.Boolean(
        "Livrari Imobilizari Necorporale",
        help="Livrari imobilizari necorporale",
    )

    def clean_read(self, obj):
        objdata = obj.read()[0]
        for key, value in objdata.items():
            if isinstance(value, list) and key == 'op11_ids':
                items = getattr(obj, key)
                if items:
                    objdata[key] = []
                    for item in items:
                        skip_tvaPr = False
                        if item.op1_id.l10n_ro_partner_type == '2' or (item.op1_id.l10n_ro_partner_type == '1' and item.op1_id.l10n_ro_operation_type in ['V']):
                            skip_tvaPr = True
                        objdata[key] += [{'codPR': str(item.codPR),
                                          'bazaPR': str(item.bazaPR),
                                          'nrFactPR': str(item.nrFactPR)}]  # getattr(obj, key).read()
                        if not skip_tvaPr:
                            objdata[key][0].update({'tvaPR': str(item.tvaPR),})
            if isinstance(value, list) and key == 'rezumat1_detaliu_ids' and obj._name == 'report.d394.rezumat1':
                items = getattr(obj, key)
                if items:
                    objdata[key] = []
                    for item in items:
                        detalii = {
                                   'bun': str(item.bun),
                                }
                        if item.nrLivV:
                            detalii.update({
                                   'nrLivV': str(int(item.nrLivV)),
                                   'bazaLivV': str(int(item.bazaLivV)),
                                })
                        if item.nrAchizC:
                            detalii.update({
                                   'nrAchizC': str(int(item.nrAchizC)),
                                   'bazaAchizC': str(int(item.bazaAchizC)),
                                   'tvaAchizC': str(int(item.tvaAchizC)),
                                })
                        if item.nrN:
                            detalii.update({
                                    'nrN': str(int(item.nrN)),
                                    'valN': str(int(item.valN)),
                                })
                        objdata[key] += [detalii] #getattr(obj, key).read()
        for k, v in objdata.items():
            if isinstance(v, datetime) or isinstance(v, date):
                objdata[k] = v.strftime("%H:%M:%S")
            if isinstance(v, bool):
                objdata[k] = v and '1' or '0'
        return objdata

    def export_declaration(self):
        self.ensure_one()
        # Create file content.
        objdata = self.clean_read(self)
        objdata['facturi_ids'] = []
        for facturi in self.facturi_ids:
            objdata['facturi_ids'] += [self.clean_read(facturi)]
        objdata['lista_ids'] = []
        for lista in self.lista_ids:
            objdata['lista_ids'] += [self.clean_read(lista)]
        objdata['op1_ids'] = []
        for op1 in self.op1_ids:
            objdata['op1_ids'] += [self.clean_read(op1)]
        objdata['op2_ids'] = []
        for op2 in self.op2_ids:
            objdata['op2_ids'] += [self.clean_read(op2)]
        objdata['rezumat1_ids'] = []
        for rezumat1 in self.rezumat1_ids:
            objdata['rezumat1_ids'] += [self.clean_read(rezumat1)]
        objdata['rezumat2_ids'] = []
        for rezumat2 in self.rezumat2_ids:
            objdata['rezumat2_ids'] += [self.clean_read(rezumat2)]
        objdata['serie_facturi_ids'] = []
        for serie_facturi in self.serie_facturi_ids:
            objdata['serie_facturi_ids'] += [self.clean_read(serie_facturi)]

        l10n_ro_decalaration_url = self.env['ir.config_parameter'].sudo().get_param('dakai_declarations_common.l10n_ro_decalaration_url')
        if not l10n_ro_decalaration_url:
            raise ValidationError(_("URL-ul pentru trimitere declaratie nu este setat."))

        response = requests.post('%s/d394_data_to_xml' % l10n_ro_decalaration_url, json=objdata, timeout=80)

        xml_name = "%s.xml" % (self.name)
        xml_content = response.json().get("result")

        xml_doc = etree.fromstring(xml_content.encode())
        schema_file_path = get_module_resource(
            "dakai_d394", "static/schemas", "D394.xsd"
        )
        xml_schema = etree.XMLSchema(etree.parse(open(schema_file_path)))

        is_valid = xml_schema.validate(xml_doc)

        if not is_valid:
            self.message_post(body=_("Validation Error: %s") % xml_schema.error_log.last_error)

        domain = [
            ("name", "=", xml_name),
            ("res_model", "=", "l10_romania.report.d394"),
            ("res_id", "=", self.id),
        ]
        attachments = self.env["ir.attachment"].search(domain)
        attachments.unlink()
        return self.env["ir.attachment"].create(
            {
                "name": xml_name,
                "raw": xml_content,
                "res_model": "l10_romania.report.d394",
                "res_id": self.id,
                "mimetype": "application/xml",
            }
        )
