from odoo import fields, models


class ResCompany(models.Model):
    _name = "res.company"
    _inherit = ["res.company", "l10n.ro.mixin"]

    l10n_ro_affiliated_person_ids = fields.Many2many(
        "res.partner", "res_company_affiliated_partner_rel", string="Affiliated Persons")
