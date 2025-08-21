from odoo import models, fields, _

class SaleOrderConstructionName(models.TransientModel):

    _name = 'sale.order.construction.name'

    wiz_id = fields.Many2one('sale.order.construction.name')
    order_ids = fields.Many2many("sale.order")
    construction_order_id = fields.Many2one("sale.order")
    obiectiv = fields.Char("Denumire Proiect Santier")
    construction_order_ids = fields.One2many("sale.order.construction.name", "wiz_id")
    email = fields.Boolean()

    def execute(self):
        if self.construction_order_id:
            self.construction_order_id.obiectiv = self.obiectiv
        for construction_order_id in self.construction_order_ids:
            construction_order_id.construction_order_id.obiectiv = construction_order_id.obiectiv
        if self.email:
            return self.order_ids.action_quotation_send()
        return self.order_ids.action_confirm()