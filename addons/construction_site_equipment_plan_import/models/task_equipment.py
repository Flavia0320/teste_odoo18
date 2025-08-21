
from odoo import api, fields, models

class TaskEquipment(models.Model):
    _inherit = "project.task.equipment"
    
    procurement_line_id = fields.Many2one('project.site.procurement.product', ondelete="cascade")
    
    @api.depends("equipment_id", "equipment_id.cost", "procurement_line_id")
    def _compute_hour_cost(self):
        for s in self:
            cost = s.equipment_id.cost
            if self.procurement_line_id.e_hourly_cost:
                cost = self.procurement_line_id.e_hourly_cost
            s.hour_cost = s.convert_price(cost, s.equipment_id.currency_id, s.task_id.create_date)