from odoo import api, fields, models, _


class TaskSubcontracting(models.Model):
    _name = "project.task.subcontracting"
    _description = "Subcontracting linked to Site Work"
    _order = "sequence,id"

    ord = fields.Integer(compute="_genOrd")
    sequence = fields.Integer()
    task_id = fields.Many2one("project.task", string=_("Task"), ondelete="cascade")
    product_id = fields.Many2one("product.product", string=_("Product"), copy=False, required=True)

    planned_cost_unit = fields.Integer(string="Cost planificat unitar")
    effective_cost_unit = fields.Integer(string="Cost efectiv unitar")
    planned_qty = fields.Float(string=_("Planned Qty"))
    effective_qty = fields.Float(string=_("Effective Qty"))

    planned_cost = fields.Float(
        string=_("Planned Cost"), compute="_compute_planned_cost", store=True
    )
    effective_cost = fields.Float(
        string=_("Effective Cost"), compute="_compute_effective_cost", store=True
    )
    currency_id = fields.Many2one(related="task_id.currency_id")
    analytic_account_line_id = fields.Many2one('account.analytic.line', ondelete="cascade")
    purchase_order_line_id = fields.Many2one("purchase.order.line", _("Task subcontracting"), ondelete="cascade")

    def _genOrd(self):
        def Convert(tup, di):
            for a, b in tup:
                di.setdefault(a, []).append(b)
            return di

        task_ids = self.filtered(lambda x: isinstance(x.id, int)).mapped("task_id.id")
        dids = {}
        if task_ids:
            self._cr.execute(
                "SELECT id, task_id from project_task_subcontracting where task_id in %s order by sequence,id",
                (tuple(self.mapped("task_id.id")),)
            )
            ids = [(task_id, i) for i, task_id in self._cr.fetchall()]
            Convert(ids, dids)
        for s in self:
            if dids.get(s.task_id.id, None):
                s.ord = dids.get(s.task_id.id).index(s.id) + 1
            else:
                s.ord = 0

    def convert_price(self, price, from_currency, date=fields.Date.today()):
        if self.currency_id != from_currency:
            return from_currency._convert(
                price,
                self.currency_id,
                self.task_id.company_id or self.env.company,
                date,
            )
        return price

    @api.depends("planned_qty", "planned_cost_unit")
    def _compute_planned_cost(self):
        for task_subcontracting in self:
            task_subcontracting.planned_cost = (
                    -1 * task_subcontracting.planned_qty * task_subcontracting.planned_cost_unit
            )

    @api.depends("purchase_order_line_id.qty_invoiced")
    def _compute_effective_cost(self):
        for task_subcontracting in self:
            qty = task_subcontracting.purchase_order_line_id.qty_invoiced
            cost = -1 * task_subcontracting.purchase_order_line_id.price_unit * qty
            task_subcontracting.effective_cost = cost
            task_subcontracting.effective_qty = qty
            task_subcontracting.effective_cost_unit = cost / qty if qty else 0.0

    def syncAnalyticLines(self):
        self_sudo = self.sudo()
        ptime_id = self_sudo.env.ref('sale_timesheet.time_product_product_template')
        for subcontracting in self:
            analytic_account_line_id = subcontracting.analytic_account_line_id
            if not analytic_account_line_id:
                subcontracting.analytic_account_line_id = analytic_account_line_id.create({
                    'name': _('Subcontracting %s') % subcontracting.product_id.name,
                    'unit_amount': subcontracting.effective_qty,
                    'product_uom_id': ptime_id.id,
                    'amount': subcontracting.effective_cost,
                    'account_id': subcontracting.task_id.analytic_account_id.id
                })
            else:
                analytic_account_line_id.write({
                    'unit_amount': subcontracting.effective_qty,
                    'amount': subcontracting.effective_cost,
                })

    def _incrementParentTask(self, tasks=None):
        if tasks:
            tasks._incrementCostTask()
        else:
            self.mapped("task_id")._incrementCostTask()

    @api.model_create_multi
    def create(self, values):
        res = super(TaskSubcontracting, self).create(values)
        res.syncAnalyticLines()
        res._incrementParentTask()
        return res

    def write(self, values):
        res = super(TaskSubcontracting, self).write(values)
        self.syncAnalyticLines()
        self._incrementParentTask()
        return res

    def unlink(self):
        tasks = self.mapped("task_id")
        return super(TaskSubcontracting, self).unlink()
        self._incrementParentTask(tasks=tasks)
