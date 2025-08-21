from odoo import models, fields, _

class ResCompany(models.Model):
    _inherit = "res.company"

    purchase_force_qty = fields.Boolean(string=_("Construction - Purchase Force Qty"), help=_("Generate purchase from procurment regardless supply warehouse stock."))