from odoo import api, fields, models, Command, _
from .common_decl import months, period
from dateutil.relativedelta import relativedelta
from datetime import datetime, date
from lxml import etree
from odoo.modules.module import get_module_resource
import requests
from odoo.exceptions import ValidationError

class DeclaratiaD300(models.Model):
    _name = "l10_romania.report.d300"
    _inherit = ['mail.thread', 'mail.activity.mixin', "l10n.ro.mixin"]
    _description = "Declaratia D300"

    name = fields.Char(compute="_compute_name", store=True)

    @api.depends('tip_D300', 'luna', 'an')
    def _compute_name(self):
        for s in self:
            s.name = f"D300_{s.tip_D300} - {s.luna}.{s.an}"

    version = fields.Selection([('v8', 'Versiunea 8')], default="v8", required=True)
    company_id = fields.Many2one("res.company", required=True)

    # TODO Templates
    # template_id = fields.Many2one("report.d300.template")
    depus_reprezentant = fields.Boolean("Depus Reprezentant")
    bifa_interne = fields.Boolean(string="Metoda simplificata operatiuni interne", default=False)
    temei = fields.Selection(
        [
            ("0", "Normal"),
            ("2", "Cf art. 105 alin. (6) lit. b) din Legea nr. 207/2015"),
        ],
        string="Temei",
        default="0",
    )

    succesor_id = fields.Many2one("res.partner", string="Succesor")
    cui_succesor = fields.Char(string="Cui Succesor", compute="_get_succesor_data", store=True)

    @api.depends("succesor_id")
    def _get_succesor_data(self):
        for s in self:
            s.cui_succesor = s.succesor_id and s.succesor_id.l10n_ro_vat_number or False

    reprezentant_id = fields.Many2one("l10_romania.report.reprezentant", domain="[('is_company', '=', False)]", string="Reprezentant Declaratie", required=True)
    nume_declar = fields.Char(string="Nume declarant", compute="_get_reprezentant_data", store=True)
    prenume_declar = fields.Char(string="Prenume declarant", compute="_get_reprezentant_data", store=True)
    functie_declar = fields.Char(string="Functie declarant", compute="_get_reprezentant_data", store=True)

    @api.depends("reprezentant_id")
    def _get_reprezentant_data(self):
        for s in self:
            s.nume_declar = s.reprezentant_id and s.reprezentant_id.name.split(" ")[0]
            s.prenume_declar = s.reprezentant_id and s.reprezentant_id.name.split(" ")[1]
            s.functie_declar = s.reprezentant_id and s.reprezentant_id.function

    cui = fields.Char(string="Cod de înregistrare", compute="_get_company_data", store=True)
    den = fields.Char(string="Nume Companie", compute="_get_company_data", store=True)
    adresa = fields.Char(string="Adresă", compute="_get_company_data", store=True)
    telefon = fields.Char(string="Telefon", compute="_get_company_data", store=True)
    caen = fields.Char(string="Cod caen", compute="_get_company_data", store=True)
    mail = fields.Char(string="E-mail", compute="_get_company_data", store=True)
    bank_account_id = fields.Many2one("res.partner.bank", string="Bank Account", compute="_get_company_data", store=True)
    banca = fields.Char(string="Bank", compute="_get_company_data", store=True)
    cont = fields.Char(string="Bank Account", compute="_get_company_data", store=True)

    @api.depends("company_id")
    def _get_company_data(self):
        for s in self:
            s.cui = s.company_id.vat and self.env['res.partner']._split_vat(s.company_id.vat)[1] or False
            s.den = s.company_id.name
            s.adresa = "%s %s %s %s %s" % (
                s.company_id.partner_id.street or "",
                s.company_id.partner_id.street2 or "",
                s.company_id.partner_id.state_id and s.company_id.partner_id.state_id.name or "",
                s.company_id.partner_id.zip or "",
                s.company_id.partner_id.country_id and s.company_id.partner_id.country_id.name or "",
            )
            s.telefon = s.company_id.partner_id.phone
            s.caen = s.company_id.l10n_ro_caen_code
            s.mail = s.company_id.partner_id.email
            bank = s.company_id.partner_id.bank_ids[0]
            s.bank_account_id = bank and bank.id or None
            s.banca = bank and bank.bank_id.name or None
            s.cont = bank and bank.acc_number or None

    luna = fields.Selection(
        selection=months(),
        default=str(datetime.now().month),
        string="Luna",
        required=True,
        help="Perioada de raportare - Luna"
    )
    an = fields.Selection(
        selection=[(str(num), str(num)) for num in range(2022, ((datetime.now().year)+2))],
        default=str(datetime.now().year),
        string="An",
        required=True,
        help="Perioada de raportare - An"
    )
    tip_D300 = fields.Selection(selection=period(), string="Tip D300", required=True, default="L")
    start_date = fields.Date("Start Date")
    end_date = fields.Date("End Date")
    move_line_ids = fields.One2many("account.move.line", 'd300_id', string="Move Lines")

    def get_move_lines(self):
        move_lines_f = self.env['account.move.line'].search([
            ("company_id", "=", self.company_id.id),
            ("date", ">=", self.start_date),
            ("date", "<=", self.end_date),
            ("tax_tag_ids", "!=", False),
            ("move_id.state", "=", "posted"),
        ]).filtered(lambda x:
                    x.tax_line_id.tax_exigibility != "on_payment" or
                    x.move_id.always_tax_exigible or
                    x.move_id.tax_cash_basis_rec_id
                    )
        if self.env['account.move']._fields.get('pos_payment_ids', None):
            bonuri_moves = move_lines_f.filtered(
                lambda x: x.move_id.pos_payment_ids
                        or x.move_id.pos_refunded_invoice_ids
                        #or x.move_id.pos_order_ids
            )
            move_lines_f -= bonuri_moves
        return move_lines_f

    invoice_ids = fields.One2many("account.move", "d300_id", string="Facturi")

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
            '|','&',
                ('journal_id.l10n_ro_fiscal_receipt','=',True),
                ('journal_id.type','in', ['sale','general']),
            ('move_type', 'in', types),
            ("date", ">=", self.start_date),
            ("date", "<=", self.end_date),
            ("state", "in", ["posted"]),# "cancel")),
            "|",
            ("company_id", "=", self.company_id.id),
            ("company_id", "in", self.company_id.child_ids.ids),
        ])
        cancel_supp_inv = invoices.filtered(
            lambda i: i.move_type in ["in_invoice", "in_refund", "in_receipt"]
            and i.state == "cancel"
        )
        invoices -= cancel_supp_inv
        if self.env['account.move']._fields.get('pos_payment_ids', None):
            invoices_BF = invoices.filtered(
                lambda i: i.pos_payment_ids
                        #or i.pos_order_ids
                        or i.pos_refunded_invoice_ids
                        #or i.journal_id.l10n_ro_fiscal_receipt
                    )
            invoices -= invoices_BF
        return invoices

    @api.onchange("luna", "an", "tip_D300")
    def c1_change_date(self):
        if self.tip_D300 == 'L':
            input_dt = datetime(int(self.an), int(self.luna), 1)
            self.start_date = input_dt + relativedelta(day=1)
            self.end_date = input_dt + relativedelta(day=1, days=-1, months=1)
        if self.tip_D300 == 'T':
            if 1 <= int(self.luna) <= 3:
                luna = 3
            if 4 <= int(self.luna) <= 6:
                luna = 6
            if 7 <= int(self.luna) <= 9:
                luna = 9
            if 10 <= int(self.luna) <= 12:
                luna = 12
            input_dt = datetime(int(self.an), int(luna), 1)
            self.start_date = input_dt + relativedelta(day=1, months=-2)
            self.end_date = input_dt + relativedelta(day=1, days=-1, months=1)
        if self.tip_D300 == 'S':
            if 1 <= int(self.luna) <= 6:
                luna = 6
            if 7 <= int(self.luna) <= 12:
                luna = 12
            input_dt = datetime(int(self.an), int(luna), 1)
            self.start_date = input_dt + relativedelta(day=1, months=-5)
            self.end_date = input_dt + relativedelta(day=1, days=-1, months=1)
        if self.tip_D300 == 'A':
            input_dt = datetime(int(self.an), int(12), 1)
            self.start_date = input_dt + relativedelta(day=1, months=-11)
            self.end_date = input_dt + relativedelta(day=1, days=-1, months=1)

    pro_rata = fields.Integer(string="Pro-rata", default=0)
    bifa_cereale = fields.Boolean(compute="_compute_operations")
    bifa_mob = fields.Boolean(compute="_compute_operations")
    bifa_disp = fields.Boolean(compute="_compute_operations")
    bifa_cons = fields.Boolean(compute="_compute_operations")

    @api.depends("move_line_ids")
    def _compute_operations(self):
        for s in self:
            s.bifa_cereale = len(s.move_line_ids.filtered(lambda x: x.product_id.categ_id.anaf_code == '21')) > 0
            s.bifa_mob = len(s.move_line_ids.filtered(lambda x: x.product_id.categ_id.anaf_code == '29')) > 0
            s.bifa_disp = len(s.move_line_ids.filtered(lambda x: x.product_id.categ_id.anaf_code == '30')) > 0
            s.bifa_cons = len(s.move_line_ids.filtered(lambda x: x.product_id.categ_id.anaf_code == '31')) > 0

    solicit_ramb = fields.Boolean(string="Solicitare rambursare TVA", default=False)

    nr_evid = fields.Char(compute="get_nr_evid", store=True)

    @api.depends("tip_D300", "luna", "an", "start_date", "end_date")
    def get_nr_evid(self):
        for s in self:
            r = relativedelta(s.start_date, s.end_date)
            months = r.months + 12 * r.years + 1
            date_next = (s.end_date + relativedelta(day=25, months=months)).strftime("%d%m%y")
            types = {
                "L": "301",
                "T": "302",
                "S": "303",
                "A": "304",
            }
            nr_evid = f"10{types.get(s.tip_D300)}01{s.luna.zfill(2)}{s.an[-2:]}{date_next}0000"
            control = sum(int(x) for x in nr_evid)
            s.nr_evid = f"{nr_evid}{str(control)[-2:]}"

    totalPlata_A = fields.Integer(compute="_get_totalPlata_A", store=True)

    R1_1 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R2_1 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R3_1 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R3_1_1 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R4_1 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R5_1 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R5_2 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R5_1_1 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R5_1_2 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R6_1 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R6_2 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R7_1 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R7_2 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R7_1_1 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R7_1_2 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R8_1 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R8_2 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R9_1 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R9_2 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R10_1 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R10_2 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R11_1 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R11_2 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R12_1 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R12_2 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R12_1_1 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R12_1_2 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R12_2_1 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R12_2_2 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R12_3_1 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R12_3_2 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R13_1 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R14_1 = fields.Integer(compute="_get_totalPlata_A", store=True)

    #TODO
    R67_1 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R68_1 = fields.Integer(compute="_get_totalPlata_A", store=True)

    R15_1 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R16_1 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R16_2 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R64_1 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R64_2 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R65_1 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R65_2 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R17_1 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R17_2 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R18_1 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R18_2 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R18_1_1 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R18_1_2 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R19_1 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R19_2 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R20_1 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R20_2 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R20_1_1 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R20_1_2 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R21_1 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R21_2 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R22_1 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R22_2 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R23_1 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R23_2 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R24_1 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R24_2 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R25_1 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R25_2 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R25_1_1 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R25_1_2 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R25_2_1 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R25_2_2 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R25_3_1 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R25_3_2 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R43_2 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R44_2 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R26_1 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R26_1_1 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R27_1 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R27_2 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R28_2 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R29_2 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R30_1 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R30_2 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R31_2 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R32_2 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R33_2 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R34_2 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R35_2 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R36_2 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R37_2 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R38_2 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R39_2 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R40_2 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R41_2 = fields.Integer(compute="_get_totalPlata_A", store=True)
    R42_2 = fields.Integer(compute="_get_totalPlata_A", store=True)

    def get_balance(self, tag):
        move_lines = self.move_line_ids.filtered(lambda x: tag in x.tax_tag_ids._get_related_tax_report_expressions().mapped('formula'))
        if move_lines:
            return int(round(abs(sum(move_lines.mapped('balance')))))
        return 0

    @api.depends("move_line_ids")
    def _get_totalPlata_A(self):
        for s in self:
            s.R1_1 = s.get_balance("01 - TAX BASE")
            s.R2_1 = s.get_balance("02 - TAX BASE")
            s.R3_1 = s.get_balance("03 - TAX BASE")
            s.R3_1_1 = s.get_balance("03_1 - TAX BASE")
            s.R4_1 = s.get_balance("04 - TAX BASE")
            s.R5_1 = s.get_balance("05 - TAX BASE")
            s.R5_2 = s.get_balance("05 - VAT")
            s.R5_1_1 = s.get_balance("05_1 - TAX BASE")
            s.R5_1_2 = s.get_balance("05_1 - VAT")
            s.R6_1 = s.get_balance("06 - TAX BASE")
            s.R6_2 = s.get_balance("06 - VAT")
            s.R7_1 = s.get_balance("07 - TAX BASE")
            s.R7_2 = s.get_balance("07 - VAT")
            s.R7_1_1 = s.get_balance("07_1 - TAX BASE")
            s.R7_1_2 = s.get_balance("07_1 - VAT")
            s.R8_1 = s.get_balance("08 - TAX BASE")
            s.R8_2 = s.get_balance("08 - VAT")
            s.R9_1 = s.get_balance("09 - TAX BASE")
            s.R9_2 = s.get_balance("09 - VAT")
            s.R10_1 = s.get_balance("10 - TAX BASE")
            s.R10_2 = s.get_balance("10 - VAT")
            s.R11_1 = s.get_balance("11 - TAX BASE")
            s.R11_2 = s.get_balance("11 - VAT")
            s.R12_1_1 = s.get_balance("12_1 - TAX BASE")
            s.R12_2_1 = s.get_balance("12_2 - TAX BASE")
            s.R12_3_1 = s.get_balance("12_3 - TAX BASE")
            s.R12_1 = s.get_balance("12 - TAX BASE") + s.R12_1_1 + s.R12_2_1 + s.R12_3_1
            s.R12_1_2 = s.get_balance("12_1 - VAT")
            s.R12_2_2 = s.get_balance("12_2 - VAT")
            s.R12_3_2 = s.get_balance("12_3 - VAT")
            s.R12_2 = s.get_balance("12 - VAT") + s.R12_1_2 + s.R12_2_2 + s.R12_3_2
            s.R13_1 = s.get_balance("13 - TAX BASE")
            s.R14_1 = s.get_balance("14 - TAX BASE")
            s.R15_1 = s.get_balance("15 - TAX BASE")
            s.R16_1 = s.get_balance("16 - TAX BASE")
            s.R16_2 = s.get_balance("16 - VAT")
            s.R64_1 = s.get_balance("17 - TAX BASE")
            s.R64_2 = s.get_balance("17 - VAT")
            s.R65_1 = s.get_balance("18 - TAX BASE")
            s.R65_2 = s.get_balance("18 - VAT")
            s.R17_1 = (
                s.R1_1
                + s.R2_1
                + s.R3_1
                + s.R4_1
                + s.R5_1
                + s.R6_1
                + s.R7_1
                + s.R8_1
                + s.R9_1
                + s.R10_1
                + s.R11_1
                + s.R12_1
                + s.R13_1
                + s.R14_1
                + s.R15_1
                + s.R16_1
                + s.R64_1
                + s.R65_1
            )
            s.R17_2 = (
                s.R5_2
                + s.R6_2
                + s.R7_2
                + s.R8_2
                + s.R9_2
                + s.R10_2
                + s.R11_2
                + s.R12_2
                + s.R16_2
                + s.R64_2
                + s.R65_2
            )
            s.R18_1 = s.get_balance("20 - TAX BASE")
            s.R18_2 = s.get_balance("20 - VAT")
            s.R18_1_1 = s.get_balance("20_1 - TAX BASE")
            s.R18_1_2 = s.get_balance("20_1 - VAT")
            s.R19_1 = s.get_balance("21 - TAX BASE")
            s.R19_2 = s.get_balance("21 - VAT")
            s.R20_1 = s.get_balance("22 - TAX BASE")
            s.R20_2 = s.get_balance("22 - VAT")
            s.R20_1_1 = s.get_balance("22_1 - TAX BASE")
            s.R20_1_2 = s.get_balance("22_1 - VAT")
            s.R21_1 = s.get_balance("23 - TAX BASE")
            s.R21_2 = s.get_balance("23 - VAT")
            s.R22_1 = s.get_balance("24_1 - TAX BASE") + s.get_dvis_values(s.invoice_ids)
            s.R22_2 = s.get_balance("24_1 - VAT")
            s.R23_1 = s.get_balance("25_1 - TAX BASE")
            s.R23_2 = s.get_balance("25_1 - VAT")
            s.R24_1 = s.get_balance("26_1 - TAX BASE")
            s.R24_2 = s.get_balance("26_1 - VAT")
            s.R25_1_1 = s.get_balance("27_1 - TAX BASE")
            s.R25_2_1 = s.get_balance("27_2 - TAX BASE")
            s.R25_3_1 = s.get_balance("27_3 - TAX BASE")
            s.R25_1 = s.get_balance("27 - TAX BASE") + s.R25_1_1 + s.R25_2_1 + s.R25_3_1
            s.R25_1_2 = s.get_balance("27_1 - VAT")
            s.R25_2_2 = s.get_balance("27_2 - VAT")
            s.R25_3_2 = s.get_balance("27_3 - VAT")
            s.R25_2 = s.get_balance("27 - VAT") + s.R25_1_2 + s.R25_2_2 + s.R25_3_2
            s.R26_1 = s.get_balance("30 - TAX BASE")
            s.R26_1_1 = s.get_balance("30_1 - TAX BASE")
            s.R27_1 = (
                    s.R18_1
                    + s.R19_1
                    + s.R20_1
                    + s.R21_1
                    + s.R22_1
                    + s.R23_1
                    + s.R24_1
                    + s.R25_1
            )
            s.R27_2 = (
                    s.R18_2
                    + s.R19_2
                    + s.R20_2
                    + s.R21_2
                    + s.R22_2
                    + s.R23_2
                    + s.R24_2
                    + s.R25_2
                    + s.R43_2
                    + s.R44_2
            )
            s.R28_2 = s.R27_2
            s.R29_2 = s.get_balance("33 - VAT")
            s.R30_1 = s.get_balance("34 - TAX BASE")
            s.R30_2 = s.get_balance("34 - VAT")
            s.R31_2 = s.get_balance("35 - VAT")
            s.R32_2 = (
                    s.R28_2
                    + s.R29_2
                    + s.R30_2
                    + s.R31_2
            )
            vat = s.R32_2 - s.R17_2
            s.R33_2 = vat if vat > 0 else 0
            s.R34_2 = -1 * vat if vat < 0 else 0

            R35_2_old = 0
            R38_2_old = 0
            for record in self:
                acc_4423 = self.env["account.account"].search(
                    [("code", "=", "442300"), ("company_ids", "=", record.company_id.id)]
                )
                acc_4424 = self.env["account.account"].search(
                    [("code", "=", "442400"), ("company_ids", "=", record.company_id.id)]
                )
                if acc_4423 and acc_4424:
                    ml_lines_4423 = self.env["account.move.line"].search(
                        [
                            ("move_id.state", "=", "posted"),
                            (
                                "move_id.date",
                                ">=",
                                s.company_ids.account_opening_date,
                            ),
                            ("move_id.date", "<", datetime.now().date()),
                            ("company_ids", "=", s.company_ids.id),
                            ("account_id", "=", acc_4423.id),
                        ]
                    )
                    R35_2_old = int(round(sum(ml_lines_4423.mapped("balance"))))
                    ml_lines_4424 = s.env["account.move.line"].search(
                        [
                            ("move_id.state", "=", "posted"),
                            (
                                "move_id.date",
                                ">=",
                                s.company_id.account_opening_date,
                            ),
                            ("move_id.date", "<", datetime.now().date()),
                            ("company_id", "=", s.company_id.id),
                            ("account_id", "=", acc_4424.id),
                        ]
                    )
                    R38_2_old = int(round(sum(ml_lines_4424.mapped("balance"))))
            s.R35_2 = 0 if R35_2_old > 0 else R35_2_old
            s.R37_2 = s.R34_2 + s.R35_2 + s.R36_2
            s.R38_2 = 0 if R38_2_old > 0 else R38_2_old
            s.R40_2 = s.R33_2 + s.R38_2 + s.R39_2
            vat_result = s.R37_2 - s.R40_2
            s.R41_2 = vat_result if vat_result > 0 else 0
            s.R42_2 = -1 * vat_result if vat_result < 0 else 0
            s.R43_2 = s.get_balance("28 - VAT")
            s.R44_2 = s.get_balance("29 - VAT")
            s.R36_2 = s.get_balance("40 - VAT")
            s.R39_2 = s.get_balance("43 - VAT")

            s.totalPlata_A = (
                s.R1_1 +
                s.R2_1 +
                s.R3_1 +
                s.R3_1_1 +
                s.R4_1 +
                s.R5_1 +
                s.R5_2 +
                s.R5_1_1 +
                s.R5_1_2 +
                s.R6_1 +
                s.R6_2 +
                s.R7_1 +
                s.R7_2 +
                s.R7_1_1 +
                s.R7_1_2 +
                s.R8_1 +
                s.R8_2 +
                s.R9_1 +
                s.R9_2 +
                s.R10_1 +
                s.R10_2 +
                s.R11_1 +
                s.R11_2 +
                s.R12_1 +
                s.R12_2 +
                s.R12_1_1 +
                s.R12_1_2 +
                s.R12_2_1 +
                s.R12_2_2 +
                s.R12_3_1 +
                s.R12_3_2 +
                s.R13_1 +
                s.R14_1 +
                s.R67_1 +
                s.R68_1 +
                s.R15_1 +
                s.R16_1 +
                s.R16_2 +
                s.R64_1 +
                s.R64_2 +
                s.R65_1 +
                s.R65_2 +
                s.R17_1 +
                s.R17_2 +
                s.R18_1 +
                s.R18_2 +
                s.R18_1_1 +
                s.R18_1_2 +
                s.R19_1 +
                s.R19_2 +
                s.R20_1 +
                s.R20_2 +
                s.R20_1_1 +
                s.R20_1_2 +
                s.R21_1 +
                s.R21_2 +
                s.R22_1 +
                s.R22_2 +
                s.R23_1 +
                s.R23_2 +
                s.R24_1 +
                s.R24_2 +
                s.R25_1 +
                s.R25_2 +
                s.R25_1_1 +
                s.R25_1_2 +
                s.R25_2_1 +
                s.R25_2_2 +
                s.R25_3_1 +
                s.R25_3_2 +
                s.R43_2 +
                s.R44_2 +
                s.R26_1 +
                s.R26_1_1 +
                s.R27_1 +
                s.R27_2 +
                s.R28_2 +
                s.R29_2 +
                s.R30_1 +
                s.R30_2 +
                s.R31_2 +
                s.R32_2 +
                s.R33_2 +
                s.R34_2 +
                s.R35_2 +
                s.R36_2 +
                s.R37_2 +
                s.R38_2 +
                s.R39_2 +
                s.R40_2 +
                s.R41_2 +
                s.R42_2 +
                s.nr_facturi +
                s.baza +
                s.tva +
                s.nr_facturi_primite
            )

            #TODO
            s.R67_1 = 0
            s.R68_1 = 0

    nr_facturi = fields.Integer("Nr Facturi", compute="get_invoice_data", store=True)
    baza = fields.Integer("Baza", compute="get_invoice_data", store=True)
    tva = fields.Integer("TVA", compute="get_invoice_data", store=True)
    nr_facturi_primite = fields.Integer("Nr Facturi Primite", compute="get_invoice_data", store=True)
    baza_primite = fields.Integer("Baza Primite", compute="get_invoice_data", store=True)
    tva_primite = fields.Integer("TVA Primite", compute="get_invoice_data", store=True)
    valoare_a = fields.Integer(compute="get_invoice_data", store=True)
    valoare_a1 = fields.Integer(compute="get_invoice_data", store=True)
    tva_a = fields.Integer(compute="get_invoice_data", store=True)
    tva_a1 = fields.Integer(compute="get_invoice_data", store=True)
    valoare_b = fields.Integer(compute="get_invoice_data", store=True)
    valoare_b1 = fields.Integer(compute="get_invoice_data", store=True)
    tva_b = fields.Integer(compute="get_invoice_data", store=True)
    tva_b1 = fields.Integer(compute="get_invoice_data", store=True)
    nr_fact_emise = fields.Integer(compute="get_invoice_data", store=True)
    total_baza = fields.Integer(compute="get_invoice_data", store=True)
    total_tva = fields.Integer(compute="get_invoice_data", store=True)
    total_precedent = fields.Integer(compute="get_invoice_data", store=True)
    total_curent = fields.Integer(compute="get_invoice_data", store=True)

    @api.depends("invoice_ids")
    def get_invoice_data(self):
        for s in self:
            facturi = s.invoice_ids.filtered(lambda x: x.move_type in ["out_invoice", "out_refund"] and x.l10n_ro_correction)
            s.nr_facturi = len(facturi)
            s.baza = int(sum(facturi.mapped('amount_untaxed_signed')))
            s.tva = int(sum(facturi.mapped('amount_tax_signed')))

            facturi_primite = s.invoice_ids.filtered(lambda x: x.move_type in ["in_invoice", "in_refund"] and x.l10n_ro_correction)
            s.nr_facturi_primite = len(facturi_primite)
            s.baza_primite = int(sum(facturi_primite.mapped('amount_untaxed_signed')))
            s.tva_primite = int(sum(facturi_primite.mapped('amount_tax_signed')))

            fp = self.company_id.l10n_ro_property_vat_on_payment_position_id
            if not fp:
                fp = self.env["account.fiscal.position"].search(
                    [
                        ("company_id", "=", s.company_id.id),
                        ("name", "=", "Regim TVA la Incasare"),
                    ]
                )

            date1 = s.end_date - relativedelta(months=6)

            valoare_a = valoare_a1 = tva_a = tva_a1 = 0
            facturi_vatp = s.invoice_ids.filtered(lambda x: x.move_type in ["out_invoice", "out_refund"] and x.fiscal_position_id.id == fp.id)
            for inv in facturi_vatp:
                valoare_a += inv.amount_untaxed_signed
                tva_a += inv.amount_tax_signed
                cash_basis_moves = self.env["account.move"].search(
                    [("tax_cash_basis_origin_move_id", "=", inv.id), ("date", "<=", s.end_date), ("date", ">=", s.start_date)]
                )
                for line in cash_basis_moves.mapped("line_ids"):
                    if not line.tax_repartition_line_id:
                        continue
                    valoare_a += line.tax_base_amount
                    tva_a += line.balance
                    if inv.date > date1:
                        valoare_a1 += line.tax_base_amount
                        tva_a1 += line.balance

            s.valoare_a = valoare_a
            s.valoare_a1 = valoare_a1
            s.tva_a = tva_a
            s.tva_a1 = tva_a1

            valoare_b = valoare_b1 = tva_b = tva_b1 = 0
            sign = -1
            facturi_primite_vatp = s.invoice_ids.filtered(lambda x: x.move_type in ["out_invoice", "out_refund"] and x.fiscal_position_id.id == fp.id)
            for inv in facturi_primite_vatp:
                valoare_b += sign * inv.amount_untaxed_signed
                tva_b += sign * inv.amount_tax_signed
                cash_basis_moves = self.env["account.move"].search(
                    [("tax_cash_basis_origin_move_id", "=", inv.id), ("date", "<=", s.end_date)]
                )

                for line in cash_basis_moves.line_ids:

                    if not line.tax_repartition_line_id:
                        continue
                    valoare_b += sign * line.tax_base_amount
                    tva_b += sign * line.balance
                    if inv.date > date1:
                        valoare_b1 += sign * line.tax_base_amount
                        tva_b1 += sign * line.balance

            nond_tags_base = ["24_2 - TAX BASE", "25_2 - TAX BASE", "26_2 - TAX BASE"]
            nond_tags_tax = ["24_2 - VAT", "25_2 - VAT", "26_2 - VAT"]
            for tag in nond_tags_base:
                valoare_b += s.get_balance(tag)
            for tag in nond_tags_tax:
                tva_b += s.get_balance(tag)

            s.valoare_b = valoare_b
            s.valoare_b1 = valoare_b1
            s.tva_b = tva_b
            s.tva_b1 = tva_b1

            s.nr_fact_emise = 0
            s.total_baza = 0
            s.total_tva = 0
            s.total_precedent = 0
            s.total_curent = 0

    def get_dvis_values(self, invoice_ids):
        if 'l10n.ro.account.dvi' in self.env:
            invoices_with_dvi = invoice_ids.filtered(lambda x: x.l10n_ro_dvi_ids)
            unique_dvis_ids = invoices_with_dvi.mapped('l10n_ro_dvi_ids').ids
            unique_dvis = self.env['l10n.ro.account.dvi'].browse(unique_dvis_ids)
            return sum(unique_dvis.mapped('customs_duty_value'))
        return 0

    def rebuild_declaration(self):
        for s in self:
            s.move_line_ids.d300_id = False
            move_lines = s.get_move_lines()
            move_lines.d300_id = s.id

            s.invoice_ids.d300_id = False
            invoice_ids = s.get_invoices()
            invoice_ids.d300_id = s.id

            s.get_nr_evid()
            s._get_company_data()
            s._get_succesor_data()
            s._get_reprezentant_data()

    def export_declaration(self):
        self.ensure_one()
        objdata = self.read()[0]
        for k, v in objdata.items():
            if isinstance(v, datetime) or isinstance(v, date):
                objdata[k] = v.strftime("%H:%M:%S")
            if isinstance(v, bool):
                objdata[k] = v and '1' or '0'

        l10n_ro_decalaration_url = self.env['ir.config_parameter'].sudo().get_param('dakai_declarations_common.l10n_ro_decalaration_url')
        if not l10n_ro_decalaration_url:
            raise ValidationError(_("URL-ul pentru trimitere declaratie nu este setat."))

        response = requests.post('%s/d300_data_to_xml' % l10n_ro_decalaration_url, json=objdata, timeout=80)
        xml_name = "%s.xml" % self.name
        xml_content = response.json().get("result")

        xml_doc = etree.fromstring(xml_content.encode())
        schema_file_path = get_module_resource(
            "dakai_d300", "static/schemas", "D300.xsd"
        )
        xml_schema = etree.XMLSchema(etree.parse(open(schema_file_path)))

        is_valid = xml_schema.validate(xml_doc)

        if not is_valid:
            self.message_post(body=_("Validation Error: %s") % xml_schema.error_log.last_error)

        domain = [
            ("name", "=", xml_name),
            ("res_model", "=", "l10_romania.report.d300"),
            ("res_id", "=", self.id),
        ]
        attachments = self.env["ir.attachment"].search(domain)
        attachments.unlink()

        return self.env["ir.attachment"].create(
            {
                "name": xml_name,
                "raw": xml_content,
                "res_model": "l10_romania.report.d300",
                "res_id": self.id,
                "mimetype": "application/xml",
            }
        )
