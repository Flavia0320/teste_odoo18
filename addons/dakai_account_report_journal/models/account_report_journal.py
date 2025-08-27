from odoo import api, fields, models, Command, _
import xlwt
from io import BytesIO
from dateutil.relativedelta import relativedelta

class AccountReportJournal(models.Model):
    _name = "account.report.journal"
    _inherit = ['mail.thread', 'mail.activity.mixin', "l10n.ro.mixin"]
    _description = "Account Report Journal"

    name = fields.Char(compute="_compute_name", store=True)

    @api.depends('type', 'start_date', 'end_date')
    def _compute_name(self):
        for s in self:
            if s.type == 'purchase':
                type = 'Achizitii'
            else:
                type = 'Vanzari'
            s.name = f"Raport_Jurnal_{type}-{s.start_date}-{s.end_date}"

    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company)

    type = fields.Selection(
        selection=[
            ("purchase", "Achizitii = In invoices"),
            ("sale", "Vanzari = Out invoices"),
        ],
        string="Journal type",
        default="sale",
        required=True,
    )
    start_date = fields.Date("Start Date")
    end_date = fields.Date("End Date")

    @api.onchange('start_date')
    def _set_date_end(self):
        if self.start_date:
            self.end_date = self.start_date + relativedelta(day=1, days=-1, months=1)

    invoice_ids = fields.Many2many("account.move", string="Facturi")

    #Invoice/Bill Values
    report_total_invoice_total = fields.Float(string="Total Document", compute="_get_line_values", store=True)
    report_total_total_base = fields.Float(string="Taxabile - Total Baza", compute="_get_line_values", store=True)
    report_total_total_vat = fields.Float(string="Taxabile - Total TVA", compute="_get_line_values", store=True)
    report_total_base_19 = fields.Float(string="Taxabile - Baza 19%", compute="_get_line_values", store=True)
    report_total_tva_19 = fields.Float(string="Taxabile - TVA 19%", compute="_get_line_values", store=True)
    report_total_base_9 = fields.Float(string="Taxabile - Baza 9%", compute="_get_line_values", store=True)
    report_total_tva_9 = fields.Float(string="Taxabile - TVA 9%", compute="_get_line_values", store=True)
    report_total_base_5 = fields.Float(string="Taxabile - Baza 5%", compute="_get_line_values", store=True)
    report_total_tva_5 = fields.Float(string="Taxabile - TVA 5%", compute="_get_line_values", store=True)
    report_total_base_0 = fields.Float(string="Baza Regim Special", compute="_get_line_values", store=True)
    report_total_base_invers_tax = fields.Float(string="Baza Taxare Inversa", compute="_get_line_values", store=True)
    report_total_intracom_base_deduction = fields.Float(string="Intracom. - Cu Deducere Baza", compute="_get_line_values", store=True)
    report_total_intracom_tva_deduction = fields.Float(string="Intracom. - Cu Deducere TVA", compute="_get_line_values", store=True)
    report_total_intracom_base_nondeduction = fields.Float(string="Intracom. - Fara Deducere Baza", compute="_get_line_values", store=True)
    report_total_intracom_tva_nondeduction = fields.Float(string="Intracom. - Fara Deducere TVA", compute="_get_line_values", store=True)
    report_total_intracom_scutit_a_d = fields.Float(string="Intracom. - Scutit art.143 al.2 lit.a+d", compute="_get_line_values", store=True)
    report_total_intracom_scutit_b_c = fields.Float(string="Intracom. - Scutit art.143 al.2 lit.b+c", compute="_get_line_values", store=True)
    report_total_intracom_scutit_other = fields.Float(string="Intracom. - Scutit Altele", compute="_get_line_values", store=True)
    report_total_intracom_base_invers_tax = fields.Float(string="Intracom. - Baza Taxare Inversa", compute="_get_line_values", store=True)
    report_total_intracom_tva_invers_tax = fields.Float(string="Intracom. - TVA Taxare Inversa", compute="_get_line_values", store=True)

    @api.depends('account_report_journal_line_ids')
    def _get_line_values(self):
        for s in self:
            s.report_total_invoice_total = sum(s.account_report_journal_line_ids.mapped('invoice_total'))
            s.report_total_total_base = sum(s.account_report_journal_line_ids.mapped('total_base'))
            s.report_total_total_vat = sum(s.account_report_journal_line_ids.mapped('total_vat'))
            s.report_total_base_19 = sum(s.account_report_journal_line_ids.mapped('base_19'))
            s.report_total_tva_19 = sum(s.account_report_journal_line_ids.mapped('tva_19'))
            s.report_total_base_9 = sum(s.account_report_journal_line_ids.mapped('base_9'))
            s.report_total_tva_9 = sum(s.account_report_journal_line_ids.mapped('tva_9'))
            s.report_total_base_5 = sum(s.account_report_journal_line_ids.mapped('base_5'))
            s.report_total_tva_5 = sum(s.account_report_journal_line_ids.mapped('tva_5'))
            s.report_total_base_0 = sum(s.account_report_journal_line_ids.mapped('base_0'))
            s.report_total_base_invers_tax = sum(s.account_report_journal_line_ids.mapped('base_invers_tax'))
            s.report_total_intracom_base_deduction = sum(s.account_report_journal_line_ids.mapped('intracom_base_deduction'))
            s.report_total_intracom_tva_deduction = sum(s.account_report_journal_line_ids.mapped('intracom_tva_deduction'))
            s.report_total_intracom_base_nondeduction = sum(s.account_report_journal_line_ids.mapped('intracom_base_nondeduction'))
            s.report_total_intracom_tva_nondeduction = sum(s.account_report_journal_line_ids.mapped('intracom_tva_nondeduction'))
            s.report_total_intracom_scutit_a_d = sum(s.account_report_journal_line_ids.mapped('intracom_scutit_a_d'))
            s.report_total_intracom_scutit_b_c = sum(s.account_report_journal_line_ids.mapped('intracom_scutit_b_c'))
            s.report_total_intracom_scutit_other = sum(s.account_report_journal_line_ids.mapped('intracom_scutit_other'))
            s.report_total_intracom_base_invers_tax = sum(s.account_report_journal_line_ids.mapped('intracom_base_invers_tax'))
            s.report_total_intracom_tva_invers_tax = sum(s.account_report_journal_line_ids.mapped('intracom_tva_invers_tax'))

    def get_invoices(self):
        if self.type == "sale":
            by_type = [
                '|','&',
                ('journal_id.l10n_ro_fiscal_receipt','=',True),
                ('journal_id.type','in', ['sale','general']),
                ('move_type', 'in', [
                "out_invoice",
                "out_refund",
                "out_receipt",
                "in_invoice",
                "in_refund",
                "in_receipt"
            ])]
        else:
            by_type = [('move_type', 'in', [
                        "in_invoice",
                        "in_refund",
                        "in_receipt"
                    ])]
        inv_domain = [
            ("date", ">=", self.start_date),
            ("date", "<=", self.end_date),
            ("state", "=", "posted"),
            "|",
            ("company_id", "=", self.company_id.id),
            ("company_id", "in", self.company_id.child_ids.ids)
        ] + by_type
        invoices = self.env['account.move'].search(inv_domain)
        if self.type == "sale":
            for inv in invoices.filtered(lambda i: i.move_type in ["in_invoice", "in_refund", "in_receipt"]):
                has_4427 = any(
                    getattr(line.account_id, "code", "")[:4] == "4427"
                    for line in inv.line_ids if line.account_id
                )
                has_4426 = any(
                    getattr(line.account_id, "code", "")[:4] == "4426"
                    for line in inv.line_ids if line.account_id
                )
                if (has_4427 == False) or (has_4426 == False):
                    invoices -= inv

        if self.env['account.move']._fields.get('pos_payment_ids', None):
            bonuri_moves = invoices.filtered(lambda x: x.pos_payment_ids)
            invoices -= bonuri_moves
        return invoices

    def get_paid_invoices(self):
        if self.type == "sale":
            types = [
                "out_invoice",
                "out_refund",
                "out_receipt"
            ]
        else:
            types = [
                "entry",
                "in_invoice",
                "in_refund",
                "in_receipt"
            ]
        fp = self.company_id.l10n_ro_property_vat_on_payment_position_id
        if not fp:
            fp = self.env["account.fiscal.position"].search(
                [
                    ("company_id", "=", self.company_id.id),
                    ("name", "=", "Regim TVA la Incasare"),
                ]
            )
        invoices = self.env["account.move"]
        if fp:
            vatp_invoices = self.env["account.move"].search(
                [
                    ("state", "=", "posted"),
                    ("move_type", "in", types),
                    ("date", ">=", self.start_date),
                    ("date", "<=", self.end_date),
                    ("fiscal_position_id", "=", fp.id),
                    "|",
                    ("company_id", "=", self.company_id.id),
                    ("company_id", "in", self.company_id.child_ids.ids),
                ]
            )
            for inv in vatp_invoices:

                if inv.payment_state not in ["paid", "reversed", "invoicing_legacy"]:
                    invoices |= inv
                elif inv.payment_state == "paid":
                    for itemrec in inv._get_reconciled_invoices_partials():
                        if not itemrec:
                            continue
                        partial, amount, counterpart_line = itemrec[0]
                        if counterpart_line.date >= self.start_date and counterpart_line.date <= self.end_date:
                            invoices |= inv

        cancel_supp_inv = invoices.filtered(
            lambda i: i.move_type in ["in_invoice", "in_refund", "in_receipt"]
            and i.state == "cancel"
        )
        invoices -= cancel_supp_inv
        non_current_tva0 = self.env['account.move']
        for inv in invoices:
            if inv.fiscal_position_id.name == 'Regim TVA la Incasare':
                for l in inv.line_ids:
                    if l.tax_tag_ids and l.tax_tag_ids.name == '+30 - BAZA' and (
                            self.start_date > inv.date or self.end_date < inv.date):
                        non_current_tva0 |= inv
        invoices -= non_current_tva0

        return invoices

    account_report_journal_line_ids = fields.One2many("account.report.journal.line", 'account_report_journal_id')

    def rebuild(self):
        for s in self:
            invoice_ids = s.get_invoices()
            invoice_ids |= s.get_paid_invoices()
            s.invoice_ids = [Command.set(invoice_ids.sorted(key=lambda r: r.invoice_date or r.date).ids)]
            if 'l10n.ro.account.dvi' in self.env:
                dvis = self.env['l10n.ro.account.dvi'].search([('date', '>', self.start_date), ('date', '<', self.end_date)])
            s.account_report_journal_line_ids.unlink()
            with_dvi = s.env['account.move']
            for i in invoice_ids:
                if 'l10n.ro.account.dvi' in self.env and i.l10n_ro_dvi_ids and s.type != 'sale':
                    with_dvi |= i
                    continue
                s.account_report_journal_line_ids = [Command.create({
                    'name': i.id
                })]
            if 'l10n.ro.account.dvi' in self.env and s.type != 'sale':
                for d in dvis:
                    for i in with_dvi:
                        if i.id in d.invoice_ids.ids:
                            s.account_report_journal_line_ids = [Command.create({'name': i.id})]
                    s.account_report_journal_line_ids = [Command.create({
                        'name': d.landed_cost_ids.account_move_id.id,
                        'is_dvi': True,
                        'dvi': d.id})]
            s.account_report_journal_line_ids.get_payments()

    def write_sale_xls(self, ws0):
        style_header = xlwt.easyxf('borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin; pattern: pattern solid, fore_colour custom_colour; font: bold on;')
        style = xlwt.easyxf('borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin;')
        ws0.write_merge(0, 1, 0, 0, 'Nr. crt.', style=style_header)
        ws0.write_merge(0, 0, 1, 2, 'Document', style=style_header)
        ws0.write_merge(1, 1, 1, 1, 'Numar', style=style_header)
        ws0.write_merge(1, 1, 2, 2, 'Data', style=style_header)
        ws0.write_merge(0, 1, 3, 3, 'Denumirea/Numele clientului/beneficiarului', style=style_header)
        ws0.write_merge(0, 1, 4, 4, 'Codul de înregistrare in scopuri de TVA al clientului/beneficiarului', style=style_header)
        ws0.write_merge(0, 1, 5, 5, 'Total document (inclusiv TVA)', style=style_header)
        ws0.write_merge(0, 0, 6, 13, 'Livrări de bunuri și prestări de servicii taxabile', style=style_header)
        ws0.write_merge(1, 1, 6, 6, 'Baza Total', style=style_header)
        ws0.write_merge(1, 1, 7, 7, 'TVA Total', style=style_header)
        ws0.write_merge(1, 1, 8, 8, 'Baza 19%', style=style_header)
        ws0.write_merge(1, 1, 9, 9, 'TVA 19%', style=style_header)
        ws0.write_merge(1, 1, 10, 10, 'Baza 9%', style=style_header)
        ws0.write_merge(1, 1, 11, 11, 'TVA 9%', style=style_header)
        ws0.write_merge(1, 1, 12, 12, 'Baza 5%', style=style_header)
        ws0.write_merge(1, 1, 13, 13, 'TVA 5%', style=style_header)
        ws0.write_merge(0, 1, 14, 14, 'Bunuri și servicii pentru care s-a aplicat un regim special, conform art. 1521 sau 1522 din Codul fiscal', style=style_header)
        ws0.write_merge(0, 0, 15, 19, 'Plati - Operatii exigibile', style=style_header)
        ws0.write_merge(1, 1, 15, 15, 'Numar', style=style_header)
        ws0.write_merge(1, 1, 16, 16, 'Data', style=style_header)
        ws0.write_merge(1, 1, 17, 17, 'Total', style=style_header)
        ws0.write_merge(1, 1, 18, 18, 'Baza', style=style_header)
        ws0.write_merge(1, 1, 19, 19, 'TVA', style=style_header)
        ws0.write_merge(0, 0, 20, 21, 'Operatii neexigibile', style=style_header)
        ws0.write_merge(1, 1, 20, 20, 'Baza', style=style_header)
        ws0.write_merge(1, 1, 21, 21, 'TVA', style=style_header)
        ws0.write_merge(0, 0, 22, 23, 'Livrări de bunuri și prestări de servicii pentru care locul livrării/prestării este în afara României', style=style_header)
        ws0.write_merge(1, 1, 22, 22, 'Cu drept de deducere', style=style_header)
        ws0.write_merge(1, 1, 23, 23, 'Fără drept de deducere', style=style_header)
        ws0.write_merge(0, 1, 24, 24, 'Scutite conform art. 143 alin. (2) lit. a) și d) din Codul fiscal', style=style_header)
        ws0.write_merge(0, 1, 25, 25, 'Scutite conform art. 143 alin. (2) lit. b) și c) din Codul fiscal', style=style_header)
        ws0.write_merge(0, 1, 26, 26, 'Alte livrări de bunuri și prestări de servicii scutite cu drept de deducere', style=style_header)
        ws0.write_merge(0, 0, 27, 28, 'Intracomunitară și taxare inversă', style=style_header)
        ws0.write_merge(1, 1, 27, 27, 'Baza', style=style_header)
        ws0.write_merge(1, 1, 28, 28, 'TVA', style=style_header)
        nr_crt = 1
        row_number = 2
        for line in self.account_report_journal_line_ids:
            payment_rowspan = len(line.journal_payment_ids) - 1 if len(line.journal_payment_ids) > 1 else 0
            ws0.write_merge(row_number, row_number + payment_rowspan, 0, 0, nr_crt, style=style)
            ws0.write_merge(row_number, row_number + payment_rowspan, 1, 1, line.name.display_name, style=style)
            ws0.write_merge(row_number, row_number + payment_rowspan, 2, 2, line.date.strftime("%d/%m/%Y"), style=style)
            ws0.write_merge(row_number, row_number + payment_rowspan, 3, 3, line.partner_id.display_name, style=style)
            ws0.write_merge(row_number, row_number + payment_rowspan, 4, 4, line.tva, style=style)
            ws0.write_merge(row_number, row_number + payment_rowspan, 5, 5, line.invoice_total, style=style)
            ws0.write_merge(row_number, row_number + payment_rowspan, 6, 6, line.total_base, style=style)
            ws0.write_merge(row_number, row_number + payment_rowspan, 7, 7, line.total_vat, style=style)
            ws0.write_merge(row_number, row_number + payment_rowspan, 8, 8, line.base_19, style=style)
            ws0.write_merge(row_number, row_number + payment_rowspan, 9, 9, line.tva_19, style=style)
            ws0.write_merge(row_number, row_number + payment_rowspan, 10, 10, line.base_9, style=style)
            ws0.write_merge(row_number, row_number + payment_rowspan, 11, 11, line.tva_9, style=style)
            ws0.write_merge(row_number, row_number + payment_rowspan, 12, 12, line.base_5, style=style)
            ws0.write_merge(row_number, row_number + payment_rowspan, 13, 13, line.tva_5, style=style)
            ws0.write_merge(row_number, row_number + payment_rowspan, 14, 14, line.base_0, style=style)
            ws0.write_merge(row_number, row_number, 15, 15, line.journal_payment_ids and line.journal_payment_ids[0].payment_number or '', style=style)
            ws0.write_merge(row_number, row_number, 16, 16, line.journal_payment_ids and line.journal_payment_ids[0].payment_date.strftime("%d/%m/%Y") or '', style=style)
            ws0.write_merge(row_number, row_number, 17, 17, line.journal_payment_ids and line.journal_payment_ids[0].total_exig or '', style=style)
            ws0.write_merge(row_number, row_number, 18, 18, line.journal_payment_ids and line.journal_payment_ids[0].base_exig or '', style=style)
            ws0.write_merge(row_number, row_number, 19, 19, line.journal_payment_ids and line.journal_payment_ids[0].tva_exig or '', style=style)
            ws0.write_merge(row_number, row_number + payment_rowspan, 20, 20, line.base_neex, style=style)
            ws0.write_merge(row_number, row_number + payment_rowspan, 21, 21, line.tva_neex, style=style)
            ws0.write_merge(row_number, row_number + payment_rowspan, 22, 22, line.intracom_base_deduction, style=style)
            ws0.write_merge(row_number, row_number + payment_rowspan, 23, 23, line.intracom_base_nondeduction, style=style)
            ws0.write_merge(row_number, row_number + payment_rowspan, 24, 24, line.intracom_scutit_a_d, style=style)
            ws0.write_merge(row_number, row_number + payment_rowspan, 25, 25, line.intracom_scutit_b_c, style=style)
            ws0.write_merge(row_number, row_number + payment_rowspan, 26, 26, line.intracom_scutit_other, style=style)
            ws0.write_merge(row_number, row_number + payment_rowspan, 27, 27, line.intracom_base_invers_tax, style=style)
            ws0.write_merge(row_number, row_number + payment_rowspan, 28, 28, line.intracom_tva_invers_tax, style=style)
            row_number += 1
            if payment_rowspan:
                for pay in line.journal_payment_ids[1:]:
                    ws0.write_merge(row_number, row_number, 0, 15, '', style=style)
                    ws0.write_merge(row_number, row_number, 15, 15, pay.payment_number, style=style)
                    ws0.write_merge(row_number, row_number, 16, 16, pay.payment_date.strftime("%d/%m/%Y"), style=style)
                    ws0.write_merge(row_number, row_number, 17, 17, pay.total_exig, style=style)
                    ws0.write_merge(row_number, row_number, 18, 18, pay.base_exig, style=style)
                    ws0.write_merge(row_number, row_number, 19, 19, pay.tva_exig, style=style)
                    ws0.write_merge(row_number, row_number, 20, 28, '', style=style)
                    row_number += 1
            nr_crt += 1

    def write_purchase_xls(self, ws0):
        style_header = xlwt.easyxf('borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin; pattern: pattern solid, fore_colour custom_colour; font: bold on;')
        style = xlwt.easyxf('borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin;')
        ws0.write_merge(0, 1, 0, 0, 'Nr. crt.', style=style_header)
        ws0.write_merge(0, 0, 1, 2, 'Document', style=style_header)
        ws0.write_merge(1, 1, 1, 1, 'Numar', style=style_header)
        ws0.write_merge(1, 1, 2, 2, 'Data', style=style_header)
        ws0.write_merge(0, 1, 3, 3, 'Denumirea/Numele clientului/beneficiarului', style=style_header)
        ws0.write_merge(0, 1, 4, 4, 'Codul de înregistrare in scopuri de TVA al clientului/beneficiarului', style=style_header)
        ws0.write_merge(0, 1, 5, 5, 'Total document (inclusiv TVA)', style=style_header)
        ws0.write_merge(0, 0, 6, 13, 'Achiziții de bunuri și servicii din țară și importuri de bunuri taxabile', style=style_header)
        ws0.write_merge(1, 1, 6, 6, 'Baza Total', style=style_header)
        ws0.write_merge(1, 1, 7, 7, 'TVA Total', style=style_header)
        ws0.write_merge(1, 1, 8, 8, 'Baza 19%', style=style_header)
        ws0.write_merge(1, 1, 9, 9, 'TVA 19%', style=style_header)
        ws0.write_merge(1, 1, 10, 10, 'Baza 9%', style=style_header)
        ws0.write_merge(1, 1, 11, 11, 'TVA 9%', style=style_header)
        ws0.write_merge(1, 1, 12, 12, 'Baza 5%', style=style_header)
        ws0.write_merge(1, 1, 13, 13, 'TVA 5%', style=style_header)
        ws0.write_merge(0, 1, 14, 14, 'Achiziții de bunuri scutite sau neimpozabile', style=style_header)
        ws0.write_merge(0, 0, 15, 19, 'Plati - Operatii exigibile', style=style_header)
        ws0.write_merge(1, 1, 15, 15, 'Numar', style=style_header)
        ws0.write_merge(1, 1, 16, 16, 'Data', style=style_header)
        ws0.write_merge(1, 1, 17, 17, 'Total', style=style_header)
        ws0.write_merge(1, 1, 18, 18, 'Baza', style=style_header)
        ws0.write_merge(1, 1, 19, 19, 'TVA', style=style_header)
        ws0.write_merge(0, 0, 20, 21, 'Operatii neexigibile', style=style_header)
        ws0.write_merge(1, 1, 20, 20, 'Baza', style=style_header)
        ws0.write_merge(1, 1, 21, 21, 'TVA', style=style_header)
        ws0.write_merge(0, 0, 22, 25, 'Achiziții intracomunitare de servicii și bunuri', style=style_header)
        ws0.write_merge(1, 1, 22, 22, 'Baza Servicii', style=style_header)
        ws0.write_merge(1, 1, 23, 23, 'TVA Servicii', style=style_header)
        ws0.write_merge(1, 1, 24, 24, 'Baza Produse', style=style_header)
        ws0.write_merge(1, 1, 25, 25, 'TVA Produse', style=style_header)
        ws0.write_merge(0, 1, 26, 26, 'Intracom. cumpărături scutite', style=style_header)
        ws0.write_merge(0, 1, 27, 27, 'Intracom. cumpărături neimpozabile', style=style_header)
        ws0.write_merge(0, 0, 28, 29, 'Intracomunitară și taxare inversă', style=style_header)
        ws0.write_merge(1, 1, 28, 28, 'Baza', style=style_header)
        ws0.write_merge(1, 1, 29, 29, 'TVA', style=style_header)
        nr_crt = 1
        row_number = 2
        for line in self.account_report_journal_line_ids:
            payment_rowspan = len(line.journal_payment_ids) - 1 if len(line.journal_payment_ids) > 1 else 0
            ws0.write_merge(row_number, row_number + payment_rowspan, 0, 0, nr_crt, style=style)
            ws0.write_merge(row_number, row_number + payment_rowspan, 1, 1, line.name.display_name, style=style)
            ws0.write_merge(row_number, row_number + payment_rowspan, 2, 2, line.date.strftime("%d/%m/%Y"), style=style)
            ws0.write_merge(row_number, row_number + payment_rowspan, 3, 3, line.partner_id.name or line.name.tax_cash_basis_origin_move_id.partner_id.name or '', style=style)
            ws0.write_merge(row_number, row_number + payment_rowspan, 4, 4, line.tva or line.name.tax_cash_basis_origin_move_id.partner_id.vat or '', style=style)
            ws0.write_merge(row_number, row_number + payment_rowspan, 5, 5, line.invoice_total, style=style)
            ws0.write_merge(row_number, row_number + payment_rowspan, 6, 6, line.total_base, style=style)
            ws0.write_merge(row_number, row_number + payment_rowspan, 7, 7, line.total_vat, style=style)
            ws0.write_merge(row_number, row_number + payment_rowspan, 8, 8, line.base_19, style=style)
            ws0.write_merge(row_number, row_number + payment_rowspan, 9, 9, line.tva_19, style=style)
            ws0.write_merge(row_number, row_number + payment_rowspan, 10, 10, line.base_9, style=style)
            ws0.write_merge(row_number, row_number + payment_rowspan, 11, 11, line.tva_9, style=style)
            ws0.write_merge(row_number, row_number + payment_rowspan, 12, 12, line.base_5, style=style)
            ws0.write_merge(row_number, row_number + payment_rowspan, 13, 13, line.tva_5, style=style)
            ws0.write_merge(row_number, row_number + payment_rowspan, 14, 14, line.base_0, style=style)
            ws0.write_merge(row_number, row_number, 15, 15, line.journal_payment_ids and line.journal_payment_ids[0].payment_number or '', style=style)
            ws0.write_merge(row_number, row_number, 16, 16, line.journal_payment_ids and line.journal_payment_ids[0].payment_date.strftime("%d/%m/%Y") or '', style=style)
            ws0.write_merge(row_number, row_number, 17, 17, line.journal_payment_ids and line.journal_payment_ids[0].total_exig or '', style=style)
            ws0.write_merge(row_number, row_number, 18, 18, line.journal_payment_ids and line.journal_payment_ids[0].base_exig or '', style=style)
            ws0.write_merge(row_number, row_number, 19, 19, line.journal_payment_ids and line.journal_payment_ids[0].tva_exig or '', style=style)
            ws0.write_merge(row_number, row_number + payment_rowspan, 20, 20, line.base_neex, style=style)
            ws0.write_merge(row_number, row_number + payment_rowspan, 21, 21, line.tva_neex, style=style)
            ws0.write_merge(row_number, row_number + payment_rowspan, 22, 22, line.intracom_base_deduction, style=style)
            ws0.write_merge(row_number, row_number + payment_rowspan, 23, 23, line.intracom_tva_deduction, style=style)
            ws0.write_merge(row_number, row_number + payment_rowspan, 24, 24, line.intracom_base_nondeduction, style=style)
            ws0.write_merge(row_number, row_number + payment_rowspan, 25, 25, line.intracom_tva_nondeduction, style=style)
            ws0.write_merge(row_number, row_number + payment_rowspan, 26, 26, line.intracom_scutit_a_d, style=style)
            ws0.write_merge(row_number, row_number + payment_rowspan, 27, 27, line.intracom_scutit_b_c, style=style)
            ws0.write_merge(row_number, row_number + payment_rowspan, 28, 28, line.intracom_base_invers_tax, style=style)
            ws0.write_merge(row_number, row_number + payment_rowspan, 29, 29, line.intracom_tva_invers_tax, style=style)
            row_number += 1
            if payment_rowspan:
                for pay in line.journal_payment_ids[1:]:
                    ws0.write_merge(row_number, row_number, 15, 15, pay.payment_number, style=style)
                    ws0.write_merge(row_number, row_number, 16, 16, pay.payment_date and pay.payment_date.strftime("%d/%m/%Y") or '', style=style)
                    ws0.write_merge(row_number, row_number, 17, 17, pay.total_exig, style=style)
                    ws0.write_merge(row_number, row_number, 18, 18, pay.base_exig, style=style)
                    ws0.write_merge(row_number, row_number, 19, 19, pay.tva_exig, style=style)
                    row_number += 1
            nr_crt += 1

    def export(self):
        xlwt.add_palette_colour("custom_colour", 0x21)
        f = BytesIO()
        wb = xlwt.Workbook()
        sheet1_name = "Centralizator %s" % (self.name,)
        wb.add_sheet(sheet1_name)

        xlwt.add_palette_colour("custom_colour", 0x21)
        wb.set_colour_RGB(0x21, 220, 220, 220)

        ws0 = wb.get_sheet(0)
        if self.type == 'sale':
            self.write_sale_xls(ws0)
        else:
            self.write_purchase_xls(ws0)
        wb.save(f)
        file_name = self.name + ".xls"
        data_file = f.getvalue()

        attachment = self.env["ir.attachment"].create(
            {
                "name": file_name,
                "raw": data_file,
                "mimetype": "application/xlsx",
                "res_model": "account.report.journal",
                "res_id": self.id,
            }
        )
        return {
            "type": "ir.actions.act_url",
            "url": "/web/content?model=%s&download=True&field=datas&id=%s&filename=%s"
            % ("ir.attachment", attachment.id, file_name),
            "target": "new",
        }


