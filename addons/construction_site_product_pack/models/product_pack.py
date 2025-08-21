from odoo import api, models, fields


class ProductPackLine(models.Model):
    _inherit = "product.pack.line"

    def flatProductHierarchy(self, default_qty=1):
        product_lines = []
        product_lines += self.filtered(lambda x: not x.product_id.pack_ok).packItems(default_qty=default_qty)
        for line_pack in self.filtered(lambda x: x.product_id.pack_ok):
            product_lines += line_pack.product_id.pack_line_ids.flatProductHierarchy(default_qty=line_pack.quantity)
        return product_lines

    def packItems(self, default_qty=1):
        pack = []
        for s in self:
            pack.append(s._mkPackItemValues(default_qty=default_qty))
        return pack

    def _mkPackItemValues(self, default_qty=1):
        return {
            'product_id':self.product_id,
            'quantity': self.quantity * default_qty,
            'price_unit': self.get_price(),
            }
