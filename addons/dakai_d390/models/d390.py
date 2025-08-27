from odoo import api, fields, models, Command, _
from .common_decl import months
from dateutil.relativedelta import relativedelta
from datetime import datetime, date
import requests
from lxml import etree
from odoo.modules.module import get_module_resource
from odoo.exceptions import ValidationError

class DeclaratiaD390(models.Model):
    _name = "l10_romania.report.d390"
    _inherit = ['mail.thread', 'mail.activity.mixin', "l10n.ro.mixin"]
    _description = "Declaratia D390"

    name = fields.Char(compute="_compute_name", store=True)

    @api.depends('luna', 'an')
    def _compute_name(self):
        for s in self:
            s.name = f"D390 - {s.luna}.{s.an}"

    version = fields.Selection([('v3', 'Versiunea 3')], default="v3", required=True)
    company_id = fields.Many2one("res.company", required=True)

    reprezentant_id = fields.Many2one("l10_romania.report.reprezentant", string="Reprezentant Declaratie", required=True)
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
    mail = fields.Char(string="E-mail", compute="_get_company_data", store=True)

    @api.depends("company_id")
    def _get_company_data(self):
        for s in self:
            s.cui = s.company_id.vat and self.env['res.partner']._split_vat(s.company_id.vat)[1] or False
            s.den = s.company_id.name
            s.adresa = "%s %s %s %s %s" % (
                s.company_id.street or "",
                s.company_id.street2 or "",
                s.company_id.state_id and s.company_id.state_id.name or "",
                s.company_id.zip or "",
                s.company_id.country_id and s.company_id.country_id.name or "",
            )
            s.telefon = s.company_id.phone
            s.mail = s.company_id.email

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
    start_date = fields.Date("Start Date")
    end_date = fields.Date("End Date")

    @api.onchange("luna", "an")
    def c1_change_date(self):
        input_dt = datetime(int(self.an), int(self.luna), 1)
        self.start_date = input_dt + relativedelta(day=1)
        self.end_date = input_dt + relativedelta(day=1, days=-1, months=1)

    d_rec = fields.Boolean("Declaratie rectificativa")

    invoice_ids = fields.One2many("account.move", "d390_id")

    def get_invoices(self):
        types = ["out_invoice", "out_refund", "in_invoice", "in_refund", "in_receipt"]
        invoices = self.env['account.move'].search([
            ('move_type', 'in', types),
            ("date", ">=", self.start_date),
            ("date", "<=", self.end_date),
            ("state", "in", ("posted", "cancel")),
            "|",
            ("company_id", "=", self.company_id.id),
            ("company_id", "in", self.company_id.child_ids.ids),
            ("l10n_ro_partner_type", "=", "3")
        ])
        cancel_supp_inv = invoices.filtered(
            lambda i: i.move_type in ["in_invoice", "in_refund", "in_receipt"]
            and i.state == "cancel"
        )
        invoices -= cancel_supp_inv
        return invoices

    operatie_ids = fields.One2many("report.d390.operatie", "d390_id")

    picking_ids = fields.One2many("stock.picking", "d390_id")

    def get_pickings(self):
        pickings = self.env["stock.picking"].search(
            [("date_done", ">=", self.start_date), ("date_done", "<=", self.end_date), ("partner_id.l10n_ro_partner_type", "=", "3")]
        )
        # TODO
        # pickings += self.env["stock.picking"].search(
        #     [
        #         ("l10n_ro_date_transfer_new_contact", ">=", self.start_date),
        #         ("l10n_ro_date_transfer_new_contact", "<=", self.end_date),
        #     ]
        # )
        return pickings.filtered(lambda x: x._is_delivery())

    cos_ids = fields.One2many("report.d390.cos", "d390_id")

    rezumat_nrOPI = fields.Integer(string="Nr. OPI", compute="_compute_rezumat_data", store=True)
    rezumat_bazaL = fields.Integer(string="bazaL", compute="_compute_rezumat_data", store=True)
    rezumat_bazaT = fields.Integer(string="bazaT", compute="_compute_rezumat_data", store=True)
    rezumat_bazaA = fields.Integer(string="bazaA", compute="_compute_rezumat_data", store=True)
    rezumat_bazaP = fields.Integer(string="bazaP", compute="_compute_rezumat_data", store=True)
    rezumat_bazaS = fields.Integer(string="bazaS", compute="_compute_rezumat_data", store=True)
    rezumat_bazaR = fields.Integer(string="bazaR", compute="_compute_rezumat_data", store=True)
    rezumat_total_baza = fields.Integer(string="Total Baza", compute="_compute_rezumat_data", store=True)
    rezumat_nr_pag = fields.Integer(string="Nr. Pag", compute="_compute_rezumat_data", store=True)

    totalPlata_A = fields.Integer(string="Total Plata A", compute="_compute_rezumat_data", store=True)

    @api.depends("operatie_ids", "cos_ids")
    def _compute_rezumat_data(self):
        for s in self:
            s.rezumat_nrOPI = len(s.operatie_ids)
            s.rezumat_bazaL = int(sum(s.operatie_ids.filtered(lambda x: x.tip == 'L').mapped('baza')))
            s.rezumat_bazaT = int(sum(s.operatie_ids.filtered(lambda x: x.tip == 'T').mapped('baza')))
            s.rezumat_bazaA = int(sum(s.operatie_ids.filtered(lambda x: x.tip == 'A').mapped('baza')))
            s.rezumat_bazaP = int(sum(s.operatie_ids.filtered(lambda x: x.tip == 'P').mapped('baza')))
            s.rezumat_bazaS = int(sum(s.operatie_ids.filtered(lambda x: x.tip == 'S').mapped('baza')))
            s.rezumat_bazaR = int(sum(s.operatie_ids.filtered(lambda x: x.tip == 'R').mapped('baza')))
            s.rezumat_total_baza = s.rezumat_bazaL + s.rezumat_bazaT + s.rezumat_bazaA + s.rezumat_bazaP + s.rezumat_bazaS + s.rezumat_bazaR
            s.rezumat_nr_pag = s.rezumat_nrOPI + len(s.cos_ids)
            s.totalPlata_A = s.rezumat_nrOPI + s.rezumat_total_baza

    def rebuild_declaration(self):
        for s in self:
            s.invoice_ids.d390_id = False
            invoices = s.get_invoices()
            invoices.d390_id = s.id
            self.env['report.d390.operatie'].generate(self)
            s.picking_ids.d390_id = False
            picking_ids = s.get_pickings()
            picking_ids.d390_id = s.id
            self.env['report.d390.cos'].generate(self)

    def clean_read(self, obj):
        objdata = obj.read()[0]
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
        objdata['operatie_ids'] = []
        for op in self.operatie_ids:
            objdata['operatie_ids'] += [self.clean_read(op)]
        objdata['cos_ids'] = []
        for cos in self.cos_ids:
            objdata['cos_ids'] += [self.clean_read(cos)]

        l10n_ro_decalaration_url = self.env['ir.config_parameter'].sudo().get_param('dakai_declarations_common.l10n_ro_decalaration_url')
        if not l10n_ro_decalaration_url:
            raise ValidationError(_("URL-ul pentru trimitere declaratie nu este setat."))

        response = requests.post('%s/d390_data_to_xml' % l10n_ro_decalaration_url, json=objdata, timeout=80)

        xml_name = "%s.xml" % (self.name)
        xml_content = response.json().get("result")

        xml_doc = etree.fromstring(xml_content.encode())
        schema_file_path = get_module_resource(
            "dakai_d390", "static/schemas", "D390.xsd"
        )
        xml_schema = etree.XMLSchema(etree.parse(open(schema_file_path)))

        is_valid = xml_schema.validate(xml_doc)

        if not is_valid:
            self.message_post(body=_("Validation Error: %s") % xml_schema.error_log.last_error)

        domain = [
            ("name", "=", xml_name),
            ("res_model", "=", "l10_romania.report.d390"),
            ("res_id", "=", self.id),
        ]
        attachments = self.env["ir.attachment"].search(domain)
        attachments.unlink()

        return self.env["ir.attachment"].create(
            {
                "name": xml_name,
                "raw": xml_content,
                "res_model": "l10_romania.report.d390",
                "res_id": self.id,
                "mimetype": "application/xml",
            }
        )
