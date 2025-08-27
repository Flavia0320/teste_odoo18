from odoo import api, fields, models, Command


class DeclaratiaD394Rezumat2(models.Model):
    _name = "report.d394.rezumat2"
    _description = "Declaratia D394 Rezumat2"

    name = fields.Char(compute="_compute_name", store=True)

    @api.depends('d394_id', 'cota')
    def _compute_name(self):
        for s in self:
            s.name = f"Rezumat2 - {s.cota}%"

    d394_id = fields.Many2one('l10_romania.report.d394')
    cota = fields.Integer(string="Cota TVA-ului")
    op1_ids = fields.Many2many('report.d394.op1')

    def get_invoice_base_tva(self, invoices, cota):
        baza = 0
        tva = 0
        for i in invoices:
            sign = 1
            if "refund" in i.move_type:
                sign = -1
            taxes = i._prepare_invoice_aggregated_taxes()
            for tax, details in taxes['tax_details'].items():
                if tax['tax'].amount == cota:
                    baza += sign * details['base_amount']
                    tva += sign * details['tax_amount']
        return baza, tva

    bazaFSLcod = fields.Integer(string="Valoarea bazei impozabile aferente livrarilor", compute="_computeFSLcod", store=True)
    TVAFSLcod = fields.Integer(string="Valoarea TVA-ului aferent livrarilor", compute="_computeFSLcod", store=True)

    @api.depends('d394_id', 'd394_id.invoice_ids')
    def _computeFSLcod(self):
        for s in self:
            invoices = s.d394_id.invoice_ids
            out_receipts_slcod = invoices.filtered(lambda i:
                i.state == "posted" and
                i.line_ids.mapped("tax_ids") and
                i.move_type in ["out_receipt"] and
                i.l10n_ro_simple_invoice and
                i.l10n_ro_has_vat_number and
                i.l10n_ro_partner_type in ["1", "2"]
            )
            baza, tva = self.get_invoice_base_tva(out_receipts_slcod, s.cota)
            s.bazaFSLcod = int(round(baza))
            s.TVAFSLcod = int(round(tva))

    bazaFSL = fields.Integer(string="bazaFSL", compute="_computeFSL", store=True)
    TVAFSL = fields.Integer(string="TVAFSL", compute="_computeFSL", store=True)

    @api.depends('d394_id', 'd394_id.invoice_ids')
    def _computeFSL(self):
        for s in self:
            invoices = s.d394_id.invoice_ids
            out_receipts_sl = invoices.filtered(lambda i:
                i.state == "posted" and
                i.line_ids.mapped("tax_ids") and
                i.move_type in ["out_receipt"] and
                i.l10n_ro_simple_invoice and
                not i.l10n_ro_has_vat_number and
                i.l10n_ro_partner_type in ["1", "2"]
            )
            baza, tva = self.get_invoice_base_tva(out_receipts_sl, s.cota)
            s.bazaFSL = int(round(baza))
            s.TVAFSL = int(round(tva))

    bazaFSA = fields.Integer(string="bazaFSA", compute="_computeFSA", store=True)
    TVAFSA = fields.Integer(string="TVAFSA", compute="_computeFSA", store=True)

    @api.depends('d394_id', 'd394_id.invoice_ids')
    def _computeFSA(self):
        for s in self:
            invoices = s.d394_id.invoice_ids
            in_receipts_fsa = invoices.filtered(lambda i:
                i.state == "posted" and
                i.line_ids.mapped("tax_ids") and
                i.move_type in ["in_receipt"] and
                i.l10n_ro_simple_invoice and
                i.l10n_ro_has_vat_number and
                i.l10n_ro_partner_type in ["1", "2"]
            )
            baza, tva = self.get_invoice_base_tva(in_receipts_fsa, s.cota)
            s.bazaFSA = int(round(baza))
            s.TVAFSA = int(round(tva))

    bazaFSAI = fields.Integer(string="bazaFSAI", compute="_computeFSAI", store=True)
    TVAFSAI = fields.Integer(string="TVAFSAI", compute="_computeFSAI", store=True)

    @api.depends('d394_id', 'd394_id.invoice_ids')
    def _computeFSAI(self):
        for s in self:
            fp = s.d394_id.company_id.l10n_ro_property_vat_on_payment_position_id
            if not fp:
                fp = self.env["account.fiscal.position"].search(
                    [
                        ("company_id", "=", s.d394_id.company_id.id),
                        ("name", "=", "Regim TVA la Incasare"),
                    ]
                )
            invoices = s.d394_id.invoice_ids
            in_receipts_fsai = invoices.filtered(lambda i:
                i.state == "posted" and
                i.line_ids.mapped("tax_ids") and
                i.move_type in ["in_receipt"] and
                i.l10n_ro_simple_invoice and
                i.l10n_ro_has_vat_number and
                i.l10n_ro_partner_type in ["1", "2"] and
                i.fiscal_position_id == fp
            )
            baza, tva = self.get_invoice_base_tva(in_receipts_fsai, s.cota)
            s.bazaFSAI = int(round(baza))
            s.TVAFSAI = int(round(tva))

    bazaBFAI = fields.Integer(string="bazaBFAI", compute="_computeBFAI", store=True)
    TVABFAI = fields.Integer(string="TVABFAI", compute="_computeBFAI", store=True)

    @api.depends('d394_id', 'd394_id.invoice_ids')
    def _computeBFAI(self):
        for s in self:
            fp = s.d394_id.company_id.l10n_ro_property_vat_on_payment_position_id
            if not fp:
                fp = self.env["account.fiscal.position"].search(
                    [
                        ("company_id", "=", s.d394_id.company_id.id),
                        ("name", "=", "Regim TVA la Incasare"),
                    ]
                )
            invoices = s.d394_id.invoice_ids
            in_receipts_bfai = invoices.filtered(lambda i:
                i.state == "posted" and
                i.line_ids.mapped("tax_ids") and
                i.move_type in ["in_receipt"] and
                not i.l10n_ro_simple_invoice and
                i.l10n_ro_has_vat_number and
                i.l10n_ro_partner_type in ["1", "2"] and
                i.fiscal_position_id == fp
            )
            baza, tva = self.get_invoice_base_tva(in_receipts_bfai, s.cota)
            s.bazaBFAI = int(round(baza))
            s.TVABFAI = int(round(tva))

    nrFacturiL = fields.Integer(string="nrFacturiL", compute="_computeL", store=True)
    bazaL = fields.Integer(string="bazaL", compute="_computeL", store=True)
    tvaL = fields.Integer(string="tvaL", compute="_computeL", store=True)

    @api.depends('op1_ids')
    def _computeL(self):
        for s in self:
            op1L_ids = s.op1_ids.filtered(lambda x: x.l10n_ro_operation_type == 'L')
            s.nrFacturiL = int(round(sum(op1L_ids.mapped('nrFact'))))
            s.bazaL = int(round(sum(op1L_ids.mapped('baza'))))
            s.tvaL = int(round(sum(op1L_ids.mapped('tva'))))

    nrFacturiA = fields.Integer(string="nrFacturiA", compute="_computeA", store=True)
    bazaA = fields.Integer(string="bazaA", compute="_computeA", store=True)
    tvaA = fields.Integer(string="tvaA", compute="_computeA", store=True)

    @api.depends('op1_ids')
    def _computeA(self):
        for s in self:
            op1A_ids = s.op1_ids.filtered(lambda x: x.l10n_ro_operation_type in ['A','C'])
            s.nrFacturiA = int(round(sum(op1A_ids.mapped('nrFact'))))
            s.bazaA = int(round(sum(op1A_ids.mapped('baza'))))
            s.tvaA = int(round(sum(op1A_ids.mapped('tva'))))

    nrFacturiAI = fields.Integer(string="nrFacturiAI", compute="_computeAI", store=True)
    bazaAI = fields.Integer(string="bazaAI", compute="_computeAI", store=True)
    tvaAI = fields.Integer(string="tvaAI", compute="_computeAI", store=True)

    @api.depends('op1_ids')
    def _computeAI(self):
        for s in self:
            op1AI_ids = s.op1_ids.filtered(lambda x: x.l10n_ro_operation_type == 'AI')
            s.nrFacturiAI = int(round(sum(op1AI_ids.mapped('nrFact'))))
            s.bazaAI = int(round(sum(op1AI_ids.mapped('baza'))))
            s.tvaAI = int(round(sum(op1AI_ids.mapped('tva'))))

    baza_incasari_i1 = fields.Integer(string="baza_incasari_i1", compute="_computeI1", store=True)
    tva_incasari_i1 = fields.Integer(string="tva_incasari_i1", compute="_computeI1", store=True)

    @api.depends('d394_id', 'd394_id.op2_ids')
    def _computeI1(self):
        for s in self:
            baza_incasari_i1 = tva_incasari_i1 = 0
            if s.cota in [5,9,19,20]:
                op2_i1_ids = s.d394_id.op2_ids.filtered(lambda x: x.tip_op2 == 'i1')
                baza_incasari_i1 = sum(op2_i1_ids.mapped('baza%s' % s.cota))
                tva_incasari_i1 = sum(op2_i1_ids.mapped('tva%s' % s.cota))
            s.baza_incasari_i1 = int(round(baza_incasari_i1))
            s.tva_incasari_i1 = int(round(tva_incasari_i1))

    baza_incasari_i2 = fields.Integer(string="baza_incasari_i2", compute="_computeI2", store=True)
    tva_incasari_i2 = fields.Integer(string="tva_incasari_i2", compute="_computeI2", store=True)

    @api.depends('d394_id', 'd394_id.op2_ids')
    def _computeI2(self):
        for s in self:
            baza_incasari_i2 = tva_incasari_i2 = 0
            if s.cota in [5, 9, 19, 20]:
                op2_i2_ids = s.d394_id.op2_ids.filtered(lambda x: x.tip_op2 == 'i2')
                baza_incasari_i2 = sum(op2_i2_ids.mapped('baza%s' % s.cota))
                tva_incasari_i2 = sum(op2_i2_ids.mapped('tva%s' % s.cota))
            s.baza_incasari_i2 = int(round(baza_incasari_i2))
            s.tva_incasari_i2 = int(round(tva_incasari_i2))

    bazaL_PF = fields.Integer(string="bazaL_PF", compute="_computeL_PF", store=True)
    tvaL_PF = fields.Integer(string="tvaL_PF", compute="_computeL_PF", store=True)

    @api.depends('op1_ids')
    def _computeL_PF(self):
        for s in self:
            s.bazaL_PF = 0
            s.tvaL_PF = 0

    @api.model
    def generate(self, d394_id):
        d394_id.rezumat2_ids.unlink()
        cotas = [5, 9, 19, 20, 24]
        for cota in cotas:
            cota_op1 = d394_id.op1_ids.filtered(lambda i: i.cota == cota)
            self.env['report.d394.rezumat2'].create({
                'd394_id': d394_id.id,
                'cota': cota,
                'op1_ids': [Command.set(cota_op1.ids)]
            })
