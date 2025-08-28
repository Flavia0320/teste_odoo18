from odoo import api, fields, models, Command

class DeclaratiaD394Lista(models.Model):
    _name = "report.d394.lista"
    _description = "Declaratia D394 Lista"

    name = fields.Char(compute="_compute_name", store=True)

    @api.depends('d394_id', 'caen', 'cota', 'operat')
    def _compute_name(self):
        for s in self:
            s.name = f"Lista_{s.caen} - {s.operat}- {s.cota}%"

    d394_id = fields.Many2one('l10_romania.report.d394')
    caen = fields.Integer(string="Activitate")
    cota = fields.Float(string="Cota de TVA")
    invoice_line_ids = fields.Many2many('account.move.line')
    operat = fields.Selection([
        ("1", "Livrare Bunuri"),
        ("2", "Prestari Servicii")
    ], string="Tipul operatiunii")
    valoare = fields.Float(string="Valoarea livrarilor/prestarilor de servicii", compute="_compute_value", store=True)
    tva = fields.Float(string="Valoare TVA", compute="_compute_value", store=True)

    @api.depends('invoice_line_ids')
    def _compute_value(self):
        for s in self:
            baza = tva = 0
            for line in s.invoice_line_ids:
                comp_curr = line.company_id.currency_id
                inv_curr = line.move_id.currency_id
                inv_date = line.move_id.invoice_date
                baza += inv_curr._convert(
                    line.price_subtotal,
                    comp_curr,
                    line.company_id,
                    inv_date,
                )
                tva += inv_curr._convert(
                    line.tax_base_amount,
                    comp_curr,
                    line.company_id,
                    inv_date,
                )
            s.valoare = round(baza)
            s.tva = round(tva)

    @api.model
    def generate(self, d394_id):
        d394_id.lista_ids.unlink()
        invoices = d394_id.invoice_ids.filtered(lambda i:
            i.move_type in ["out_invoice", "out_refund"] and
            i.payment_state in ["paid"]
        )
        companies = set(invoices.mapped("company_id"))
        caens = [
            "1071",
            "4520",
            "4730",
            "47761",
            "47762",
            "4932",
            "55101",
            "55102",
            "55103",
            "5630",
            "0812",
            "9313",
            "9602",
            "9603",
        ]
        for company in companies:
            if company.l10n_ro_caen_code.zfill(4) in caens:
                comp_inv = invoices.filtered(lambda r: r.company_id.id == company.id)
                invoice_lines = comp_inv.mapped('invoice_line_ids')
                tax_line_ids = invoice_lines.mapped('tax_line_id')
                for tax_line_id in tax_line_ids:
                    tax_invoice_lines = invoice_lines.filtered(lambda x: tax_line_id.id in x.tax_line_ids.ids)
                    cota = tax_line_id.value
                    bunuri_invoice_lines = tax_invoice_lines.filtered(lambda x: x.product_id.type in ("product", "consu"))
                    if bunuri_invoice_lines:
                        self.create({
                            'd394_id': d394_id.id,
                            'cota': cota,
                            'caen': company.l10n_ro_caen_code.zfill(4),
                            'operat': "1",
                            'invoice_line_ids': [Command.set(bunuri_invoice_lines.ids)]
                        })
                    servicii_invoice_lines = tax_invoice_lines.filtered(lambda x: x.product_id.type not in ("product", "consu"))
                    if servicii_invoice_lines:
                        self.create({
                            'd394_id': d394_id.id,
                            'cota': cota,
                            'caen': company.l10n_ro_caen_code.zfill(4),
                            'operat': "2",
                            'invoice_line_ids': [Command.set(servicii_invoice_lines.ids)]
                        })