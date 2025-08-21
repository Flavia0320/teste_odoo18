from odoo import models
from odoo.exceptions import ValidationError


class ProjectTask(models.Model):
    _inherit = "project.task"
    
    def _agregate(self, line):
        vals = super(ProjectTask, self)._agregate(line)
        hours_qty = cost = 0
        if len(line) < 6:
            return vals
        if len(line)>=6:
            hours_qty = float(line[5]) #nr ore
        if len(line)>=7:
            cost = float(line[6]) #cost/ora
        vals.update({
            'ehours_qty': hours_qty,
            'ehours_cost': cost,
            })
        return vals
    
    def import_xls(self):
        data = super(ProjectTask, self).import_xls()
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
            task_id.task_equipment_ids = [
                (0, 0, {
                    'planned_hours': hours,
                    'hour_cost': cost,
                    })
                for cost, hours in hours_dict.items()
                ]
        return data