class AccountReportJournalLine(models.Model):
    _name = "account.report.journal.line"
    _description = "Account Report Journal Line"

    account_report_journal_id = fields.Many2one("account.report.journal")

    name = fields.Many2one("account.move", string="Invoice")
    partner_id = fields.Many2one("res.partner", string="Partner", related="name.commercial_partner_id")
    date = fields.Date(string="Data", related="name.date", store=True)
    tva = fields.Char(string="TVA", related="partner_id.vat", store=True)

    is_dvi = fields.Boolean(string="Is DVI")
    dvi = fields.Many2one("l10n.ro.account.dvi", string="DVI")

    #Invoice/Bill Values
    invoice_total = fields.Float(string="Total Document", compute="_get_line_values", store=True)
    total_base = fields.Float(string="Taxabile - Total Baza", compute="_get_line_values", store=True)
    total_vat = fields.Float(string="Taxabile - Total TVA", compute="_get_line_values", store=True)
    base_19 = fields.Float(string="Taxabile - Baza 19%", compute="_get_line_values", store=True)
    tva_19 = fields.Float(string="Taxabile - TVA 19%", compute="_get_line_values", store=True)
    base_9 = fields.Float(string="Taxabile - Baza 9%", compute="_get_line_values", store=True)
    tva_9 = fields.Float(string="Taxabile - TVA 9%", compute="_get_line_values", store=True)
    base_5 = fields.Float(string="Taxabile - Baza 5%", compute="_get_line_values", store=True)
    tva_5 = fields.Float(string="Taxabile - TVA 5%", compute="_get_line_values", store=True)
    base_0 = fields.Float(string="Baza Regim Special", compute="_get_line_values", store=True)
    base_invers_tax = fields.Float(string="Baza Taxare Inversa", compute="_get_line_values", store=True)

    intracom_base_deduction = fields.Float(string="Intracom. - Cu Deducere Baza", compute="_get_line_values", store=True)
    intracom_tva_deduction = fields.Float(string="Intracom. - Cu Deducere TVA", compute="_get_line_values", store=True)
    intracom_base_nondeduction = fields.Float(string="Intracom. - Fara Deducere Baza", compute="_get_line_values", store=True)
    intracom_tva_nondeduction = fields.Float(string="Intracom. - Fara Deducere TVA", compute="_get_line_values", store=True)
    intracom_scutit_a_d = fields.Float(string="Intracom. - Scutit art.143 al.2 lit.a+d", compute="_get_line_values", store=True)
    intracom_scutit_b_c = fields.Float(string="Intracom. - Scutit art.143 al.2 lit.b+c", compute="_get_line_values", store=True)
    intracom_scutit_other = fields.Float(string="Intracom. - Scutit Altele", compute="_get_line_values", store=True)
    intracom_base_invers_tax = fields.Float(string="Intracom. - Baza Taxare Inversa", compute="_get_line_values", store=True)
    intracom_tva_invers_tax = fields.Float(string="Intracom. - TVA Taxare Inversa", compute="_get_line_values", store=True)

    @api.depends("name")
    def _get_line_values(self):
        for s in self:
            sign = s.name.journal_id.type == 'purchase' and -1 or 1
            sign_all = s.name.move_type in ['in_refund', 'out_refund'] and -1 or 1

            s.invoice_total = sign * s.name.amount_total_signed

            tags_19 = ["09", "09_1", "09_2", "24", "24_1", "24_2"]
            base_19 = 0
            tva_19 = 0
            for tag in tags_19:
                base_19 += s.get_balance(f"{tag} - TAX BASE")
                tva_19 += s.get_balance(f"{tag} - VAT")
            s.base_19 = base_19*sign_all
            s.tva_19 = tva_19*sign_all

            tags_9 = ["10", "10_1", "10_2", "25", "25_1", "25_2"]
            base_9 = 0
            tva_9 = 0
            for tag in tags_9:
                base_9 += s.get_balance(f"{tag} - TAX BASE")
                tva_9 += s.get_balance(f"{tag} - VAT")
            s.base_9 = base_9*sign_all
            s.tva_9 = tva_9*sign_all

            tags_5 = ["11", "11_1", "11_2", "26", "26_1", "26_2"]
            base_5 = 0
            tva_5 = 0
            for tag in tags_5:
                base_5 += s.get_balance(f"{tag} - TAX BASE")
                tva_5 += s.get_balance(f"{tag} - VAT")
            s.base_5 = base_5*sign_all
            s.tva_5 = tva_5*sign_all

            tags_0 = ["14 - TAX BASE", "30 - TAX BASE"]
            base_0 = 0
            if s.partner_id.l10n_ro_partner_type in ["1", "2", "4"]:
                for tag in tags_0:
                    base_0 += s.get_balance(tag)
            s.base_0 = base_0*sign_all

            tags_invers = ["13 - TAX BASE"]
            base_invers_tax = 0
            for tag in tags_invers:
                base_invers_tax += s.get_balance(tag)
            s.base_invers_tax = base_invers_tax*sign_all

            # tags_invers = ["13 - TAX BASE"]
            # base_invers_tax = 0
            # for tag in tags_invers:
            #     base_invers_tax += s.get_balance(tag)
            # s.base_invers_tax = base_invers_tax*sign_all

            tags_intracom_base_deduction = ["22_1 - TAX BASE", "03 - TAX BASE"]
            intracom_base_deduction = 0
            for tag in tags_intracom_base_deduction:
                intracom_base_deduction += s.get_balance(tag)
            s.intracom_base_deduction = intracom_base_deduction*sign_all

            tags_intracom_tva_deduction = ["22_1 - VAT"]
            intracom_tva_deduction = 0
            for tag in tags_intracom_tva_deduction:
                intracom_tva_deduction += s.get_balance(tag)
            s.intracom_tva_deduction = intracom_tva_deduction*sign_all

            tags_intracom_base_nondeduction = ["20_1 - TAX BASE"]
            intracom_base_nondeduction = 0
            for tag in tags_intracom_base_nondeduction:
                intracom_base_nondeduction += s.get_balance(tag)
            s.intracom_base_nondeduction = intracom_base_nondeduction*sign_all

            tags_intracom_tva_nondeduction = ["20_1 - VAT"]
            intracom_tva_nondeduction = 0
            for tag in tags_intracom_tva_nondeduction:
                intracom_tva_nondeduction += s.get_balance(tag)
            s.intracom_tva_nondeduction = intracom_tva_nondeduction*sign_all


            tags_intracom_scutit_a_d = ["01 - TAX BASE", "14 - TAX BASE", "30 - TAX BASE"]
            intracom_scutit_a_d = 0
            if s.partner_id.l10n_ro_partner_type in ["3"]:
                for tag in tags_intracom_scutit_a_d:
                    intracom_scutit_a_d += s.get_balance(tag)
            s.intracom_scutit_a_d = intracom_scutit_a_d*sign_all

            tags_intracom_scutit_b_c = ["15 - TAX BASE"]
            intracom_scutit_b_c = 0
            for tag in tags_intracom_scutit_b_c:
                intracom_scutit_b_c += s.get_balance(tag)
            s.intracom_scutit_b_c = intracom_scutit_b_c*sign_all


            tags_intracom_scutit_other = ["03_1 - TAX BASE", "14 - TAX BASE", "30 - TAX BASE"]
            intracom_scutit_other = 0
            if not s.partner_id.l10n_ro_partner_type:
                for tag in tags_intracom_scutit_other:
                    intracom_scutit_other += s.get_balance(tag)
            s.intracom_scutit_other = intracom_scutit_other*sign_all

            tags_intracom_invers_tax = ["27_1", "27_2", "27_3", "22_1", "20_1"]
            intracom_base_invers_tax = 0
            intracom_tva_invers_tax = 0
            for tag in tags_intracom_invers_tax:
                intracom_base_invers_tax += s.get_balance(f"{tag} - TAX BASE")
                intracom_tva_invers_tax += s.get_balance(f"{tag} - VAT")
            s.intracom_base_invers_tax = intracom_base_invers_tax*sign_all
            s.intracom_tva_invers_tax = intracom_tva_invers_tax*sign_all

            s.total_base = s.base_19 + s.base_9 + s.base_5
            s.total_vat = s.tva_19 + s.tva_9 + s.tva_5

            if s.is_dvi:
                dvi_record = s.env['l10n.ro.account.dvi'].browse(s.dvi.id)
                s.invoice_total = dvi_record.total_tax_value + dvi_record.customs_duty_value
                s.total_base = dvi_record.customs_duty_value
                s.base_19 = dvi_record.customs_duty_value

    #Payments Values
    journal_payment_ids = fields.One2many("account.report.journal.payment", "account_report_journal_line_id")

    base_neex = fields.Float(string="Op. neexigibile - Baza", compute="_get_payment_values", store=True)
    tva_neex = fields.Float(string="Op. neexigibile - TVA", compute="_get_payment_values", store=True)

    def get_payments(self):
        for s in self:
            for pay in s.name._get_reconciled_invoices_partials()[0]:
                moves = self.env["account.move"].search([
                    ("tax_cash_basis_rec_id", "=", pay[0].id),
                    ("date", ">=", s.account_report_journal_id.start_date)
                ])
                s.journal_payment_ids.unlink()
                for move in moves:
                    s.journal_payment_ids = [Command.create({
                        'name': move.id
                    })]

    @api.depends("journal_payment_ids")
    def _get_payment_values(self):
        for s in self:
            fp = self.account_report_journal_id.company_id.l10n_ro_property_vat_on_payment_position_id
            if not fp:
                fp = self.env["account.fiscal.position"].search(
                    [
                        ("company_id", "=", self.account_report_journal_id.company_id.id),
                        ("name", "=", "Regim TVA la Incasare"),
                    ]
                )
            tags_payment = [
                "09", "09_1", "09_2", "10", "10_1", "10_2", "11", "11_1", "11_2", "24", "24_1", "24_2",
                "25", "25_1", "25_2", "26", "26_1", "26_2"
            ]
            base_neex = 0
            tva_neex = 0
            if s.name.fiscal_position_id.id == fp.id:
                for tag in tags_payment:
                    base_neex += s.get_balance(f"{tag} - TAX BASE")
                    tva_neex += s.get_balance(f"{tag} - VAT")
            s.base_neex = base_neex - sum(s.journal_payment_ids.mapped('base_exig'))
            s.tva_neex = tva_neex - sum(s.journal_payment_ids.mapped('tva_exig'))

    def get_balance(self, tag):
        move_lines = self.name.line_ids.filtered(lambda x: tag in x.tax_tag_ids._get_related_tax_report_expressions().mapped('formula'))
        if move_lines:
            subtotal_sign = sum(move_lines.mapped('price_subtotal'))
            balance_sum = sum(move_lines.mapped('balance'))
            if subtotal_sign < 0:
                return abs(balance_sum) * -1
            elif subtotal_sign >= 0:
                return abs(balance_sum)
            else:
                return abs(sum(move_lines.mapped('balance')))
        return 0

