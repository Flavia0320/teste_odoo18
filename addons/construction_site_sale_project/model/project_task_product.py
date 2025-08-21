from odoo import api, fields, models, _


class ProjectTaskProduct(models.Model):
    _inherit = "project.task.product"

    order_line_id = fields.Many2one("sale.order.line", string=_("Sale Line"))

    @api.depends(
        'pricelist_id',
        'received_qty',
        'planned_qty',
        'consumed_qty'
    )
    def _compute_prices(self):
        for s in self:
            if s.order_line_id:
                punit = s.order_line_id.price_unit
                s.price_unit = punit
                s.price_total_planned = punit * s.planned_qty