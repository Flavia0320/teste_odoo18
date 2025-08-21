# Copyright 2022 Dakai SOFT SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).

from odoo import api, fields, models


class Task(models.Model):
    _inherit = "project.task"

    task_employee_ids = fields.One2many(
        "project.task.employee", "task_id", string="Employees", copy=True,
    )
    employee_planned_cost = fields.Monetary(
        compute="_compute_employee_cost", string="Employee Planned Cost", store=True
    )
    employee_cost = fields.Monetary(
        compute="_compute_employee_cost", string="Employee Cost", store=True
    )
    hourly_cost = fields.Float()

    def _compute_planned_employee_cost(self):
        employee_planned_cost = employee_cost = 0
        # TODO: De verificat daca trebuie sa vina si costurile dupa copii
        # for subtask in self.child_ids:
        #     employee_planned_cost += subtask.employee_planned_cost
        #     employee_cost += subtask.employee_cost
        for employee in self.task_employee_ids:
            employee_planned_cost += employee.planned_cost
            employee_cost += employee.effective_cost
        return employee_planned_cost, employee_cost

    @api.depends("task_employee_ids", "task_employee_ids.planned_cost", "task_employee_ids.effective_cost")
    def _compute_employee_cost(self):
        for task in self:
            employee_planned_cost, employee_cost = task._compute_planned_employee_cost()
            task.employee_planned_cost = employee_planned_cost
            task.employee_cost = employee_cost
            task._compute_total_cost()

    def _sumCost(self):
        cost = super(Task, self)._sumCost()
        cost += self.employee_cost
        return cost

    def _sumPlannedCost(self):
        planned_cost = super(Task, self)._sumPlannedCost()
        planned_cost += self.employee_planned_cost
        return planned_cost
    
    def _sumSalePrices(self, dType=None):
        res = super(Task, self)._sumSalePrices(dType=dType)
        if dType=='planned':
            res += sum(self.task_employee_ids.mapped('planned_cost'))
        elif dType=='reported':
            res += sum(self.task_employee_ids.mapped('effective_cost'))
        return res

    def employee_attendance_wizard(self):
        ctx = self.env.context.copy()
        ctx.update({
            'default_task_id': self.id,
        })
        return {
            "name": "Employee Attendance Wizard",
            "type": "ir.actions.act_window",
            "res_model": "project.task.employee.attendance",
            "view_mode": "form",
            "target": "new",
            "context": ctx,
        }

    def action_open_reports_employees(self):
        action = self.env.ref('construction_site_employee.project_task_employee_report_action').read()[0]
        action.update({'domain': [('project_id', '=', self.id), '|', ('parent_id', '=', self.id), ('task_id', '=', self.id)]})
        return action