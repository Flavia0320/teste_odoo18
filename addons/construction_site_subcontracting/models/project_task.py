# Copyright 2022 Dakai SOFT SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/16.0/legal/licenses/licenses.html#).

from odoo import api, fields, models, _
import base64

from odoo.exceptions import UserError


class Task(models.Model):
    _inherit = "project.task"

    task_subcontracting_ids = fields.One2many(
        "project.task.subcontracting", "task_id", string="Subcontracting", copy=True,
    )

    contract_id = fields.Many2one("smart.contract", _("Contract"))
    purchase_order_created = fields.Boolean("Purchase Order Created", default=False)
    subcontracting_planned_cost = fields.Monetary(
        compute="_compute_subcontracting_cost", string="Subcontracting Planned Cost", store=True
    )
    subcontracting_cost = fields.Monetary(
        compute="_compute_subcontracting_cost", string="Subcontracting Cost", store=True
    )

    def _compute_planned_subcontracting_cost(self):
        subcontracting_planned_cost = subcontracting_cost = 0
        # TODO: De verificat daca trebuie sa vina si costurile dupa copii
        for subcontracting in self.task_subcontracting_ids:
            subcontracting_planned_cost += subcontracting.planned_cost
            subcontracting_cost += subcontracting.effective_cost
        return subcontracting_planned_cost, subcontracting_cost

    @api.depends("task_subcontracting_ids", "task_subcontracting_ids.planned_cost", "task_subcontracting_ids.effective_cost")
    def _compute_subcontracting_cost(self):
        for task in self:
            subcontracting_planned_cost,subcontracting_cost = task._compute_planned_subcontracting_cost()
            task.subcontracting_planned_cost = subcontracting_planned_cost
            task.subcontracting_cost = subcontracting_cost
            task._compute_total_cost()

    def _sumCost(self):
        cost = super(Task, self)._sumCost()
        cost += self.subcontracting_cost
        return cost

    def _sumPlannedCost(self):
        planned_cost = super(Task, self)._sumPlannedCost()
        planned_cost += self.subcontracting_planned_cost
        return planned_cost

    def _sumSalePrices(self, dType=None):
        res = super(Task, self)._sumSalePrices(dType=dType)
        if dType == 'planned':
            res += sum(self.task_subcontracting_ids.mapped('planned_cost'))
        elif dType == 'reported':
            res += sum(self.task_subcontracting_ids.mapped('effective_cost'))
        return res

    def action_create_contract(self):
        total_effective_cost = sum(abs(line.effective_cost) for line in self.task_subcontracting_ids)
        values = {
            'partner_id': self.partner_id.id,
            'document_type': 'contract',
            'valoare_fixa': total_effective_cost,
        }
        self.contract_id = self.env['smart.contract'].create(values)
        self.action_add_attachment()

    def action_open_smart_contract(self):
        self.ensure_one()
        action = self.env.ref('smart_contract.action_smart_contract').read()[0]
        action['domain'] = [('id', '=', self.contract_id.id)]
        return action


    def action_add_attachment(self):
        pdf = self.env['ir.actions.report']._render_qweb_pdf("smart_contract.smart_contract_pdf_report", self.contract_id.id)
        b64_pdf = base64.b64encode(pdf[0])
        name = self.contract_id.name
        return self.env['ir.attachment'].create({
            'name': f'{name}.pdf',
            'type': 'binary',
            'datas': b64_pdf,
            'store_fname': name,
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/x-pdf'
        })

    def create_purchase_order(self):
        if not self.contract_id:
            self.action_create_contract()

        PurchaseOrder = self.env["purchase.order"]
        PurchaseOrderLine = self.env["purchase.order.line"]

        for task in self:
            if not task.task_subcontracting_ids:
                raise UserError(_("No subcontracting lines found for this task."))

            purchase_order = PurchaseOrder.create({
                "partner_id": task.partner_id.id,
                "date_order": fields.Date.today(),
                "origin": task.name,
                "contract_id": task.contract_id.id,
            })

            for line in task.task_subcontracting_ids:
                PurchaseOrderLine.create({
                    "task_id": task.id,
                    "order_id": purchase_order.id,
                    "product_id": line.product_id.id,
                    "name": line.product_id.display_name or "Subcontracting Line",
                    "product_qty": line.planned_qty,
                    "price_unit": line.planned_cost_unit,
                    "date_planned": fields.Date.today(),
                    "task_subcontracting_ids": [(6, 0, [line.id])]
                })
            task.purchase_order_created = True  # Set the flag after creating PO
            return {
                "type": "ir.actions.act_window",
                "res_model": "purchase.order",
                "view_mode": "form",
                "res_id": purchase_order.id,
            }

    def action_open_reports_subcontracting(self):
        action = self.env.ref('construction_site_subcontracting.project_task_subcontracting_report_action').read()[0]
        action.update({'domain': [('project_id', '=', self.id), '|', ('parent_id', '=', self.id), ('task_id', '=', self.id)]})
        return action