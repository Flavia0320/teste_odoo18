from odoo import api, fields, models, Command


class DeclaratiaD394Op2(models.Model):
    _name = "report.d394.op2"
    _description = "Declaratia D394 OP2"

    name = fields.Char(compute="_compute_name", store=True)

    @api.depends('d394_id', 'luna', 'tip_op2')
    def _compute_name(self):
        for s in self:
            s.name = f"OP2_{s.tip_op2} - {s.luna}"

    d394_id = fields.Many2one('l10_romania.report.d394')
    tip_op2 = fields.Selection(
        [('i1', 'I1'), ('i2', 'I2')],
        string="Operation Type"
    )
    invoice_ids = fields.Many2many('account.move', string="OP1 Invoices")
    luna = fields.Integer(string="Luna")
    nrAMEF = fields.Integer(string="Nr de AMEF", compute="_compute_nr", store=True)
    nrBF = fields.Integer(string="Nr de bonuri fiscale", compute="_compute_nr", store=True)

    @api.depends("invoice_ids")
    def _compute_nr(self):
        for s in self:
            s.nrAMEF = len(s.invoice_ids.mapped('journal_id'))
            s.nrBF = len(s.invoice_ids)

    total = fields.Float(string="Total incasari", compute="_get_values", store=True)
    baza20 = fields.Float(string="Valoare baza impozabila pt cota 20%", compute="_get_values", store=True)
    baza19 = fields.Float(string="Valoare baza impozabila pt cota 19%", compute="_get_values", store=True)
    baza9 = fields.Float(string="Valoare baza impozabila pt cota 9%", compute="_get_values", store=True)
    baza5 = fields.Float(string="Valoare baza impozabila pt cota 5%", compute="_get_values", store=True)
    tva20 = fields.Float(string="Valoarea TVA-ului pt cota 20%", compute="_get_values", store=True)
    tva19 = fields.Float(string="Valoarea TVA-ului pt cota 19%", compute="_get_values", store=True)
    tva9 = fields.Float(string="Valoarea TVA-ului pt cota 9%", compute="_get_values", store=True)
    tva5 = fields.Float(string="Valoarea TVA-ului pt cota 5%", compute="_get_values", store=True)

    @api.depends("invoice_ids")
    def _get_values(self):
        for s in self:
            total = 0
            baza20 = baza19 = baza9 = baza5 = 0
            tva20 = tva19 = tva9 = tva5 = 0
            for i in s.invoice_ids:
                sign = 1
                if "refund" in i.move_type:
                    sign = -1
                taxes = i._prepare_invoice_aggregated_taxes()
                for tax, details in taxes['tax_details'].items():
                    if tax['tax'].amount == 5:
                        baza5 += sign * details['base_amount']
                        tva5 += sign * details['tax_amount']
                    if tax['tax'].amount == 9:
                        baza9 += sign * details['base_amount']
                        tva9 += sign * details['tax_amount']
                    if tax['tax'].amount == 19:
                        baza19 += sign * details['base_amount']
                        tva19 += sign * details['tax_amount']
                    if tax['tax'].amount == 20:
                        baza20 += sign * details['base_amount']
                        tva20 += sign * details['tax_amount']
            s.baza20 = round(baza20)
            s.tva20 = round(tva20)
            s.baza19 = round(baza19)
            s.tva19 = round(tva19)
            s.baza9 = round(baza9)
            s.tva9 = round(tva9)
            s.baza5 = round(baza5)
            s.tva5 = round(tva5)
            s.total = round(baza20) + round(baza19) + round(baza9) + round(baza5) + round(tva20) + round(tva19) + round(tva9) + round(tva5)


    @api.model
    def generate(self, d394_id):
        d394_id.op2_ids.unlink()
        op2_invoices = self.env['account.move']
        if op2_invoices._fields.get('pos_order_ids', None):
            op2_invoices |= d394_id.invoice_ids.filtered(lambda i:
                i.state == "posted" and
                ((i.move_type in ["out_receipt"] and
                i.journal_id.l10n_ro_fiscal_receipt) or
                i.pos_order_ids)
            )
        arr = {}
        for i in op2_invoices:
            month = fields.Date.from_string(i.invoice_date).month
            if not arr.get(month):
                arr[month] = []
            arr[month] += [i]
        for month, invoices in arr.items():
            self.create({
                'd394_id': d394_id.id,
                'tip_op2': 'i1',
                'luna': month,
                'invoice_ids': [Command.set([inv.id for inv in invoices])]
            })
