
from odoo import api, fields, models

class TaskEmployees(models.Model):
    _inherit = "project.task.employee"
    
    procurement_line_id = fields.Many2one('project.site.procurement.product', ondelete="cascade")
    
    @api.depends("planned_hours", "hourly_cost", "procurement_line_id")
    def _compute_planned_cost(self):
        for task_empl in self:
            hcost = task_empl.hourly_cost
            if task_empl.procurement_line_id.hourly_cost > 0:
                hcost = task_empl.procurement_line_id.hourly_cost
            task_empl.planned_cost = -1 * task_empl.planned_hours * hcost