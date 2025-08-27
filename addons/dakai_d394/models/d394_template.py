from odoo import api, fields, models
from .common_decl import period


class D394Template(models.Model):
    _name = "report.d394.template"
    _description = "Template D394"

    tip_D394 = fields.Selection(selection=period(), string="Perioada cuprinsa")
    company_id = fields.Many2one("res.company")
    reprezentant_id = fields.Many2one("l10-romania.report.reprezentant")
    transaction_with_afiliates = fields.Boolean()
