from odoo import models, api, fields

class ProductCategory(models.Model):

    _inherit = "product.category"
    
    change_planned_cost = fields.Boolean()

class ProductProduct(models.Model):

    _inherit = "product.product"

    def _get_domain_locations(self):
        domain_quant_loc, domain_move_in_loc, domain_move_out_loc = super(ProductProduct, self)._get_domain_locations()
        task_id = self.env.context.get('task')
        if task_id:
            domain_move_in_loc = domain_move_in_loc + [('task_id', '=', task_id)]
            domain_move_out_loc = domain_move_out_loc + [('task_id', '=', task_id)]
        return (
            domain_quant_loc,
            domain_move_in_loc,
            domain_move_out_loc
        )


    def _select_seller(self, partner_id=False, quantity=0.0, date=None, uom_id=False, ordered_by='price_discounted', params=False):
        supp = super(ProductProduct, self)._select_seller(partner_id=partner_id, quantity=quantity, date=date, uom_id=uom_id, ordered_by=ordered_by, params=params)
        if not supp and self._context.get('procurement_source_id', None) and partner_id:
            project = self.env['project.site.procurement'].browse(self._context.get('procurement_source_id')).project_id
            supp = self.env['product.supplierinfo'].create({
                    'partner_id': partner_id.id,
                    'sequence': max(self.seller_ids.mapped('sequence')) + 1 if self.seller_ids else 1,
                    'min_qty': 0.0,
                    'price': 0,
                    'currency_id': project.pricelist_id.currency_id.id,
                    'delay': 0,
                })
        return supp