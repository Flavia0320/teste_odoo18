from odoo import models, fields, _

class ProductCategory(models.Model):
    _inherit = 'product.category'

    anaf_code = fields.Char(string='ANAF Code')