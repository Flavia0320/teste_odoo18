from odoo import api, fields, models, Command
from .common_decl import operation_types


class DeclaratiaD390Operatie(models.Model):
    _name = "report.d390.operatie"
    _description = "Declaratia D390 Operatie"

    name = fields.Char(compute="_compute_name", store=True)

    @api.depends('tip', 'partner_id')
    def _compute_name(self):
        for s in self:
            s.name = f"Operatie_{s.tip} - {s.partner_id.name}"

    d390_id = fields.Many2one('l10_romania.report.d390')
    tip = fields.Selection(operation_types(), string="Operation Type")

    partner_id = fields.Many2one("res.partner")
    tara = fields.Char(string="Țara operator", compute="_get_partner_data", store=True)
    codO = fields.Char(string="Cod operator", compute="_get_partner_data", store=True)
    denO = fields.Char(string="Nume operator", compute="_get_partner_data", store=True)

    @api.depends("partner_id")
    def _get_partner_data(self):
        for s in self:
            if s.partner_id:
                s.denO = s.partner_id.name.replace("&", "-").replace('"', "")
                s.tara = s.partner_id.l10n_ro_country_code
                s.codO = s.partner_id.l10n_ro_vat_number

    invoice_line_ids = fields.Many2many("account.move.line")

    baza = fields.Integer(string="Bază impozabilă", compute="_get_baza", store=True)

    @api.depends("invoice_line_ids")
    def _get_baza(self):
        for s in self:
            baza = 0
            for invoice_line in s.invoice_line_ids:
                sign = 1
                if invoice_line.move_id.move_type in [
                    "out_invoice",
                    "out_receipt",
                    "in_refund",
                ]:
                    sign = -1
                baza += int(round(sign * invoice_line.balance))
            s.baza = baza

    @api.model
    def generate(self, d390_id):
        d390_id.operatie_ids.unlink()
        partner_ids = d390_id.invoice_ids.mapped("commercial_partner_id")
        for partner in partner_ids:
            partner_invoices = d390_id.invoice_ids.filtered(lambda i: i.partner_id.id == partner.id)
            tags = {
                "01 - TAX BASE": "L",
                "03 - TAX BASE": "P",
                "20 - TAX BASE": "A",
                "22_1 - TAX BASE": "S",
            }
            for tag, tip in tags.items():
                invoice_lines = partner_invoices.mapped('invoice_line_ids').filtered(lambda x: tag in x.tax_tag_ids._get_related_tax_report_expressions().mapped('formula'))
                if invoice_lines:
                    self.create({
                        'd390_id': d390_id.id,
                        'tip': tip,
                        'partner_id': partner.id,
                        'invoice_line_ids': [Command.set(invoice_lines.ids)]
                    })
