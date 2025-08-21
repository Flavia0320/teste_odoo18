from odoo import api, fields, models, _, SUPERUSER_ID
from collections import defaultdict
from dateutil.relativedelta import relativedelta
from itertools import groupby


class ProcurementGroup(models.Model):
    _inherit = "procurement.group"

    task_id = fields.Many2one("project.task", _("Task"))


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _get_stock_move_values(self, product_id, product_qty, product_uom, location_id, name, origin, company_id, values):
        res = super(StockRule, self)._get_stock_move_values(product_id, product_qty, product_uom, location_id, name, origin, company_id, values)
        if values.get('task_id', None):
            res['task_id'] = values.get('task_id')
        task_product_ids = []
        ### de continuat
        if values.get('task_product_id', None):
            if isinstance(values.get('task_product_id'), int):
                task_product_ids += [(4, values.get('task_product_id'))]
        if values.get('task_product_ids', None):
            task_product_ids += values.get('task_product_ids')
        if task_product_ids:
            res['task_product_ids'] = len(task_product_ids)>1 and list(set(task_product_ids)) or task_product_ids
        return res

    def _update_purchase_order_line(self, product_id, product_qty, product_uom, company_id, values, line):
        res = super(StockRule, self)._update_purchase_order_line(product_id, product_qty, product_uom, company_id, values, line)
        if values.get('task_product_id', None):
            task_product = values.get('task_product_id')
            res['task_product_ids'] = [(0, 0, {
                'task_product_id':task_product.id,
                'planned_qty': task_product.planned_qty,
                'warehouse_id': line.order_id.picking_type_id.warehouse_id.id,
                })]
            res['task_id'] = task_product.task_id.id
        return res

    def _push_prepare_move_copy_values(self, move_to_copy, new_date):
        res = super(StockRule, self)._push_prepare_move_copy_values(move_to_copy, new_date)
        if move_to_copy.task_id:
            res['task_id'] = move_to_copy.task_id.id
        if move_to_copy.task_product_ids:
            res['task_product_ids'] = [(6, 0, move_to_copy.task_product_ids.ids)]
        return res

    def _postUpdateConstructionSite(self, res, origins, values):
        return res

    def _prepare_purchase_order(self, company_id, origins, values):
        res = super()._prepare_purchase_order(company_id, origins, values)
        res = self._postUpdateConstructionSite(res, origins, values)
        return res
