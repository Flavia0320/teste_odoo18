from odoo import models, fields, api, Command

class ProjectTaskEmployeeAttendance(models.TransientModel):
    _name = "project.task.employee.attendance"
    _description = "Project Task Employee Attendance Wizard"

    task_id = fields.Many2one('project.task', string="Task")
    employee_id = fields.Many2one('hr.employee', string="Manager",
        domain="[('child_ids', '!=', False)]")
    employee_ids = fields.Many2many('hr.employee', string="Employees")
    consumed_hours = fields.Integer(string="Time Consumed")

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        self.employee_ids = [Command.set(self.employee_id.ids + self.employee_id.child_ids.ids)]

    def action_confirm(self):
        for employee in self.employee_ids:
            task_employee_id = self.task_id.task_employee_ids.filtered(lambda x: x.employee_id.id == employee.id)
            if task_employee_id:
                task_employee_id[0].manual_effective_hours = self.consumed_hours
            else:
                self.task_id.task_employee_ids = [Command.create({
                    'employee_id': employee.id,
                    'manual_effective_hours': self.consumed_hours
                })]