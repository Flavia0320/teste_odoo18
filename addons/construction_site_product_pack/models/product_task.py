from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.misc import clean_context


class Task(models.Model):
    _inherit = "project.task"

    product_id = fields.Many2one(
        "product.template", string="Product Pack", copy=True,
    )
    quantity = fields.Float(string="Quantity", copy=True,)
    uom_id = fields.Many2one("uom.uom", string="Uom", related="product_id.uom_id")

    def loadProducts_change_pqty(self, product_id, q=1):
        unique_variant = (
                self.product_id.product_variant_ids[0]
                if len(self.product_id.product_variant_ids) == 1
                else False
        )
        vals = []
        if unique_variant:
            vals += [(5,)]
            if self.product_id.pack_line_ids:
                for comp in self.product_id.pack_line_ids.flatProductHierarchy(default_qty=q):
                    vals.append((0, 0, {
                                            "product_id": comp.get('product_id').id,
                                            "planned_qty": comp.get('quantity'),
                                        }))
        return vals

    @api.onchange("product_id")
    def onchange_product_id(self):
        res = {'value':{'task_product_ids':[]}, 'domain':{}}
        if self.product_id:
            vals = self.loadProducts_change_pqty(self.product_id, self.quantity)
            res['value']['task_product_ids'] = vals
            res['value']['product_id'] = self.product_id.id
        return res

    @api.onchange("quantity")
    def onchange_quantity(self):
        res = {'value':{'task_product_ids':[]}, 'domain':{}}
        if self.product_id:
            vals = self.loadProducts_change_pqty(self.product_id, self.quantity)
            res['value']['task_product_ids'] = vals
            res['value']['product_id'] = self.product_id.id
        return res
