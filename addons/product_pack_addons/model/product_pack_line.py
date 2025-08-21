from odoo import api, fields, models, _


class ProductpackLine(models.Model):
    _inherit = 'product.pack.line'
    
    sequence = fields.Integer(_("Sequence"))
    price_unit = fields.Float(_("Price Unit"))
    default_price = fields.Boolean(_("Default Price Unit"), default=True)
    
    @api.onchange('product_id')
    def changeProductToPrice(self):
        if self.product_id:
            self.price_unit = self.product_id.list_price
            
    def getUnitPrice(self):
        return self.default_price and self.price_unit or self.product_id.price
            
    def get_price(self):
        self.ensure_one()
        return self.getUnitPrice() * self.quantity
