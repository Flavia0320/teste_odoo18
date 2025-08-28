from odoo import api, fields, models


class DeclaratiaD394Facturi(models.Model):
    _name = "report.d394.facturi"
    _description = "Declaratia D394 Facturi"

    name = fields.Char(compute="_compute_name", store=True)

    @api.depends('d394_id', 'tip_factura', 'serie', 'nr')
    def _compute_name(self):
        for s in self:
            s.name = f"Facturi_{s.tip_factura} - {s.serie}{s.nr}"

    d394_id = fields.Many2one('l10_romania.report.d394')
    tip_factura = fields.Selection([
        ('1', 'Factura Stornata'),
        ('2', 'Factura Anulata '),
        ('3', 'Autofacturar'),
        ('4', 'în calitate de beneficiar în numele furnizorilor')],
        string="Tip Factura"
    )
    invoice_id = fields.Many2one('account.move')
    serie = fields.Char(string="Serie", related="invoice_id.sequence_prefix")
    nr = fields.Integer(string="Numarul facturii", related="invoice_id.sequence_number")

    baza24 = fields.Float(string="Baza impozabila aferenta facturii- cota 24%", compute="_get_values", store=True)
    baza20 = fields.Float(string="Baza impozabila aferenta facturii- cota 20%", compute="_get_values", store=True)
    baza19 = fields.Float(string="Baza impozabila aferenta facturii- cota 19%", compute="_get_values", store=True)
    baza9 = fields.Float(string="Baza impozabila aferenta facturii- cota 9%", compute="_get_values", store=True)
    baza5 = fields.Float(string="Baza impozabila aferenta facturii- cota 5%", compute="_get_values", store=True)
    tva5 = fields.Float(string="Tva-ul aferent facturii daca se aplica tva 5%", compute="_get_values", store=True)
    tva9 = fields.Float(string="Tva-ul aferent facturii daca se aplica tva 9%", compute="_get_values", store=True)
    tva19 = fields.Float(string="Tva-ul aferent facturii daca se aplica tva 19%", compute="_get_values", store=True)
    tva20 = fields.Float(string="Tva-ul aferent facturii daca se aplica tva 20%", compute="_get_values", store=True)
    tva24 = fields.Float(string="Tva-ul aferent facturii daca se aplica tva 24%", compute="_get_values", store=True)

    @api.depends("invoice_id")
    def _get_values(self):
        for s in self:
            if s.tip_factura == '3':
                baza24 = baza20 = baza19 = baza9 = baza5 = 0
                tva24 = tva20 = tva19 = tva9 = tva5 = 0
                sign = 1
                if "refund" in s.invoice_id.move_type:
                    sign = -1
                taxes = s.invoice_id._prepare_invoice_aggregated_taxes()
                for tax, details in taxes['tax_details'].items():
                    if int(tax.amount) == 5:
                        baza5 += sign * details['base_amount']
                        tva5 += sign * details['tax_amount']
                    if int(tax.amount) == 9:
                        baza9 += sign * details['base_amount']
                        tva9 += sign * details['tax_amount']
                    if int(tax.amount) == 19:
                        baza19 += sign * details['base_amount']
                        tva19 += sign * details['tax_amount']
                    if int(tax.amount) == 20:
                        baza20 += sign * details['base_amount']
                        tva20 += sign * details['tax_amount']
                    if int(tax.amount) == 24:
                        baza24 += sign * details['base_amount']
                        tva24 += sign * details['tax_amount']
                s.baza24 = round(baza24)
                s.tva24 = round(tva24)
                s.baza20 = round(baza20)
                s.tva20 = round(tva20)
                s.baza19 = round(baza19)
                s.tva19 = round(tva19)
                s.baza9 = round(baza9)
                s.tva9 = round(tva9)
                s.baza5 = round(baza5)
                s.tva5 = round(tva5)

    @api.model
    def generate(self, d394_id):
        d394_id.facturi_ids.unlink()
        invoices = d394_id.invoice_ids.filtered(lambda i:
            i.state == "cancel" or
            i.move_type in ["out_refund"] or
            i.journal_id.l10n_ro_sequence_type in ("autoinv1", "autoinv2")
        )
        for inv in invoices:
            inv_type = False
            if inv.move_type in ("out_invoice", "out_refund"):
                if inv.state == "cancel":
                    inv_type = '2'
                elif inv.journal_id.l10n_ro_sequence_type == "autoinv1":
                    inv_type = '3'
                elif inv.move_type == "out_refund":
                    inv_type = '1'
            elif inv.journal_id.l10n_ro_sequence_type == "autoinv2":
                inv_type = '4'
            if inv_type:
                self.create({
                    'd394_id': d394_id.id,
                    "tip_factura": inv_type,
                    "invoice_id": inv.id
                })
