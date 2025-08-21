# Copyright 2022 Dakai SOFT SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/16.0/legal/licenses/licenses.html#).

from odoo import api, fields, models


class Task(models.Model):
    _inherit = "project.task"

    task_transport_ids = fields.One2many(
        "project.task.transport", "task_id", string="Transports", copy=True,
    )
    transport_planned_cost = fields.Float(
        compute="_compute_transport_cost", string="Transport Planned Cost", store=True
    )
    transport_cost = fields.Float(
        compute="_compute_transport_cost", string="Transport Cost", store=True
    )

    @api.depends("task_transport_ids", "task_transport_ids.planned_cost", "task_transport_ids.effective_cost")
    def _compute_transport_cost(self):
        for task in self:
            transport_planned_cost = transport_cost = 0
            # TODO: De verificat daca trebuie sa vina si costurile dupa copii
            # for subtask in task.child_ids:
            #     transport_planned_cost += subtask.transport_planned_cost
            #     transport_cost += subtask.transport_cost
            for transport in task.task_transport_ids:
                transport_planned_cost += transport.planned_cost
                transport_cost += transport.effective_cost
            task.transport_planned_cost = transport_planned_cost
            task.transport_cost = transport_cost
            task._compute_total_cost()

    def _sumCost(self):
        cost = super(Task, self)._sumCost()
        cost += self.transport_cost
        return cost

    def _sumPlannedCost(self):
        planned_cost = super(Task, self)._sumPlannedCost()
        planned_cost += self.transport_planned_cost
        return planned_cost

    def _sumSalePrices(self, dType=None):
        res = super(Task, self)._sumSalePrices(dType=dType)
        if dType == 'planned':
            res += sum(self.task_transport_ids.mapped('price_total_planned'))
        elif dType == 'reported':
            res += sum(self.task_transport_ids.mapped('price_total_received'))
        return res

    def action_open_reports_transports(self):
        action = self.env.ref('construction_site_transport.project_task_transport_report_action').read()[0]
        action.update({'domain': [('project_id', '=', self.id), '|', ('parent_id', '=', self.id), ('task_id', '=', self.id)]})
        return action