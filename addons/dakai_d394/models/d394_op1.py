from odoo import api, fields, models, Command
from .common_decl import op_type, partner_type, inv_origin


class DeclaratiaD394Op1(models.Model):
    _name = "report.d394.op1"
    _description = "Declaratia D394 OP1"

    name = fields.Char(compute="_compute_name", store=True)

    @api.depends('d394_id', 'l10n_ro_operation_type', 'l10n_ro_invoice_origin_d394', 'cota', 'denP')
    def _compute_name(self):
        for s in self:
            s.name = f"OP1_{s.denP} - {s.l10n_ro_operation_type} - {s.l10n_ro_invoice_origin_d394} - {s.cota}%"

    d394_id = fields.Many2one('l10_romania.report.d394')
    l10n_ro_operation_type = fields.Selection(
        op_type(),
        string="Operation Type"
    )
    l10n_ro_partner_type = fields.Selection(
        partner_type(),
        string="D394 Partner Type",
    )
    cota = fields.Float(string="Cota TVA-ului")

    partner_id = fields.Many2one("res.partner", string="Partner")

    cuiP = fields.Char(string="Cod de înregistrare Partner", compute="_get_partner_data", store=True)
    denP = fields.Char(string="Denumire Partner", compute="_get_partner_data", store=True)
    taraP = fields.Char(string="Țara Partner", compute="_get_partner_data", store=True)
    locP = fields.Char(string="Localitate Partner", compute="_get_partner_data", store=True)
    judP = fields.Char(string="Judet Partner", compute="_get_partner_data", store=True)
    strP = fields.Char(string="Strada Partner", compute="_get_partner_data", store=True)
    detP = fields.Char(string="Alte detalii adresa", compute="_get_partner_data", store=True)

    @api.depends("partner_id")
    def _get_partner_data(self):
        for s in self:
            if s.partner_id:
                cui = s.partner_id.vat
                if cui and not cui[0].isalpha():
                    cui = 'RO' + cui
                s.cuiP = cui and self.env['res.partner']._split_vat(cui)[1] or False
                s.denP = s.partner_id.name
                s.taraP = s.partner_id.country_id.code
                s.locP = s.partner_id.city
                s.judP = s.partner_id.state_id.l10n_ro_order_code
                s.strP = s.partner_id.street
                s.detP = s.partner_id.street2

    l10n_ro_invoice_origin_d394 = fields.Selection(
        inv_origin(), string="Document type", default="1"
    )
    invoice_ids = fields.Many2many('account.move', string="OP1 Invoices")
    invoice_line_ids = fields.Many2many('account.move.line', string="OP1 Invoice Lines")

    nrFact = fields.Integer(string="Numar facturi", compute="_compute_nrFact", store=True)

    @api.depends("invoice_ids")
    def _compute_nrFact(self):
        for s in self:
            nr = 0
            for i in s.invoice_ids:
                taxes = i._prepare_invoice_aggregated_taxes()
                to_add = True
                for tax, details in taxes['tax_details'].items():
                    if tax['tax'].amount > s.cota:
                        to_add = False
                if to_add:
                    nr += 1
            s.nrFact = nr

    baza = fields.Float(string="Bază impozabilă", compute="_compute_baza_tva", store=True)
    tva = fields.Float(string="TVA", compute="_compute_baza_tva", store=True)

    #functie de calculare baza tva in functie de taxa cu exceptie "C". daca nu mai e nevoie de ea o scoatem
    def _update_cotas(self, line):
        sign = 1
        if "refund" in line.move_id.move_type:
            sign = -1
        if line.move_id.move_type in [
            "out_invoice",
            "out_receipt",
            "in_refund",
        ]:
            sign = -1 * sign
        cotas = {
            'base': 0,
            'vat': 0,
        }
        if self.l10n_ro_operation_type == "C":
            tax_ids = line.product_id.supplier_taxes_id.filtered(
                lambda tax: tax.amount_type == "percent"
            )
        else:
            tax_ids = line.tax_ids.filtered(
                lambda tax: tax.amount_type == "percent"
            )
        for tax in tax_ids:
            res = tax.compute_all(line.balance, handle_price_include=False)["taxes"]
            if line.move_id.l10n_ro_operation_type == 'C':
                res = list(filter(lambda v: v.get('amount') > 0 ))
            if line.move_id.l10n_ro_operation_type == 'V':
                res = list(filter(lambda v: v.get('amount') < 0 ))
            amount = sum(tax.get("amount", 0.0) for tax in res)
            cotas["base"] += sign * line.balance
            cotas["vat"] += sign * amount
        return cotas

    @api.depends("invoice_ids")
    def _compute_baza_tva(self):
        for s in self:
            baza = 0
            tva = 0
            for i in s.invoice_ids:
                sign = 1
                if "refund" in i.move_type:
                    sign = -1
                taxes = i._prepare_invoice_aggregated_taxes()
                for tax, details in taxes['tax_details'].items():
                    if tax['tax'].amount == s.cota:
                        baza += sign * details['base_amount']
                        tva += sign * details['tax_amount']
                if i.l10n_ro_operation_type in ['C', 'V']:
                    for line in i.invoice_line_ids.filtered(lambda x: x.product_id.l10n_ro_anaf_code):
                        res = line.tax_ids.compute_all(line.price_subtotal, handle_price_include=False)["taxes"][0]
                        tva += round(abs(res.get("amount", 0.0)),2)
            s.baza = round(baza)
            s.tva = round(tva)

    op11_ids = fields.One2many("report.d394.op11", "op1_id")

    def _get_tax_ids_group(self, invoices):
        res = {}
        for i in invoices:
            taxes = i._prepare_invoice_aggregated_taxes()
            for tax, detalis in taxes['tax_details'].items():
                if not res.get(tax['tax'].amount):
                    res[tax['tax'].amount] = []
                res[tax['tax'].amount] += i
        return res

    def _get_tax_amounts(self, invoice):
        taxes = invoice._prepare_invoice_aggregated_taxes()
        amount_taxes = []
        for tax, detalis in taxes['tax_details'].items():
            amount_taxes += [detalis['raw_tax_amount']]
        return amount_taxes

    @api.model
    def generate(self, d394_id):
        d394_id.op1_ids.unlink()
        op1_invoices = d394_id.invoice_ids.filtered(lambda i:
            i.state == "posted" and
            (i.move_type in ["out_invoice", "out_refund", "in_invoice", "in_refund"] or
            ((i.l10n_ro_simple_invoice or i.l10n_ro_has_vat_number) and i.move_type in ["in_receipt"])) and
            i.l10n_ro_partner_type in ["1", "2"]
        )
        arr = {}
        for i in op1_invoices:
            if not (i.l10n_ro_partner_type and i.commercial_partner_id and i.l10n_ro_operation_type and i.l10n_ro_invoice_origin_d394):
                continue
            if not arr.get(i.l10n_ro_partner_type):
                arr[i.l10n_ro_partner_type] = {}
            if not arr[i.l10n_ro_partner_type].get(i.commercial_partner_id.id):
                arr[i.l10n_ro_partner_type][i.commercial_partner_id.id] = {}
            if not arr[i.l10n_ro_partner_type][i.commercial_partner_id.id].get(i.l10n_ro_operation_type):
                arr[i.l10n_ro_partner_type][i.commercial_partner_id.id][i.l10n_ro_operation_type] = {}
            if not arr[i.l10n_ro_partner_type][i.commercial_partner_id.id][i.l10n_ro_operation_type].get(i.l10n_ro_invoice_origin_d394):
                arr[i.l10n_ro_partner_type][i.commercial_partner_id.id][i.l10n_ro_operation_type][i.l10n_ro_invoice_origin_d394] = {}
            for tax_amount in self._get_tax_amounts(i):
                if not arr[i.l10n_ro_partner_type][i.commercial_partner_id.id][i.l10n_ro_operation_type][i.l10n_ro_invoice_origin_d394].get(tax_amount):
                    arr[i.l10n_ro_partner_type][i.commercial_partner_id.id][i.l10n_ro_operation_type][i.l10n_ro_invoice_origin_d394][tax_amount] = []
                arr[i.l10n_ro_partner_type][i.commercial_partner_id.id][i.l10n_ro_operation_type][i.l10n_ro_invoice_origin_d394][tax_amount] += [i]
        for l10n_ro_partner_type, l10n_ro_partner_typed in arr.items():
            for commercial_partner_id, commercial_partner_idd in l10n_ro_partner_typed.items():
                for l10n_ro_operation_type, l10n_ro_operation_typed in commercial_partner_idd.items():
                    for l10n_ro_invoice_origin_d394, l10n_ro_invoice_origin_d394d in l10n_ro_operation_typed.items():
                        for tax_amount, invoices in l10n_ro_invoice_origin_d394d.items():
                            l10n_ro_operation_type_value = l10n_ro_operation_type
                            if tax_amount == 0:
                                if l10n_ro_operation_type == 'L':
                                    l10n_ro_operation_type_value = 'LS'
                                elif l10n_ro_operation_type in ['A', 'AI']:
                                    l10n_ro_operation_type_value = 'AS'
                            invoice_lines = []
                            for inv in invoices:
                                for il in inv.invoice_line_ids:
                                    if tax_amount == 0 and (not il.tax_ids or int(il.tax_ids[0].amount) == 0):
                                        invoice_lines += il
                                    elif il.tax_ids and int(il.tax_ids[0].amount) == tax_amount:
                                        invoice_lines += il
                            op11 = []
                            partner_found_cui = self.env['res.partner'].browse(commercial_partner_id).vat
                            if partner_found_cui and not partner_found_cui[0].isalpha():
                                partner_found_cui = 'RO' + partner_found_cui
                                partner_found_cui = self.env['res.partner']._split_vat(partner_found_cui)[1]
                            if (l10n_ro_operation_type in ['C', 'V'] and l10n_ro_partner_type == 1) or (l10n_ro_operation_type in ['N'] and  (not partner_found_cui or len(partner_found_cui) == 13 )):
                                for i in invoice_lines:
                                    sums = i.tax_ids.compute_all(i.price_subtotal)['taxes']
                                    op11.append((0, 0, {
                                        "nrFactPR": 1,
                                        "codPR": i.product_id.l10n_ro_anaf_code,
                                        "bazaPR": i.price_subtotal,
                                        "tvaPR": round(abs(sums[0].get('amount')), 2),
                                    }))
                            self.create({
                                'd394_id': d394_id.id,
                                'l10n_ro_operation_type': l10n_ro_operation_type_value,
                                'l10n_ro_partner_type': l10n_ro_partner_type,
                                'l10n_ro_invoice_origin_d394': l10n_ro_invoice_origin_d394,
                                'cota': tax_amount,
                                'partner_id': commercial_partner_id,
                                'invoice_ids': [Command.set([inv.id for inv in invoices])],
                                'invoice_line_ids': [Command.set([il.id for il in invoice_lines])],
                                'op11_ids': op11,
                            })

class DeclaratiaD394Op11(models.Model):
    _name = "report.d394.op11"
    _description = "Declaratia D394 OP11"

    nrFactPR = fields.Integer(string="Numar facturi")
    codPR = fields.Char(string="Cod produs")
    bazaPR = fields.Float(string="Baza impozitabila")
    tvaPR = fields.Float(string="TVA")
    op1_id = fields.Many2one("report.d394.op1")
