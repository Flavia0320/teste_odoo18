from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    d390_id = fields.Many2one("l10_romania.report.d390")
