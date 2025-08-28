from odoo import api, fields, models, Command


class DeclaratiaD394Rezumat2(models.Model):
    _name = "report.d394.rezumat2"
    _description = "Declaratia D394 Rezumat2"

    name = fields.Char(compute="_compute_name", store=True)

    @api.depends('d394_id', 'cota')
    def _compute_name(self):
        for s in self:
            s.name = f"Rezumat2 - {int(s.cota)}%"

    d394_id = fields.Many2one('l10_romania.report.d394')
    cota = fields.Float(string="Cota TVA-ului")
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
                if int(tax.amount) == int(cota):
                    baza += sign * details['base_amount']
                    tva += sign * details['tax_amount']
        return baza, tva

    bazaFSLcod = fields.Float(string="Valoarea bazei impozabile aferente livrarilor", compute="_computeFSLcod", store=True)
    TVAFSLcod = fields.Float(string="Valoarea TVA-ului aferent livrarilor", compute="_computeFSLcod", store=True)

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
            s.bazaFSLcod = round(baza)
            s.TVAFSLcod = round(tva)

    bazaFSL = fields.Float(string="bazaFSL", compute="_computeFSL", store=True)
    TVAFSL = fields.Float(string="TVAFSL", compute="_computeFSL", store=True)

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
            s.bazaFSL = round(baza)
            s.TVAFSL = round(tva)

    bazaFSA = fields.Float(string="bazaFSA", compute="_computeFSA", store=True)
    TVAFSA = fields.Float(string="TVAFSA", compute="_computeFSA", store=True)

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
            s.bazaFSA = round(baza)
            s.TVAFSA = round(tva)

    bazaFSAI = fields.Float(string="bazaFSAI", compute="_computeFSAI", store=True)
    TVAFSAI = fields.Float(string="TVAFSAI", compute="_computeFSAI", store=True)

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
            s.bazaFSAI = round(baza)
            s.TVAFSAI = round(tva)

    bazaBFAI = fields.Float(string="bazaBFAI", compute="_computeBFAI", store=True)
    TVABFAI = fields.Float(string="TVABFAI", compute="_computeBFAI", store=True)

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
            s.bazaBFAI = round(baza)
            s.TVABFAI = round(tva)

    nrFacturiL = fields.Integer(string="nrFacturiL", compute="_computeL", store=True)
    bazaL = fields.Float(string="bazaL", compute="_computeL", store=True)
    tvaL = fields.Float(string="tvaL", compute="_computeL", store=True)

    @api.depends('op1_ids')
    def _computeL(self):
        for s in self:
            op1L_ids = s.op1_ids.filtered(lambda x: x.l10n_ro_operation_type == 'L')
            s.nrFacturiL = int(round(sum(op1L_ids.mapped('nrFact'))))
            s.bazaL = round(sum(op1L_ids.mapped('baza')))
            s.tvaL = round(sum(op1L_ids.mapped('tva')))

    nrFacturiA = fields.Integer(string="nrFacturiA", compute="_computeA", store=True)
    bazaA = fields.Float(string="bazaA", compute="_computeA", store=True)
    tvaA = fields.Float(string="tvaA", compute="_computeA", store=True)

    @api.depends('op1_ids')
    def _computeA(self):
        for s in self:
            op1A_ids = s.op1_ids.filtered(lambda x: x.l10n_ro_operation_type in ['A','C'])
            s.nrFacturiA = int(round(sum(op1A_ids.mapped('nrFact'))))
            s.bazaA = round(sum(op1A_ids.mapped('baza')))
            s.tvaA = round(sum(op1A_ids.mapped('tva')))

    nrFacturiAI = fields.Integer(string="nrFacturiAI", compute="_computeAI", store=True)
    bazaAI = fields.Float(string="bazaAI", compute="_computeAI", store=True)
    tvaAI = fields.Float(string="tvaAI", compute="_computeAI", store=True)

    @api.depends('op1_ids')
    def _computeAI(self):
        for s in self:
            op1AI_ids = s.op1_ids.filtered(lambda x: x.l10n_ro_operation_type == 'AI')
            s.nrFacturiAI = int(round(sum(op1AI_ids.mapped('nrFact'))))
            s.bazaAI = round(sum(op1AI_ids.mapped('baza')))
            s.tvaAI = round(sum(op1AI_ids.mapped('tva')))

    baza_incasari_i1 = fields.Float(string="baza_incasari_i1", compute="_computeI1", store=True)
    tva_incasari_i1 = fields.Float(string="tva_incasari_i1", compute="_computeI1", store=True)

    @api.depends('d394_id', 'd394_id.op2_ids')
    def _computeI1(self):
        for s in self:
            baza_incasari_i1 = tva_incasari_i1 = 0
            if s.cota in [5,9,19,20]:
                op2_i1_ids = s.d394_id.op2_ids.filtered(lambda x: x.tip_op2 == 'i1')
                baza_incasari_i1 = sum(op2_i1_ids.mapped('baza%s' % int(s.cota)))
                tva_incasari_i1 = sum(op2_i1_ids.mapped('tva%s' % int(s.cota)))
            s.baza_incasari_i1 = round(baza_incasari_i1)
            s.tva_incasari_i1 = round(tva_incasari_i1)

    baza_incasari_i2 = fields.Float(string="baza_incasari_i2", compute="_computeI2", store=True)
    tva_incasari_i2 = fields.Float(string="tva_incasari_i2", compute="_computeI2", store=True)

    @api.depends('d394_id', 'd394_id.op2_ids')
    def _computeI2(self):
        for s in self:
            baza_incasari_i2 = tva_incasari_i2 = 0
            if int(s.cota) in [5, 9, 19, 20]:
                op2_i2_ids = s.d394_id.op2_ids.filtered(lambda x: x.tip_op2 == 'i2')
                baza_incasari_i2 = sum(op2_i2_ids.mapped('baza%s' % int(s.cota)))
                tva_incasari_i2 = sum(op2_i2_ids.mapped('tva%s' % int(s.cota)))
            s.baza_incasari_i2 = round(baza_incasari_i2)
            s.tva_incasari_i2 = round(tva_incasari_i2)

    bazaL_PF = fields.Float(string="bazaL_PF", compute="_computeL_PF", store=True)
    tvaL_PF = fields.Float(string="tvaL_PF", compute="_computeL_PF", store=True)

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