class AccountReportJournalPayment(models.Model):
    _name = "account.report.journal.payment"
    _description = "Account Report Journal Payment"

    account_report_journal_line_id = fields.Many2one("account.report.journal.line")
    name = fields.Many2one("account.move", string="Plata")
    payment_number = fields.Char(string="Plati - Numar", compute="get_payment_data", store=True)
    payment_date = fields.Date(string="Plati - Data", compute="get_payment_data", store=True)
    total_exig = fields.Float(string="Plati - Op. exigibile - Total", compute="_get_line_values", store=True)
    base_exig = fields.Float(string="Plati - Op. exigibile - Baza", compute="_get_line_values", store=True)
    tva_exig = fields.Float(string="Plati - Op. exigibile - TVA", compute="_get_line_values", store=True)

    @api.depends("name")
    def get_payment_data(self):
        for s in self:
            if s.name.tax_cash_basis_rec_id.debit_move_id.move_id.id != s.account_report_journal_line_id.name.id:
                payment = s.name.tax_cash_basis_rec_id.debit_move_id.move_id
            else:
                payment = s.name.tax_cash_basis_rec_id.credit_move_id.move_id
            s.payment_number = payment.name
            s.payment_date = payment.date

    @api.depends("name")
    def _get_line_values(self):
        for s in self:
            tags_exig = [
                "09", "09_1", "09_2", "10", "10_1", "10_2", "11", "11_1", "11_2", "24", "24_1", "24_2",
                "25", "25_1", "25_2", "26", "26_1", "26_2"
            ]
            base_exig = 0
            tva_exig = 0
            for tag in tags_exig:
                base_exig += s.get_balance(f"{tag} - TAX BASE")
                tva_exig += s.get_balance(f"{tag} - VAT")
            s.base_exig = base_exig
            s.tva_exig = tva_exig
            s.total_exig = base_exig + tva_exig

    def get_balance(self, tag):
        move_lines = self.name.line_ids.filtered(lambda x: tag in x.tax_tag_ids._get_related_tax_report_expressions().mapped('formula'))
        if move_lines:
            return abs(sum(move_lines.mapped('balance')))
        return 0

