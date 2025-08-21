from odoo import api, fields, models, _


class Task(models.Model):
    _inherit = "project.task"

    fixed = fields.Boolean()

    def _prepare_sale_price(self):
        price = super()._prepare_sale_price()
        return self.fixed and self.sale_price or price


class TaskProduct(models.Model):
    _inherit = "project.task.product"

    block_price_unit = fields.Boolean()

    def _geProductPriceUnit(self):
        punit = super()._geProductPriceUnit()
        if self.block_price_unit and self.price_unit > 0:
            punit = self.price_unit
        return punit
