from odoo import fields, models


class ResCountryState(models.Model):
    _name = "res.country.state"
    _inherit = ["res.country.state", "l10n.ro.mixin"]

    l10n_ro_order_code = fields.Char("Ro Order Code")
