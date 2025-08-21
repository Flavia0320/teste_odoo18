# Copyright 2022 Dakai SOFT SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).

from odoo import api, fields, models

class TaskEmployees(models.Model):
    _name = "project.task.employee"
    _description = "Employees linked to Site Work"
    _order = "sequence,id"

    ord = fields.Integer(compute="_genOrd")
    sequence = fields.Integer()
    task_id = fields.Many2one("project.task", string="Task", ondelete="cascade")
    employee_id = fields.Many2one("hr.employee", string="Employee", copy=False)
    hr_department_id = fields.Many2one("hr.department", string="Department", copy=False)
    currency_id = fields.Many2one(related="employee_id.currency_id")
    hourly_cost = fields.Monetary(compute="_compute_hourly_cost", store=True)

    planned_date = fields.Date(string="Planned Date", copy=False,)
    planned_hours = fields.Float(string="Planned Hours", copy=False,)
    planned_cost = fields.Float(
        string="Planned Cost", compute="_compute_planned_cost", store=True
    )

    effective_hours = fields.Float(
        string="Effective Hours", compute="_compute_effective_cost", store=True
    )
    effective_cost = fields.Float(
        string="Effective Cost", compute="_compute_effective_cost", store=True
    )
    manual_effective_hours = fields.Float(string="Global Hours")

    @api.onchange('hr_department_id')
    def _change_departament(self):
        if self.employee_id.department_id.id != self.hr_department_id.id:
            self.employee_id = False
        res = {
            'domain':{
                'employee_id': [],
                },
            }
        if self.hr_department_id:
            res = {
                'domain':{
                    'employee_id': [('department_id','=',self.hr_department_id.id)],
                    },
                }
        return res

    @api.onchange('employee_id')
    def _change_employee(self):
        if self.employee_id:
            self.hr_department_id = self.employee_id and self.employee_id.department_id.id or False


    def _genOrd(self):
        def Convert(tup, di):
            for a, b in tup:
                di.setdefault(a, []).append(b)
            return di

        task_ids = self.filtered(lambda x: isinstance(x.id, int)).mapped("task_id.id")
        dids = {}
        if task_ids:
            self._cr.execute(
                "SELECT id, task_id from project_task_employee where task_id in %s order by sequence,id",
                (tuple(task_ids),)
            )
            ids = [(task_id, i) for i, task_id in self._cr.fetchall()]
            Convert(ids, dids)
        for s in self:
            if dids.get(s.task_id.id, None):
                s.ord = dids.get(s.task_id.id).index(s.id) + 1
            else:
                s.ord = 0

    def convert_price(self, price, from_currency, date=fields.Date.today()):
        if self.task_id.currency_id != from_currency:
            return from_currency._convert(
                price,
                self.task_id.currency_id,
                self.task_id.company_id or self.env.company,
                date,
            )
        return price

    @api.depends("planned_hours", "hourly_cost")
    def _compute_planned_cost(self):
        for task_empl in self:
            task_empl.planned_cost = -1 * task_empl.planned_hours * task_empl.hourly_cost

    @api.depends(
        "employee_id",
        "employee_id.hourly_cost",
        "hr_department_id",
        "hr_department_id.hourly_cost",
        "task_id",
        "task_id.hourly_cost",
        "manual_effective_hours"
    )
    def _compute_hourly_cost(self):
        for task_empl in self:
            obj = task_empl.employee_id or task_empl.hr_department_id or task_empl.task_id
            hourly_cost = self.convert_price(obj.hourly_cost, obj.company_id.currency_id, task_empl.task_id.create_date)
            task_empl.hourly_cost = hourly_cost

    @api.depends("effective_hours", "hourly_cost", "task_id.timesheet_ids")
    def _compute_effective_cost(self):
        for task_empl in self:
            effective_hours = effective_cost = 0
            effective_hours += task_empl.manual_effective_hours
            effective_cost -= task_empl.hourly_cost * effective_hours
            if task_empl.employee_id:
                timesheets = task_empl.task_id.timesheet_ids.filtered(lambda x:
                    x.employee_id.id == task_empl.employee_id.id
                )
            elif task_empl.hr_department_id:
                timesheets = task_empl.task_id.timesheet_ids.filtered(lambda x:
                    x.employee_id.department_id.id == task_empl.hr_department_id.id
                )
            else:
                timesheets = task_empl.task_id.timesheet_ids.filtered(lambda x:
                    x.employee_id.id not in task_empl.task_id.mapped('task_employee_ids.employee_id').ids and
                    x.employee_id.department_id.id not in task_empl.task_id.mapped('task_employee_ids.hr_department_id').ids
                )
            for timesheet in timesheets:
                effective_hours += (
                    timesheet.unit_amount * timesheet.product_uom_id.factor_inv
                )
                effective_cost += self.convert_price(timesheet.amount, timesheet.currency_id, timesheet.date)
            # Ar trebui sa nu multiplicam. Altfel effective_hours va creste * 8.
            #effective_hours *= (
            #    task_empl.task_id.project_id.timesheet_encode_uom_id.factor
            #)
            task_empl.effective_hours = int(round(effective_hours))
            task_empl.effective_cost = effective_cost

    
    def _incrementParentTask(self, tasks=None):
        if tasks:
            tasks._incrementCostTask()
        else:
            self.mapped("task_id")._incrementCostTask()
            
    @api.model_create_multi
    def create(self, values):
        res = super(TaskEmployees, self).create(values)
        res._incrementParentTask()
        return res
    
    def write(self, values):
        res = super(TaskEmployees, self).write(values)
        self._incrementParentTask()
        return res
    
    def unlink(self):
        tasks = self.mapped("task_id")
        return super(TaskEmployees, self).unlink()
        self._incrementParentTask(tasks=tasks)
