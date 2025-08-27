from odoo import api, fields, models

class ResPartner(models.Model):
    _name = "res.partner"
    _inherit = ["res.partner", "l10n.ro.mixin"]

    l10n_ro_country_code = fields.Char("Cod Tara", compute="_get_l10n_ro_country_code", store=True)

    @api.depends("vat", "country_id", "is_l10n_ro_record")
    def _get_l10n_ro_country_code(self):
        for s in self:
            l10n_ro_country_code = False
            if s.is_l10n_ro_record:
                vat_country_code = s.vat and s._split_vat(s.vat)[0].upper() or False
                country_country_code = s.country_id and s.country_id.code.upper() or False
                l10n_ro_country_code = vat_country_code or country_country_code
                if l10n_ro_country_code != country_country_code:
                    l10n_ro_country_code = country_country_code
                country_code_map = {
                    "RE": "FR",
                    "GP": "FR",
                    "MQ": "FR",
                    "GF": "FR",
                    "EL": "GR",
                }
                l10n_ro_country_code = country_code_map.get(l10n_ro_country_code, l10n_ro_country_code)
            s.l10n_ro_country_code = l10n_ro_country_code

    l10n_ro_partner_type = fields.Selection([
            ("1", "Inregistrat in scopuri de TVA"),
            ("2", "Neinregistrat in scopuri de TVA"),
            ("3", "Extern, neinregistrat/neobligat inregistrare in scopuri de TVA."),
            ("4", "Extern UE, neinregistrat/neobligat inregistrare in scopuri de TVA."),
        ], string="Tip Partener", compute="_get_l10n_ro_partner_type", store=True)

    @api.depends("l10n_ro_country_code", "l10n_ro_vat_subjected")
    def _get_l10n_ro_partner_type(self):
        for s in self:
            partner_type = "4"
            if s.l10n_ro_country_code:
                if s.l10n_ro_country_code == "RO":
                    partner_type = s.l10n_ro_vat_subjected and "1" or "2"
                elif s.l10n_ro_country_code == "XI":
                    partner_type = "3"
                else:
                    europe_group = self.env.ref("base.europe", raise_if_not_found=False)
                    if not europe_group:
                        europe_group = self.env["res.country.group"].search([("name", "=", "Europe")], limit=1)
                    if europe_group and europe_group.country_ids.filtered(lambda x: x.code == s.l10n_ro_country_code):
                        partner_type = "3"
            s.l10n_ro_partner_type = partner_type


