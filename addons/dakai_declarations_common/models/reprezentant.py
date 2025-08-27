from odoo import api, fields, models


class Reprezentant(models.Model):
    _name = "l10_romania.report.reprezentant"
    _description = "Reprezentant Depunere Declaratii"
    _inherits = {"res.partner": "partner_id"}

    partner_id = fields.Many2one("res.partner")
    cnp = fields.Char(string="CNP")
    nume = fields.Char(string="Nume")
    prenume = fields.Char(string="Prenume")

    def create_company(self, *args, **kwargs):
        return self.partner_id.create_company(*args, **kwargs)

    @api.onchange("nume", "prenume")
    def _set_name(self):
        self.name = "%s %s" % (self.nume, self.prenume)
