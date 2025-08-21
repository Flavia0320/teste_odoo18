from odoo import api, fields, models


class HrDepartment(models.Model):
    _inherit = "hr.department"
    
    hourly_cost = fields.Float(compute="_compute_costHour", store=True)
    
    @api.depends('member_ids.hourly_cost')
    def _compute_costHour(self):
        for s in self:
            employees = s.member_ids
            s.hourly_cost = employees and sum(employees.mapped("hourly_cost"))/len(employees) or 0