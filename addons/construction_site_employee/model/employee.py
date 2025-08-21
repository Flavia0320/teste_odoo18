from odoo import fields, models, _

class HeEmployee(models.Model):

    _inherit = "hr.employee"

    sale_hour_price = fields.Float()
