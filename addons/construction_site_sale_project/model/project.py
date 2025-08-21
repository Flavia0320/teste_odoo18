from odoo import api, models

class Project(models.Model):
    _inherit = "project.project"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('sale_line_id'):
                order_id = self.env['sale.order.line'].browse([vals.get('sale_line_id')]).order_id
                if order_id.obiectiv:
                    vals['name'] = order_id.obiectiv
                    vals.update({
                        'name': order_id.obiectiv,
                        'is_construction_site': True,
                        'supply_warehouse_id': order_id.warehouse_id.id,
                    })
        projects = super().create(vals_list)
        return projects

    @api.depends('partner_id', 'sale_order_id')
    def _setPriceList(self):
        for s in self:
            pl = s.sale_order_id and s.sale_order_id.pricelist_id or s.partner_id.property_product_pricelist
            s.pricelist_id = pl and pl.id or None