from odoo import models, api, fields

class ProductProduct(models.Model):

    _inherit = "product.template"

    is_construction = fields.Boolean("Create construction project")
