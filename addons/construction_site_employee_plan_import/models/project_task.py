from odoo import models
from odoo.exceptions import ValidationError


class ProjectTask(models.Model):
    _inherit = "project.task"
    
    def _agregate(self, line):
        vals = super(ProjectTask, self)._agregate(line)
        hours_qty = cost = 0
        if len(line) < 4:
            return vals
        if len(line)>=4:
            hours_qty = float(line[3]) #nr ore
        if len(line)>=5:
            cost = float(line[4]) #cost/ora
        vals.update({
            'hours_qty': hours_qty,
            'hours_cost': cost,
            })
        return vals
    
    def import_xls(self):
        data = super(ProjectTask, self).import_xls()
        colect = {}
        for d in data:
            if d.get('hours_qty', 0) == 0:
                continue
            if d.get('task_id') not in colect:
                colect[d.get('task_id')] = {}
            if d.get('hours_cost', 0) not in colect[d.get('task_id')]:
                colect[d.get('task_id')][d.get('hours_cost')] = 0
            colect[d.get('task_id')][d.get('hours_cost')] += d.get('hours_qty')
        
        for task_id, hours_dict in colect.items():
            task_id.task_employee_ids = [
                (0, 0, {
                    'planned_hours': hours,
                    'hourly_cost': cost,
                    })
                for cost, hours in hours_dict.items()
                ]
        return data