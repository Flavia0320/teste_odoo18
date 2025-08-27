from odoo import api, fields, models, Command
from .common_decl import journal_sequence_type


class DeclaratiaD394SerieFacturi(models.Model):
    _name = "report.d394.serie_facturi"
    _description = "Declaratia D394 Serie Facturi"

    name = fields.Char(compute="_compute_name", store=True)

    @api.depends('d394_id', 'serieI')
    def _compute_name(self):
        for s in self:
            s.name = f"SerieFacturi - {s.serieI}%"

    d394_id = fields.Many2one('l10_romania.report.d394')
    journal_id = fields.Many2one('account.journal')
    invoice_ids = fields.Many2many('account.move')
    l10n_ro_sequence_type = fields.Integer(string="Ro Sequence Type", compute="_get_journal_type", store=True)
    serieI = fields.Char(string="serieI", compute="_get_serie_nr", store=True)
    nrI = fields.Char(string="nrI", compute="_get_serie_nr", store=True)
    nrF = fields.Char(string="nrF", compute="_get_serie_nr", store=True)
    den = fields.Char(string="den")
    cui = fields.Integer(string="cui")

    @api.depends('journal_id')
    def _get_journal_type(self):
        for s in self:
            if s.journal_id.type == "sale" or s.journal_id.l10n_ro_sequence_type == "autoinv2":
                tip = 4
                if s.journal_id.l10n_ro_sequence_type == "normal":
                    tip = 2
                elif s.journal_id.l10n_ro_sequence_type == "autoinv1":
                    tip = 3
                else:
                    tip = 1
                s.l10n_ro_sequence_type = tip

    @api.depends('invoice_ids')
    def _get_serie_nr(self):
        for s in self:
            if len(s.invoice_ids) != 0:
                s.serieI = s.invoice_ids[0].sequence_prefix
                s.nrI = min(s.invoice_ids.mapped('sequence_number'))
                s.nrF = max(s.invoice_ids.mapped('sequence_number'))

    @api.model
    def generate(self, d394_id):
        d394_id.serie_facturi_ids.unlink()
        invoices = d394_id.invoice_ids.filtered(
            lambda i: i.move_type in ("out_invoice", "out_refund")
        )
        journal_ids = invoices.mapped("journal_id")
        for journal in journal_ids:
            if journal.type == "sale" or journal.l10n_ro_sequence_type == "autoinv2":
                journal_invoices = invoices.filtered(
                    lambda r: r.journal_id.id == journal.id
                )
                inv1 = {
                    "d394_id": d394_id.id,
                    "l10n_ro_sequence_type": 1,
                    'invoice_ids': [Command.set(journal_invoices.filtered(lambda x: 'refund' not in x.move_type).ids)]
                }
                self.create(inv1)
                inv2 = inv1.copy()
                inv2.update({
                    "journal_id": journal.id,
                })
                self.create(inv2)

                #Add Refund Sequences.
                if journal.refund_sequence:
                    rev1 = {
                        "d394_id": d394_id.id,
                        "l10n_ro_sequence_type": 1,
                        'invoice_ids': [Command.set(journal_invoices.filtered(lambda x: 'refund' in x.move_type).ids)]
                    }
                    self.create(rev1)
                    rev2 = rev1.copy()
                    rev2.update({
                        "journal_id": journal.id,
                    })
                    self.create(rev2)

                # if journal.l10n_ro_sequence_type == "normal":
                #     self.create({
                #         "d394_id": d394_id.id,
                #         "l10n_ro_sequence_type": 1,
                #         'invoice_ids': [Command.set(journal_invoices.ids)]
                #     })
