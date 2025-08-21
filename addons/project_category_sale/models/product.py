from odoo import models, api, fields

class ProductProduct(models.Model):

    _inherit = "product.template"

    project_category_id = fields.Many2one("project.category", "Project Category")
