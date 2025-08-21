from odoo import api, fields, models, _


class Product(models.Model):
    _inherit = "product.template"
    
    pack_down_id = fields.Many2one("product.product", _("Pack Down"))
    pack_up_id = fields.Many2one("product.product", _("Pack Up"))
    
    pack_down_ids = fields.Many2many("product.product", string=_("Packs Down"), compute="_getPacksDown")
    pack_up_ids = fields.Many2many("product.product", string=_("Packs Up"), compute="_getPacksUp")
    
    
    @api.depends('pack_line_ids')
    def _getPacksDown(self):
        for s in self:
            s.pack_up_ids = [(6, 0, s.getProductPackUp().ids)]
    
    @api.depends('pack_line_ids')
    def _getPacksUp(self):
        for s in self:
            s.pack_down_ids = [(6, 0, s.getProductPackDown().ids)]
    
    def getProductPackUp(self):
        return self.getPack('up')
        
    def getProductPackDown(self):
        return self.getPack('down')
    
    def getPackUp(self):
        prod = self.getProductPackUp()
        return prod and self.browse(prod.mapped('product_tmpl_id'))
        
    def getPackDown(self):
        prod = self.getProductPackDown()
        return prod and self.browse(prod.mapped('product_tmpl_id'))
        
    def getPack(self, mode=None):
        if not mode:
            return None
        self.ensure_one()
        prod = self.env['product.product']
        
        def getDown(product, ids=[]):
            if product.pack_down_id:
                ids.append(product.pack_down_id.id)
                return getUp(product.pack_down_id, ids=ids)
            return ids
        
        def getUp(product, ids=[]):
            if product.pack_down_id:
                ids.append(product.pack_down_id.id)
                return getUp(product.pack_down_id, ids=ids)
            return ids
        
        ids = []
        if mode=='up':
            ids = getUp(self, ids=[])
            
        elif mode=='down':
            ids = getDown(self, ids=[])
            
        return prod.browse(ids)
