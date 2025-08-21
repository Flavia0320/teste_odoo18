# Copyright 2022 Dakai SOFT SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).

from odoo import api, fields, models


class Task(models.Model):
    _inherit = "project.task"

    task_equipment_ids = fields.One2many(
        "project.task.equipment", "task_id", string="Equipments", copy=True,
    )
    equipment_planned_cost = fields.Float(
        compute="_compute_equipment_cost", string="Equipment Planned Cost", store=True
    )
    equipment_cost = fields.Float(
        compute="_compute_equipment_cost", string="Equipment Cost", store=True
    )

    def _compute_planned_cost_equipment(self):
        equipment_planned_cost = equipment_cost = 0
        # TODO: De verificat daca trebuie sa vina si costurile dupa copii
        # for subtask in self.child_ids:
        #     equipment_planned_cost += subtask.equipment_planned_cost
        #     equipment_cost += subtask.equipment_cost
        for equipment in self.task_equipment_ids:
            equipment_planned_cost += equipment.planned_cost
            equipment_cost += equipment.effective_cost
        return equipment_planned_cost, equipment_cost


    @api.depends("task_equipment_ids", "task_equipment_ids.planned_cost", "task_equipment_ids.effective_cost")
    def _compute_equipment_cost(self):
        for task in self:
            equipment_planned_cost, equipment_cost = task._compute_planned_cost_equipment()
            task.equipment_planned_cost = equipment_planned_cost
            task.equipment_cost = equipment_cost
            task._compute_total_cost()

    def _sumCost(self):
        cost = super(Task, self)._sumCost()
        cost += self.equipment_cost
        return cost
    
    def _sumPlannedCost(self):
        planned_cost = super(Task, self)._sumPlannedCost()
        planned_cost += self.equipment_planned_cost
        return planned_cost

    def _sumSalePrices(self, dType=None):
        res = super(Task, self)._sumSalePrices(dType=dType)
        if dType=='planned':
            res += sum(self.task_equipment_ids.mapped('price_total_planned'))
        elif dType=='reported':
            res += sum(self.task_equipment_ids.mapped('price_total_received'))
        return res

    def action_open_reports_equipment(self):
        action = self.env.ref('construction_site_equipment.project_task_equipment_report_action').read()[0]
        action.update({'domain': [('project_id', '=', self.id), '|', ('parent_id', '=', self.id), ('task_id', '=', self.id)]})
        return action