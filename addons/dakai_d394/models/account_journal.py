from odoo import api, fields, models
from .common_decl import journal_sequence_type

class AccountJournal(models.Model):
    _name = "account.journal"
    _inherit = ["account.journal", "l10n.ro.mixin"]

    l10n_ro_sequence_type = fields.Selection(
        selection=journal_sequence_type(), string="Ro Sequence Type", default="normal"
    )
