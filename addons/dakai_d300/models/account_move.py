from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    d300_id = fields.Many2one("l10_romania.report.d300")

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    d300_id = fields.Many2one("l10_romania.report.d300")
