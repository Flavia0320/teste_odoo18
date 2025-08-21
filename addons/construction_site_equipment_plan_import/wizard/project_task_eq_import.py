from odoo import models
from odoo.exceptions import ValidationError


class ProjectTaskProductImport(models.TransientModel):
    _inherit = "project.task.product.import"
    
    def _rowDict(self, cols=None):
        cols = super()._rowDict(cols)
        if not cols.get('ehours_qty'):
            cols['ehours_qty'] = 5
        if not cols.get('ehours_cost'):
            cols['ehours_cost'] = 6
        return cols

    def _agregate(self, st, rowx):
        cols = self._rowDict()
        vals = super(ProjectTaskProductImport, self)._agregate(st, row)
        hours_qty = st.cell(row, cols.get('ehours_qty', 5)).value #nr ore
        cost = st.cell(row, cols.get('ehours_cost', 6)).value #cost/ora
        vals.update({
            'ehours_qty': hours_qty or 0,
            'ehours_cost': cost or 0,
            })
        return vals
    
    def execute(self):
        data = super(ProjectTaskProductImport, self).execute()
        colect = {}
        for d in data:
            if d.get('ehours_qty', 0) == 0:
                continue
            if d.get('task_id') not in colect:
                colect[d.get('task_id')] = {}
            if d.get('ehours_cost', 0) not in colect[d.get('task_id')]:
                colect[d.get('task_id')][d.get('ehours_cost')] = 0
            colect[d.get('task_id')][d.get('ehours_cost')] += d.get('ehours_qty')
        
        for task_id, hours_dict in colect.items():
            task_id.task_employee_ids = [
                (0, 0, {
                    'planned_hours': hours,
                    'price_unit': cost,
                    })
                for cost, hours in hours_dict.items()
                ]
        return data
