from odoo import fields, models, _


class Transport(models.Model):
    _inherit = "fleet.vehicle"

    sale_km_price = fields.Float(string="Price per km")

