from odoo import api, fields, models


class ProductMapper(models.Model):
    _name = "construction.product.mapper"
    
    product_id = fields.Many2one('product.product')
    name = fields.Char()
    model = fields.Char()