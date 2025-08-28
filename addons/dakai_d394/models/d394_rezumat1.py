from odoo import api, fields, models, Command
from .common_decl import partner_type, inv_origin


class DeclaratiaD394Rezumat1(models.Model):
    _name = "report.d394.rezumat1"
    _description = "Declaratia D394 Rezumat1"

    name = fields.Char(compute="_compute_name", store=True)

    @api.depends('d394_id', 'l10n_ro_invoice_origin_d394', 'cota', 'l10n_ro_partner_type')
    def _compute_name(self):
        for s in self:
            s.name = f"Rezumat1_{s.l10n_ro_partner_type} - {s.l10n_ro_invoice_origin_d394} - {s.cota}%"

    d394_id = fields.Many2one('l10_romania.report.d394')
    op1_ids = fields.Many2many('report.d394.op1')

    l10n_ro_partner_type = fields.Selection(
        partner_type(),
        string="D394 Partner Type",
        store=True,
    )
    l10n_ro_invoice_origin_d394 = fields.Selection(
        inv_origin(), string="document_N", default="1"
    )

    cota = fields.Integer(string="Cota TVA-ului")

    facturiL = fields.Integer(string="facturiL", compute="_computeL")
    bazaL = fields.Float(string="bazaL", compute="_computeL")
    tvaL = fields.Float(string="tvaL", compute="_computeL")

    def _computeL(self):
        for s in self:
            op1L_ids = s.op1_ids.filtered(lambda x: x.l10n_ro_operation_type == 'L')
            s.facturiL = sum(op1L_ids.mapped('nrFact'))
            s.bazaL = sum(op1L_ids.mapped('baza'))
            s.tvaL = sum(op1L_ids.mapped('tva'))


    facturiLS = fields.Integer(string="facturiLS", compute="_computeLS")
    bazaLS = fields.Float(string="bazaLS", compute="_computeLS")

    def _computeLS(self):
        for s in self:
            op1LS_ids = s.op1_ids.filtered(lambda x: x.l10n_ro_operation_type == 'LS')
            s.facturiLS = sum(op1LS_ids.mapped('nrFact'))
            s.bazaLS = sum(op1LS_ids.mapped('baza'))

    facturiA = fields.Integer(string="facturiA", compute="_computeA")
    bazaA = fields.Float(string="bazaA", compute="_computeA")
    tvaA = fields.Float(string="tvaA", compute="_computeA")

    def _computeA(self):
        for s in self:
            op1A_ids = s.op1_ids.filtered(lambda x: x.l10n_ro_operation_type == 'A')
            s.facturiA = sum(op1A_ids.mapped('nrFact'))
            s.bazaA = sum(op1A_ids.mapped('baza'))
            s.tvaA = sum(op1A_ids.mapped('tva'))

    facturiAI = fields.Integer(string="facturiAI", compute="_computeAI")
    bazaAI = fields.Float(string="bazaAI", compute="_computeAI")
    tvaAI = fields.Float(string="tvaAI", compute="_computeAI")

    def _computeAI(self):
        for s in self:
            op1AI_ids = s.op1_ids.filtered(lambda x: x.l10n_ro_operation_type == 'AI')
            s.facturiAI = sum(op1AI_ids.mapped('nrFact'))
            s.bazaAI = sum(op1AI_ids.mapped('baza'))
            s.tvaAI = sum(op1AI_ids.mapped('tva'))

    facturiAS = fields.Integer(string="facturiAS", compute="_computeAS")
    bazaAS = fields.Float(string="bazaAS", compute="_computeAS")

    def _computeAS(self):
        for s in self:
            op1AS_ids = s.op1_ids.filtered(lambda x: x.l10n_ro_operation_type == 'AS')
            s.facturiAS = sum(op1AS_ids.mapped('nrFact'))
            s.bazaAS = sum(op1AS_ids.mapped('baza'))

    facturiV = fields.Integer(string="facturiV", compute="_computeV")
    bazaV = fields.Float(string="bazaV", compute="_computeV")

    def _computeV(self):
        for s in self:
            op1V_ids = s.op1_ids.filtered(lambda x: x.l10n_ro_operation_type == 'V')
            s.facturiV = sum(op1V_ids.mapped('nrFact'))
            s.bazaV = sum(op1V_ids.mapped('baza'))

    facturiC = fields.Integer(string="facturiC", compute="_computeC")
    bazaC = fields.Float(string="bazaC", compute="_computeC")
    tvaC = fields.Float(string="tvaC", compute="_computeC")

    def _computeC(self):
        for s in self:
            op1C_ids = s.op1_ids.filtered(lambda x: x.l10n_ro_operation_type == 'C')
            s.facturiC = sum(op1C_ids.mapped('nrFact'))
            s.bazaC = sum(op1C_ids.mapped('baza'))
            s.tvaC = sum(op1C_ids.mapped('tva'))

    facturiN = fields.Integer(string="facturiN", compute="_computeN")
    bazaN = fields.Float(string="bazaN", compute="_computeN")

    def _computeN(self):
        for s in self:
            op1N_ids = s.op1_ids.filtered(lambda x: x.l10n_ro_operation_type == 'N')
            s.facturiN = sum(op1N_ids.mapped('nrFact'))
            s.bazaN = sum(op1N_ids.mapped('baza'))

    rezumat1_detaliu_ids = fields.One2many("report.d394.rezumat1.detaliu", "rezumat1_id")

    @api.model
    def generate(self, d394_id):
        d394_id.rezumat1_ids.unlink()
        #op1_ids = d394_id.op1_ids
        arr = {}
        for i in d394_id.op1_ids: #op1_ids:
            if not arr.get(i.l10n_ro_partner_type):
                arr[i.l10n_ro_partner_type] = {}
            if not arr[i.l10n_ro_partner_type].get(i.cota):
                arr[i.l10n_ro_partner_type][i.cota] = {}
            if not arr[i.l10n_ro_partner_type][i.cota].get(i.l10n_ro_invoice_origin_d394):
                arr[i.l10n_ro_partner_type][i.cota][i.l10n_ro_invoice_origin_d394] = []
            arr[i.l10n_ro_partner_type][i.cota][i.l10n_ro_invoice_origin_d394].append(i)
        for l10n_ro_partner_type, l10n_ro_partner_typed in arr.items():
            for cota, cotad in l10n_ro_partner_typed.items():
                for l10n_ro_invoice_origin_d394, op1_ids in cotad.items():
                    ops = self.env[op1_ids[0]._name]
                    if len(op1_ids) >= 1:
                        for op in op1_ids:
                            cui = op[0]['cuiP']
                            if (op[0]['l10n_ro_operation_type'] in ['C', 'V'] and op[0]['l10n_ro_partner_type'] == '1') or (op[0]['l10n_ro_operation_type'] in ['N'] and (not cui or len(cui) == 13)):
                                ops |= op
                    Ctype = ops
                    details = []
                    if Ctype:
                        inv_lines_c = Ctype.mapped("invoice_ids.invoice_line_ids").filtered(lambda li: li.product_id.l10n_ro_anaf_code)
                        for tip_p in inv_lines_c.mapped("product_id"):
                            line_p = inv_lines_c.filtered(lambda x: x.product_id==tip_p)
                            linev = line_p.filtered(lambda x: x.move_type in ['out_invoice','out_refund'])
                            linec = line_p.filtered(lambda x: x.move_type in ['in_invoice','in_refund'] and x.partner_id.l10n_ro_partner_type == '1')
                            linen = line_p.filtered(lambda x: x.move_type in ['in_invoice','in_refund'] and x.partner_id.l10n_ro_partner_type == '2')
                            V = linev.mapped("move_id")
                            C = linec.mapped("move_id")
                            N = linen.mapped("move_id")
                            details = [(0, 0, {
                                'bun': tip_p.l10n_ro_anaf_code,
                                'nrLivV': len(V),
                                'bazaLivV': sum(linev.mapped("price_subtotal")),
                                'nrAchizC': len(C),
                                'bazaAchizC': sum(linec.mapped("price_subtotal")),
                                'tvaAchizC': sum(
                                        [
                                            round(
                                                abs(i.tax_ids.compute_all(i.price_subtotal)['taxes'][0].get('amount'))
                                                ,2)
                                            for i in linec
                                        ]
                                ),
                                'nrN': len(N),
                                'valN': sum(linen.mapped("price_total")),
                            })]
                    self.create({
                        'd394_id': d394_id.id,
                        'l10n_ro_partner_type': l10n_ro_partner_type,
                        'l10n_ro_invoice_origin_d394': l10n_ro_invoice_origin_d394,
                        'cota': cota,
                        'op1_ids': [Command.set([inv.id for inv in op1_ids])],
                        'rezumat1_detaliu_ids':details,
                    })



class DeclaratiaD394Rezumat1Detaliu(models.Model):
    _name = "report.d394.rezumat1.detaliu"
    _description = "Declaratia D394 Rezumat1 Detaliu"

    rezumat1_id = fields.Many2one('report.d394.rezumat1')
    bun = fields.Integer(string="Tipul bunurilor achizitionate/livrate")
    nrLivV = fields.Integer(string="Nr facturi aferente livrarilor")
    bazaLivV = fields.Float(string="Valoarea totala a bazei impozabile aferenta livrarilor")
    nrAchizC = fields.Integer(string="Nr facturi aferente achizitiilor")
    bazaAchizC = fields.Float(string="Valoarea totala a bazei impozabile aferenta achizitiilor")
    tvaAchizC = fields.Float(string="Valoarea totala a TVA aferenta achizitiilor")
    nrN = fields.Integer(string="Numar documente achiziție")
    valN = fields.Float(string="Valoare achiziție")
