# Copyright 2023 Dakai SOFT SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.misc import clean_context


class Task(models.Model):
    _inherit = "project.task"
    _order = "priority desc, sequence, id desc"

    is_construction_site = fields.Boolean(
        related="project_id.is_construction_site", store=True
    )
    need_procurement = fields.Boolean(compute="_compute_procurement_need")
    need_consume = fields.Boolean(compute="_compute_consume_need")
    need_invoice = fields.Boolean(_compute="_compute_consume_need")

    task_product_ids = fields.One2many(
        "project.task.product", "task_id", string="Products", copy=False,
    )
    # Model links
    purchase_order_line_ids = fields.One2many(
        "purchase.order.line", "task_id", string="Purchase Order Lines"
    )
    stock_move_ids = fields.One2many("stock.move", "task_id", string="Stock Moves")
    account_move_line_ids = fields.One2many(
        "account.move.line", "task_id", string="Move Lines"
    )

    currency_id = fields.Many2one("res.currency", related="project_id.pricelist_id.currency_id", store=True)
    
    cost_increment = fields.Float(default=0.0)
    material_planned_cost = fields.Monetary(
        compute="_compute_material_cost", string="Planned Material Cost", store=True
    )
    material_cost = fields.Monetary(
        compute="_compute_material_cost", string="Material Cost", store=True
    )
    extra_cost = fields.Monetary(
        compute="_compute_extra_cost",
        string="Extra Cost",
        store=True
        # Facturi furnizor fara purchase order
    )
    task_cost = fields.Monetary(
        compute="_compute_total_cost", string="Task Cost", store=True
    )
    cost = fields.Monetary(
        compute="_compute_total_cost", string="Total Cost", store=True
    )
    task_planned_cost = fields.Monetary(
        compute="_compute_total_cost", string="Task Planned Cost", store=True
    )
    planned_cost = fields.Monetary(
        compute="_compute_total_cost", string="Planned Cost", store=True
    )
    total_sale_price_consummed = fields.Monetary(compute="_computeTotalSale")

    planned_revenue = fields.Monetary(compute="_compute_distribute_revenu", string=_("Task Subtotal Value"), store=True)
    revenue = fields.Monetary(compute="_compute_distribute_revenu", string="Revenue", store=True)
    profit = fields.Monetary(compute="_compute_profit", string="Profit", store=True)

    #Procurement
    procurement_count = fields.Integer(compute="_compute_count_docs")
    delivery_count = fields.Integer(compute="_compute_count_docs")
    purchase_count = fields.Integer(compute="_purchase_count")
    invoice_count = fields.Integer(compute="_invoice_count")

    warehouse_id = fields.Many2one("stock.warehouse", _("Warehouse"), related="project_id.warehouse_id")
    location_id = fields.Many2one('stock.location', string=_("Task Location"))
    current_location_id = fields.Many2one('stock.location', compute="_compute_current_location")
    
    site_management = fields.Boolean()
    planned_extra_cost = fields.Monetary()

    def convert_price(self, price, from_currency, date=fields.Date.today()):
        if self.currency_id != from_currency:
            return from_currency._convert(
                price,
                self.currency_id,
                self.company_id or self.env.company,
                date,
            )
        return price

    def _compute_current_location(self):
        for s in self:
            s.current_location_id = s.get_current_location()

    def _compute_count_docs(self):
        stock_move_obj = self.env['stock.move']
        procurement_obj = self.env['project.site.procurement']
        for s in self:
            s.delivery_count = len(stock_move_obj.search([('task_id', '=', s.id)]).mapped('picking_id'))
            s.procurement_count = len(procurement_obj.search([('task_id', '=', s.id)]))
            
    def __getParentRevenu(self, planned=False):
        if planned:
            return (self.parent_id or self).planned_revenue
        return (self.parent_id or self).revenu
            
    def __cost_factor(self, planned=False):
        if planned:
            parent_cost = self.planned_cost
            if self.parent_id:
                parent_cost = sum(self.parent_id.child_ids.mapped("planned_cost"))
            current_cost = self.planned_cost
        else:
            parent_cost = self.cost
            if self.parent_id:
                parent_cost = sum(self.parent_id.child_ids.mapped("cost"))
            current_cost = self.cost
        if not parent_cost:
            return 1
        return abs(current_cost)/abs(parent_cost)
    
    def __getRealRevenu(self):
        if self.parent_id:
            return self.parent_id.revenue
        revenue = 0
        for aml in self.account_move_line_ids.filtered(lambda x: x.account_id.account_type == 'income'):
            revenue += self.convert_price(aml.price_subtotal, aml.currency_id, aml.date)
        return revenue
        
    
    def __getPlannedRevenu(self):
        if self.parent_id:
            return self.parent_id.planned_revenue
        price_revenu = self.planned_revenue
        sol = self.sale_line_id
        if sol:
            price_revenu = self.convert_price(sol.price_subtotal, sol.currency_id, sol.create_date)
        return price_revenu
            
    @api.depends('parent_id.child_ids', 'parent_id.revenue', 'planned_revenue', 'parent_id.planned_revenue', 'cost', 'planned_cost', 'account_move_line_ids')
    def _compute_distribute_revenu(self):
        for s in self:
            #prv = s.__getPlannedRevenu()
            cost_factor = s.__cost_factor()
            planned_cost_factor = s.__cost_factor(planned=True)
            revenue = cost_factor and s.__getRealRevenu()*cost_factor or 0
            #s.revenue = revenue
            planned_revenue = planned_cost_factor and s.__getPlannedRevenu() * planned_cost_factor or 0
            #s.planned_revenue = planned_revenue
            value_to_update = {'revenue':revenue, 'planned_revenue': planned_revenue}
            s.write(value_to_update)
            #self._cr.execute("UPDATE project_task set revenu=%s, planned_revenu=%s where id=%s", (revenue, planned_revenue, s.id))
            
    # @api.depends('child_ids', 'extra_cost','material_cost','extra_cost') #add planned & current cost on task + child_task
    # def _compute_unify_cost(self):
    #     for s in self:
    #         s.planned_cost = sum(s.child_ids.mapped("planned_cost")) + s.material_cost()
    #         s.cost = sum(s.child_ids.mapped("cost")) + s.material_cost + s.extra_cost

    def _purchase_count(self):
        for s in self:
            s.purchase_count = len(s.purchase_order_line_ids.mapped('order_id'))

    def _invoice_count(self):
        for s in self:
            s.invoice_count = len(s.account_move_line_ids.mapped('move_id'))

    def _compute_planned_consumed_materials(self):
        material_planned_cost = material_cost = 0
        # TODO: De verificat daca trebuie sa vina si costurile dupa copii
        # for subtask in self.child_ids:
        #     material_planned_cost += subtask.material_planned_cost
        #     material_cost += subtask.material_cost
        for product in self.task_product_ids:
            material_planned_cost += product.material_planned_cost
            material_cost += product.material_cost
        return material_planned_cost, material_cost


    @api.depends("task_product_ids.material_cost")
    def _compute_material_cost(self):
        for task in self:
            material_planned_cost, material_cost = task._compute_planned_consumed_materials()
            task.material_planned_cost = material_planned_cost
            task.material_cost = material_cost

    @api.depends("account_move_line_ids")
    def _compute_extra_cost(self):
        for task in self:
            extra_cost = 0
            for subtask in task.child_ids:
                extra_cost += subtask.extra_cost
            for aml in task.account_move_line_ids:
                if aml.move_id.move_type in ("in_invoice", "in_refund", "in_receipt") and aml.tax_base_amount == 0 and aml.product_id.id not in task.task_product_ids.mapped('product_id').ids:
                    extra_cost -= aml.debit
            task.extra_cost = extra_cost

    def _sumCost(self):
        return self.material_cost + self.extra_cost

    def _sumPlannedCost(self):
        planned_cost = sum(self.mapped("material_planned_cost"))
        return planned_cost + self.planned_extra_cost

    def _incrementCostTask(self):
        for s in self:
            s.cost_increment += 0.0001
            if s.parent_id:
                s.parent_id._incrementCostTask()

        #if tasks:
        #    for task in tasks:
        #        task.cost_increment += 0.0001
        #else:


    @api.depends('material_planned_cost', 'child_ids', 'child_ids.cost', 'child_ids.planned_cost', 'cost_increment')
    def _compute_total_cost(self):
        for task in self:
            
            task_planend_cost = task._sumPlannedCost()
            task.task_planned_cost = task_planend_cost
            
            task_cost = task._sumCost()
            task.task_cost = task_cost
            
            planned_cost = task_planend_cost
            cost = task_cost

            # TODO: De verificat daca trebuie sa vina si costurile dupa copii
            planned_cost += sum(task.child_ids.mapped("planned_cost"))
            cost += sum(task.child_ids.mapped("cost"))
            
            task.cost = cost
            task.planned_cost = planned_cost

    def _sumSalePrices(self, dType=None):
        if dType=='planned':
            return sum(self.task_product_ids.mapped('material_planned_cost'))
        elif dType=='reported':
            return sum(self.task_product_ids.mapped('price_total_received'))
        elif dType=='consummed':
            return sum(self.task_product_ids.mapped('price_total_consummed'))
        return 0

    def _computeTotalSale(self):
        for s in self:
            #s.total_sale_price_planned = s._sumSalePrices('planned')
            #s.total_sale_price_received = s._sumSalePrices('reported')
            s.total_sale_price_consummed = s._sumSalePrices('consummed')

    @api.depends("cost", "revenue")
    def _compute_profit(self):
        for task in self:
            profit = 0
            # TODO: de verificat logica de profit
            # for subtask in task.child_ids:
            #     profit += subtask.profit
            profit += task.revenue + task.cost
            task.profit = profit

    @api.depends('task_product_ids', 'task_product_ids.requested_qty')
    def _compute_procurement_need(self):
        def compare(line):
            requested_qty = max(line.planned_qty, line.requested_qty)
            qty = requested_qty - line.received_qty - line.product_qty_in_progress
            # if line.product_id:
            #     requested_qty = line.requested_qty or line.planned_qty
            #     if line.received_qty > 0:
            #         qty = requested_qty - line.received_qty
            #     elif requested_qty>0:
            #         qty = requested_qty
            return qty

        for task in self:
            if task.project_id.is_construction_site:
                task.need_procurement = sum(
                    task.task_product_ids.with_context(
                        warehouse=task.project_id.warehouse_id.ids
                        ).mapped(
                            lambda x: compare(x))
                        ) > 0
            else:
                task.need_procurement = False

    def _compute_consume_need(self):
        for task in self:
            location_id = task.current_location_id
            s = 0
            for i in task.task_product_ids:
                s += i.received_qty - i.consumed_qty
            task.need_consume = s > 0
            list_picking_inv = [p.state == 'done' for p in task.task_product_ids.moveAchieved().mapped("picking_id")]
            task.need_invoice = any(list_picking_inv)

    #TODO: delete.
    def _get_report_base_filename(self, docType):
        dtype = ""
        if docType=='deviz':
            dtype= _("Fisa Deviz")
        elif docType=='decont':
            dtype= _("Fisa Decont")
        return "-".join([dtype, self.name])

    #============ Separam functiile private de functiile publice.
    def consumeProducts(self, force=False):
        for task in self:
            consume_loc = task.project_id.consume_loc_id
            rule = self.env['stock.rule'].search([
                ('location_dest_id','=',consume_loc.id),
                ('location_src_id','child_of', task.project_id.warehouse_id.lot_stock_id.id),
                #('picking_type_id','=',task.project_id.warehouse_id.l10n_ro_consume_type_id.id)
                ], limit=1)
            rute_id = rule and rule.route_id or None
            if not rute_id:
                raise UserError(_("No route Consume [project_task/consumeProducts]"))
            #migrare16 - aici am inlocuit user_id dupa task cu manager proiect
            replenishment = self.env['procurement.group'].create({
                    'partner_id': task.project_id.user_id.partner_id.id,
                    'task_id': task.id
                })
            proc = []
            for pline in task.task_product_ids:
                rest = pline.received_qty - pline.consumed_qty
                qty = force and rest or min([pline.tmp_consume, rest])
                proc.append(pline.launch_replenishment(qty, replenishment, route=rute_id, location=consume_loc))
                pline.tmp_consume = 0
            self.env['procurement.group'].with_context(clean_context(self.env.context)).run(proc)

    # def calcTaskValue(self):
    #     if self.parent_id:
    #         self.parent_id.calcTaskValue()
    #     elif self.planned_revenue and self.child_ids:
    #         self.calcChildsTaskValue()
    #
    # def calcChildsTaskValue(self):
    #     total_child_costs = sum(self.child_ids.mapped('cost'))
    #     for child in self.child_ids:
    #         if total_child_costs == 0:
    #             child.with_context(calc_subtotal_value=True).planned_revenue = self.planned_revenue/len(self.child_ids)
    #         else:
    #             child.with_context(calc_subtotal_value=True).planned_revenue = child.cost/total_child_costs*self.planned_revenue
    #         if child.planned_revenue and child.child_ids:
    #             child.calcChildsTaskValue()

    def get_current_location(self):
        if self.location_id:
            return self.location_id.id
        if self.parent_id:
            return self.parent_id.get_current_location()
        return self.project_id.warehouse_id.lot_stock_id.id

    def action_view_delivery(self):
        pickings = self.env['stock.move'].search([('task_id', '=', self.id)]).mapped('picking_id')
        action = self.env["ir.actions.actions"]._for_xml_id("stock.action_picking_tree_all")

        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif pickings:
            form_view = [(self.env.ref('stock.view_picking_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = pickings.id
        # Prepare the context.
        picking_id = pickings.filtered(lambda l: l.picking_type_id.code == 'outgoing')
        if picking_id:
            picking_id = picking_id[0]
        else:
            picking_id = pickings[0]
        action['context'] = dict(self._context, default_partner_id=self.partner_id.id,
                                 default_picking_type_id=picking_id.picking_type_id.id, default_origin=self.name,
                                 default_group_id=picking_id.group_id.id)
        return action

    def action_view_purchases(self):
        purchases = self.purchase_order_line_ids.mapped('order_id')
        action = self.env["ir.actions.actions"]._for_xml_id("purchase.purchase_rfq")
        if len(purchases) > 1:
            action['domain'] = [('id', 'in', purchases.ids)]
        elif purchases:
            form_view = [(self.env.ref('purchase.purchase_order_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = purchases.id
        return action

    def action_view_invoices(self):
        invoices = self.account_move_line_ids.mapped('move_id')
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif invoices:
            form_view = [(self.env.ref('account.view_move_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = invoices.id
        return action


    def create_manual_bill(self):
        ctx = self.env.context.copy()
        ctx.update({
            'default_ref': self.project_id.partner_id.name,
            'default_move_type': 'in_invoice',
            'default_invoice_origin': self.name,
            'default_invoice_user_id': self.project_id.user_id.id,
            'default_currency_id': self.project_id.pricelist_id.currency_id.id,
            'default_payment_reference': self.project_id.name,
            'default_project_id': self.project_id.id,
            'default_task_id': self.id,
        })
        return {
            "name": "Create Project Bill",
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "view_mode": "form",
            "target": "current",
            "context": ctx,
        }
        
    #Pastram functiile suprascrise din ORM in partea de jos.
    # @api.model_create_multi
    # def create(self, vals_list):
    #     tasks = super().create(vals_list)
    #     for task in tasks:
    #         task.calcTaskValue()
    #     return tasks

    def write(self, vals):
        memo_task_dates = {s.id: s.planned_date_begin.strftime('%Y-%m-%d') for s in self if s.planned_date_begin}
        res = super().write(vals)
        # if not self.env.context.get('calc_subtotal_value'):
        #     for task in self:
        #         task.calcTaskValue()
        task_dates = [s.planned_date_begin.strftime('%Y-%m-%d') == memo_task_dates.get(s.id, None) for s in self if s.planned_date_begin]
        if res and vals.get('planned_date_begin', None) and task_dates:
            self.mapped("task_product_ids")._move_planned_date(vals.get('planned_date_begin'))
        return res
    
    def action_open_procurement(self):
        action = self.env['project.site.procurement'].action_open_procurement([('task_id','=',self.id)])
        return action
    
    def action_open_reports_balance(self):
        action = self.env.ref('construction_site.project_task_revenu_report_action').read()[0]
        action.update({'domain':[('project_id','=',self.id), '|', ('parent_id','=',self.id), ('task_id','=',self.id)]})
        return action

    def action_open_reports_material(self):
        action = self.env.ref('construction_site.project_task_product_report_action').read()[0]
        action.update({'domain':[('project_id','=',self.id), '|', ('parent_id','=',self.id), ('task_id','=',self.id)]})
        return action

    def action_open_reports_moves(self):
        action = self.env.ref('construction_site.project_task_move_report_action').read()[0]
        action.update({'domain':[('project_id','=',self.id), '|', ('parent_id','=',self.id), ('task_id','=',self.id)]})
        return action

    def action_open_reports(self):
        pass

    def action_open_decont(self):
        action = self.env.ref('construction_site.project_site_invoice_action2').read()[0]
        action.update({
            'domain':[('task_id','=',self.id)],
            })
        return action
        
