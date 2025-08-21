from odoo import api, fields, models, _

class TaskEquipment(models.Model):
    _name = "project.task.equipment"
    _description = "Equipments linked to Site Work"
    _order = "sequence,id"

    ord = fields.Integer(compute="_genOrd")
    sequence = fields.Integer()
    task_id = fields.Many2one("project.task", string=_("Task"), ondelete="cascade")
    equipment_id = fields.Many2one(
        "maintenance.equipment", string=_("Equipment"), copy=True,
    )
    hour_cost = fields.Float(compute="_compute_hour_cost", store=True)

    planned_date = fields.Date(string=_("Planned Date"), copy=True,)
    planned_hours = fields.Float(string=_("Planned Hours"), copy=True,)

    effective_hours = fields.Float(string=_("Effective Hours"), copy=True,)
    invoiced_hours = fields.Integer()
    planned_cost = fields.Float(
        string=_("Planned Cost"), compute="_compute_planned_cost", store=True
    )
    effective_cost = fields.Float(
        string=_("Effective Cost"), compute="_compute_effective_cost", store=True
    )
    currency_id = fields.Many2one(related="task_id.currency_id")
    price_unit = fields.Monetary(compute="_compute_prices", store=True)
    price_total_planned = fields.Monetary(compute="_compute_prices", store=True)
    price_total_received = fields.Monetary(compute="_compute_prices", store=True)
    analytic_account_line_id = fields.Many2one('account.analytic.line', ondelete="cascade")

    def _genOrd(self):
        def Convert(tup, di):
            for a, b in tup:
                di.setdefault(a, []).append(b)
            return di

        task_ids = self.filtered(lambda x: isinstance(x.id, int)).mapped("task_id.id")
        dids = {}
        if task_ids:
            self._cr.execute(
                "SELECT id, task_id from project_task_equipment where task_id in %s order by sequence,id",
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

    @api.depends("planned_hours", "hour_cost")
    def _compute_planned_cost(self):
        for task_equip in self:
            task_equip.planned_cost = (
                -1 * task_equip.planned_hours * task_equip.hour_cost
            )

    @api.depends("effective_hours", "hour_cost")
    def _compute_effective_cost(self):
        for task_equip in self:
            task_equip.effective_cost = (
                -1 * task_equip.effective_hours * task_equip.hour_cost
            )

    @api.depends("equipment_id", "equipment_id.cost")
    def _compute_hour_cost(self):
        for s in self:
            s.hour_cost = s.convert_price(s.equipment_id.cost, s.equipment_id.currency_id, s.task_id.create_date)

    @api.depends(
        'equipment_id.sale_hour_price',
        'hour_cost',
        'effective_hours',
        'planned_hours'
        )
    def _compute_prices(self):
        for s in self:
            punit = s.convert_price(s.equipment_id.sale_hour_price or s.hour_cost, s.equipment_id.currency_id, s.task_id.create_date)
            s.price_unit = punit
            s.price_total_planned = punit * s.planned_hours
            s.price_total_received = punit * s.effective_hours

    def syncAnalyticLines(self):
        self_sudo = self.sudo()
        ptime_id = self_sudo.env.ref('sale_timesheet.time_product_product_template')
        for equipment in self:
            analytic_account_line_id = equipment.analytic_account_line_id
            if not analytic_account_line_id:
                equipment.analytic_account_line_id = analytic_account_line_id.create({
                    'name': _('Equipment %s') % equipment.equipment_id.name,
                    'unit_amount': equipment.effective_hours,
                    'product_uom_id': ptime_id.id,
                    'amount': equipment.effective_cost,
                    'account_id': equipment.task_id.analytic_account_id.id
                })
            else:
                analytic_account_line_id.write({
                    'unit_amount': equipment.effective_hours,
                    'amount': equipment.effective_cost,
                })

    def _incrementParentTask(self, tasks=None):
        if tasks:
            tasks._incrementCostTask()
        else:
            self.mapped("task_id")._incrementCostTask()
                
    @api.model_create_multi
    def create(self, values):
        res = super(TaskEquipment, self).create(values)
        res.syncAnalyticLines()
        res._incrementParentTask()
        return res
    
    def write(self, values):
        res = super(TaskEquipment, self).write(values)
        self.syncAnalyticLines()
        self._incrementParentTask()
        return res
    
    def unlink(self):
        tasks = self.mapped("task_id")
        return super(TaskEquipment, self).unlink()
        self._incrementParentTask(tasks=tasks)
        
