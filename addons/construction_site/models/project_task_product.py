# Copyright 2023 Dakai SOFT SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.misc import clean_context
from odoo.models import _logger
from datetime import datetime


class ProjectTaskProduct(models.Model):
    _inherit = ["portal.mixin", "mail.thread.cc", "mail.activity.mixin", "rating.mixin"]
    _name = "project.task.product"
    _description = "Plan products on tasks"
    _rec_name = "product_id"
    _order = "sequence,id"

    ord = fields.Integer(compute="_genOrd")
    sequence = fields.Integer()
    company_id = fields.Many2one("res.company", default=lambda x: x.env.user.company_id.id)
    task_id = fields.Many2one("project.task", _("Task"), required=True, ondelete="cascade")
    project_id = fields.Many2one("project.project", "Project", related="task_id.project_id")
    partner_id = fields.Many2one("res.partner", string=_("Customer"), related="project_id.partner_id")
    commercial_partner_id = fields.Many2one(related="task_id.partner_id")
    product_id = fields.Many2one("product.product", string=_("Product"), copy=False, required=True)
    
    category_id = fields.Many2one("product.category", "Product Category", related="product_id.categ_id")
    change_planned_cost = fields.Boolean(related="category_id.change_planned_cost")
    
    uom_id = fields.Many2one("uom.uom", string="Uom", related="product_id.uom_id", store=True)
    purchase_line_ids = fields.One2many("project.task.product.purchase", "task_product_id", string=_("Purchase Order line"))
    stock_move_ids = fields.Many2many(comodel_name="stock.move",
                                        relation="stock_move_task_product_rel",
                                        column1="task_product_id",
                                        column2="move_id",
                                        string=_("Stock Move"))

    stock_receive_ids = fields.Many2many(
        comodel_name="stock.move", compute="_compute_moves",
        relation="stock_move_task_product_rel_receive",
        column1="task_product_id",
        column2="move_id",
        store=True
        )
    stock_consume_ids = fields.Many2many(
        comodel_name="stock.move", compute="_compute_moves",
        relation="stock_move_task_product_rel_consume",
        column1="task_product_id",
        column2="move_id",
        store=True
        )
    stock_outer_ids = fields.Many2many(
        comodel_name="stock.move", compute="_compute_moves",
        relation="stock_move_task_product_rel_outer",
        column1="task_product_id",
        column2="move_id",
        store=True
        )

    account_move_line_ids = fields.One2many("account.move.line", "task_product_id")
    synthetic_account_move_line_ids = fields.Many2many(
        comodel_name="account.move.line",
        relation="project_task_account_line_synthetic",
        column1="project_task_product_id",
        column2="account_move_line_id",
        )

    planned_qty = fields.Float(string=_("Planned Qty"), copy=False,)
    planned_date = fields.Date(string=_("Planned Receive Date"))

    procurment_product_line_ids = fields.One2many('project.site.procurement.product', "task_product_id")
    #TODO deleted field
    #to_procure_qty = fields.Float(string=_("Non-Planned Qty"))
    requested_state = fields.Selection([
        ('hipo_request', 'In plan'),
        ('fix_request', 'Fit plan'),
        ('hiper_request', 'Above plan'),
        ('no_plan', 'Non planned'),
        ], string=_("Requested State"), compute="_compute_requested_state")
    requested_qty = fields.Float(string=_("Requested Qty"), compute="_compute_requested_qty", store=True)

    purchase_qty = fields.Float(
        string=_("Ordered Quantity"), compute="_compute_in_quantities", store=True
    )
    billed_qty = fields.Float(
        string=_("Billed Quantity"), compute="_compute_in_quantities", store=True
    )
    received_qty = fields.Float(
        string=_("Received Quantity"), compute="_compute_in_quantities", store=True
    )
    purchase_qty_in_progress = fields.Float(string=("Purchase Qty"), compute="_get_quantity_in_progress")
    product_qty_in_progress = fields.Float(string=("Progress Qty"), compute="_get_quantity_in_progress")

    consumed_qty = fields.Float(
        string=_("Consumed Quantity"), compute="_compute_out_quantities", store=True
    )
    tmp_consume = fields.Float()
    to_invoice_qty = fields.Float(string=_("To Invoice Quantity"), compute="_compute_inv_quantities")
    invoiced_qty = fields.Float(
        string=_("Invoiced Quantity"), compute="_compute_inv_quantities"
    )



    currency_id = fields.Many2one("res.currency", related="pricelist_id.currency_id")
    pricelist_id = fields.Many2one("product.pricelist", related="task_id.project_id.pricelist_id")


    # Costs and profit
    material_planned_cost = fields.Float(
        compute="_compute_material_planned_cost", string=_("Planned Cost"), store=True
    )
    material_cost = fields.Float(
        compute="_compute_material_cost", string=_("Material Cost"), store=True
    )
    material_purchase_cost = fields.Float(
        compute="_compute_account_cost", string=_("Purchase Cost"), store=True
    )
    material_billed = fields.Float(
        compute="_compute_account_cost", string=_("Billed Cost"), store=True
    )
    price_total_consummed = fields.Monetary(compute="_compute_prices", store=True)
    price_total_invoiced = fields.Monetary(compute="_compute_prices", store=True)

    @api.depends('requested_qty')
    def _compute_requested_state(self):
        #DOCS: posible variants
        # """
        # ('hipo_request', 'In plan'),
        # ('fix_request', 'Fit plan'),
        # ('hiper_request', 'Above plan'),
        # ('no_plan', 'Non planned'),
        # """
        for s in self:
            state = None
            if s.requested_qty < s.planned_qty:
                state = 'hipo_request'
            elif s.requested_qty == s.planned_qty:
                state = 'fix_request'
            elif s.requested_qty > s.planned_qty:
                state = 'hiper_request'
            elif s.requested_qty > 0 and s.planned_qty == 0:
                state = 'no_plan'
            s.requested_state = state

    def _genOrd(self):
        def Convert(tup, di):
            for a, b in tup:
                di.setdefault(a, []).append(b)
            return di
        task_ids = self.filtered(lambda x: isinstance(x.id, int)).mapped("task_id.id")
        dids = {}
        if task_ids:
            self._cr.execute(
                "SELECT id, task_id from project_task_product where task_id in %s order by sequence,id",
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
        if self.currency_id != from_currency:
            return from_currency._convert(
                price,
                self.currency_id,
                self.company_id or self.env.company,
                date,
            )
        return price

    @api.depends(
        'pricelist_id',
        'received_qty',
        'planned_qty',
        'consumed_qty'
        )
    def _compute_prices(self):
        for s in self:
            if s.received_qty and s.received_qty != 0:
                if s.consumed_qty:
                    s.price_total_consummed = s.material_cost / s.received_qty * s.consumed_qty
                if s.invoiced_qty:
                    s.price_total_invoiced = s.material_cost / s.received_qty * s.invoiced_qty
            else:
                s.price_total_consummed = 0.0
                s.price_total_invoiced = 0.0

    @api.depends("product_id", "planned_qty")
    def _compute_material_planned_cost(self):
        for line in self:
            line.material_planned_cost = (
                (-1) * self.convert_price(
                    line.product_id.standard_price,
                    line.product_id.currency_id,
                    line.task_id.create_date
                    ) * line.planned_qty
            )

    @api.depends(
        "stock_receive_ids",
        "stock_receive_ids.stock_valuation_layer_ids.value",
    )
    def _compute_material_cost(self):
        for line in self:
            cost = 0
            for svl in line.stock_receive_ids.mapped("stock_valuation_layer_ids"):
                at_date = svl.l10n_ro_invoice_id and svl.l10n_ro_invoice_id.invoice_date or svl.stock_move_id.picking_id.date
                cost += self.convert_price(svl.value, svl.currency_id, at_date)
            line.material_cost = (-1) * cost

    @api.depends(
        "purchase_line_ids.state",
        "purchase_line_ids.planned_qty",
        "purchase_line_ids",
        "purchase_line_ids.purchase_order_line_id.product_uom_qty",
        "purchase_line_ids.purchase_order_line_id.qty_received",
        "purchase_line_ids.purchase_order_line_id.qty_invoiced",
        "stock_move_ids.state"
    )
    def _compute_in_quantities(self):
        for line in self:
            line.purchase_qty = sum(line.purchase_line_ids.mapped("received_qty"))
            line.received_qty = sum(line.stock_receive_ids.mapped("product_uom_qty"))
            line.billed_qty = sum(line.purchase_line_ids.mapped("billed_qty"))

    @api.depends(
        "procurment_product_line_ids",
        "procurment_product_line_ids.procurement_id.state",
        "procurment_product_line_ids.to_procure_qty"
    )
    def _compute_requested_qty(self):
        for line in self:
            line.requested_qty = sum(
                line.procurment_product_line_ids.filtered(
                    lambda x: x.procurement_id.state != 'cancel'
                    ).mapped('to_procure_qty')
                )

    @api.depends(
        "stock_move_ids",
        "stock_move_ids.product_uom_qty",
        # "stock_move_ids.quantity_done",
        "stock_move_ids.state",
    )
    def _compute_out_quantities(self):
        consume = self.mapped("task_id.project_id.consume_loc_id")
        for line in self:
            line.consumed_qty = sum(line.stock_move_ids.filtered(
                                            lambda x: x.state in ['done'] and x.location_dest_id in consume
                                        ).mapped("quantity")
                                    ) - sum(line.stock_move_ids.filtered(
                                            lambda x: x.state in ['done'] and x.location_id in consume
                                        ).mapped("quantity")
                                    )

    @api.depends(
        "account_move_line_ids",
        "account_move_line_ids.quantity",
        "account_move_line_ids.parent_state",
        "synthetic_account_move_line_ids",
        "synthetic_account_move_line_ids.quantity",
        "synthetic_account_move_line_ids.parent_state",
    )
    def _compute_inv_quantities(self):
        for line in self:
            qty_do = qty = 0.0
            aline = self.env['account.move.line']
            aline |= line.account_move_line_ids
            aline |= line.synthetic_account_move_line_ids
            for inv_line in aline:
                if inv_line.move_id.state in ["cancel"]:
                    continue
                if inv_line.move_id.move_type == "out_invoice":
                    qty += inv_line.product_uom_id._compute_quantity(
                        inv_line.quantity, line.uom_id
                    )
                elif inv_line.move_id.move_type == "out_refund":
                    qty -= inv_line.product_uom_id._compute_quantity(
                        inv_line.quantity, line.uom_id
                    )
            line.to_invoice_qty = line.qtyAchieved() - qty
            line.invoiced_qty = qty

    @api.depends(
        "stock_outer_ids",
        "stock_outer_ids.stock_valuation_layer_ids",
        "purchase_qty",
        "billed_qty",
    )
    def _compute_account_cost(self):
        for line in self:
            purchase_cost = 0
            for svl in line.stock_outer_ids.mapped("stock_valuation_layer_ids"):
                at_date = svl.l10n_ro_invoice_id and svl.l10n_ro_invoice_id.invoice_date or svl.stock_move_id.picking_id.date
                purchase_cost += self.convert_price(svl.value, svl.currency_id,at_date)
            line.material_purchase_cost = (-1) * purchase_cost
            line.material_billed = (line.purchase_qty>0 and line.billed_qty>0) and line.material_purchase_cost/line.purchase_qty*line.billed_qty or 0
            # purchase_line_ids
            # mat = rev = 0.0
            #
            # aline = self.env['account.move.line']
            # aline |= line.account_move_line_ids
            # aline |= line.synthetic_account_move_line_ids
            #
            # for inv_line in aline:
            #     if inv_line.move_id.state not in ["cancel"]:
            #         continue
            #     if inv_line.move_id.move_type == "out_invoice":
            #         rev += inv_line.balance
            #     elif inv_line.move_id.move_type == "out_refund":
            #         rev -= inv_line.balance
            #     elif inv_line.move_id.move_type == "in_invoice":
            #         mat += inv_line.balance
            #     elif inv_line.move_id.move_type == "in_refund":
            #         mat -= inv_line.balance
            # line.material_billed = (-1) * mat

    
    @api.depends(
        'stock_move_ids',
        "stock_move_ids.product_uom_qty",
        # "stock_move_ids.quantity_done",
        "stock_move_ids.state",
        'task_id'
    )
    def _compute_moves(self):
        for s in self:
            stock = s.stock_move_ids
            wh = s.task_id.project_id.warehouse_id
            spl = s.task_id.project_id.supply_warehouse_id
            s.stock_receive_ids = [(6, 0, stock.filtered(
                lambda x: x.state=='done' and x.location_dest_id.warehouse_id==wh and x.location_dest_id!=s.task_id.project_id.consume_loc_id
                ).ids)]
            s.stock_consume_ids = [(6, 0, stock.filtered(
                lambda x: x.state=='done' and x.location_dest_id==s.task_id.project_id.consume_loc_id
                ).ids)]
            stock_outer_ids = stock.filtered(
                lambda x: x.state=='done' and x.location_dest_id.warehouse_id==spl
                ).ids + stock.filtered(
                lambda x: x.state=='done' and x.location_id.id==self.env.ref('stock.stock_location_suppliers').id
                ).ids
            s.stock_outer_ids = [(6, 0, stock_outer_ids)]

    @api.depends('task_id.project_id.warehouse_id', 'product_id', 'purchase_line_ids.purchase_qty', 'purchase_line_ids.received_qty')
    def _get_quantity_in_progress(self):
        for pline in self:
            pid = pline.product_id.id

            swh = pline.task_id.project_id.supply_warehouse_id
            wh = pline.task_id.project_id.warehouse_id

            dict_qty = wh and pline.mapped('product_id').with_context(warehouse=wh.ids, task=pline.task_id.id)._compute_quantities_dict(None, None, None) or {}

            pline.product_qty_in_progress = (dict_qty.get(pid, None) and dict_qty[pid]['incoming_qty'] or 0)
            pline.purchase_qty_in_progress = sum(pline.purchase_line_ids.mapped('planned_qty')) - sum(pline.purchase_line_ids.mapped('received_qty'))
            
    def _move_planned_date(self, task_date):
        return self.filtered(lambda x: x.product_qty_in_progress == 0).write({'planned_date': task_date})
                
    def default_get(self, fieldList):
        res = super(ProjectTaskProduct, self).default_get(fieldList)
        task_date = None
        if res.get('task_id'):
            task_date = self.env['project.task'].browse(res.get('task_id')).planned_date_begin
        res['planned_date'] = task_date or fields.Date().today()
        return res

    def moveBySetting(self, strType):
        moves = self.env['stock.move']
        if strType=='consume':
            moves |= self.stock_consume_ids
        elif strType in ['received', 'planned']:
            moves |= self.stock_receive_ids
        if self._context.get('invoice_id'):
            moves = moves.filtered(lambda x: x.picking_id.construction_invoice_id.id == self._context.get('invoice_id'))
        return moves

    def moveAchieved(self):
        moves = self.env['stock.move']
        for task_product in self:
            moves |= task_product.moveBySetting(task_product.task_id.project_id.invoice_method)
        return moves

    def qtyBySetting(self, strType):
        qty = 0
        if strType=='consume':
            qty = self.consumed_qty
        elif strType=='received':
            qty = self.received_qty
        elif strType=='planned':
            qty = self.planned_qty
        return qty

    def qtyAchieved(self):
        return self.qtyBySetting(self.task_id.project_id.invoice_method)

    def launch_replenishment(self, qty, replenishment, wh=None, route=None, location=None, planned_date=None):
        uom_reference = self.product_id.uom_id

        quantity = self.uom_id._compute_quantity(qty, uom_reference)
        if not any([wh, location]):
            raise UserError(_("No warehouse or stock location [project_task_product/launch_replenishment]"))
        try:
            values = {
                    'warehouse_id': wh,
                    'date_planned': planned_date or datetime.now().date(),
                    'group_id': replenishment,
                    'task_id': self.task_id.id,
                    'task_product_ids': [(4, self.id)],
                    'task_product_id': self,
                }
            if 'procurement_source_id' in self._context:
                #get Intem source from procurement
                proc_line = self.procurment_product_line_ids.filtered(lambda x: x.procurement_id.id == self._context.get('procurement_source_id'))
                values.update({
                    'procurement_ids': [(4, self._context.get('procurement_source_id'))],
                    'supplierinfo_name': proc_line and proc_line.supplier_id or None
                    })
            if route:
                values.update({
                    'route_ids': route,
                    })
            procurement = self.env['procurement.group'].Procurement(
                    self.product_id,
                    quantity,
                    uom_reference,
                    location or wh.lot_stock_id,  # Location
                    "%s / %s" % (self.task_id.project_id.name,self.task_id.name),
                    "%s / %s" % (self.task_id.project_id.name,self.task_id.name),
                    self.company_id,
                    values  # Values
                )
        except UserError as error:
            _logger.info(error)
        else:
            return procurement

    def runProcurement(self, route=None, wh=None):
        task = self.task_id
        project = task.project_id
        if not wh:
            wh = project.warehouse_id
        index = project.warehouse_id==wh and 1 or 0
        procurements = []

        replenishment = self.env['procurement.group'].create({
            'partner_id': project.user_id.partner_id.id,
            'task_id': self.task_id.id
        })

        for product_line in self.filtered(lambda x: x.compute_purchase_move()[index] > 0 ):
            proc = product_line.launch_replenishment(
                product_line.compute_purchase_move()[index], 
                replenishment, 
                wh, 
                route=route, 
                planned_date=product_line.planned_date
                )
            if proc:
                procurements.append(proc)
        self.env['procurement.group'].with_context(clean_context(self.env.context)).run(procurements)

    def compute_purchase_move(self):
        x = y = 0
        if len(self)==0:
            return [x, y]
        for s in self:
            qty = s.received_qty + s.product_qty_in_progress
            if s.purchase_qty_in_progress <= qty:
                qty -= s.purchase_qty_in_progress
                project = s.task_id.project_id
                if not self.project_id.company_id.purchase_force_qty:
                    wh_ids = [project.supply_warehouse_id.id]
                    qty_dict = s.product_id.with_context(warehouse=wh_ids, task=s.task_id.id)._compute_quantities_dict(None, None, None)
                    qty -= qty_dict[s.product_id.id]['qty_available']
                x += qty > 0 and qty or 0
            y += s.requested_qty - s.product_qty_in_progress - s.received_qty
        return [x, y] # [QTY to Purchase, QTY to move]


    def listAchievedTransfers(self):
        return self.moveAchieved()

    def action_show_details(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }
    
    def _incrementParentTask(self, tasks=None):
        if tasks:
            tasks._incrementCostTask()
        else:
            self.mapped("task_id")._incrementCostTask()
    
    @api.model_create_multi
    def create(self, values):
        res = super(ProjectTaskProduct, self).create(values)
        res._incrementParentTask()
        return res
    
    def write(self, values):
        res = super(ProjectTaskProduct, self).write(values)
        self._incrementParentTask()
        return res
    
    def unlink(self):
        self._incrementParentTask()
        return super(ProjectTaskProduct, self).unlink()
        

    # def unlink(self):
    #     block_unlink = self.filtered(lambda x: x.product_qty_in_progress >0)
    #     if block_unlink:
    #         raise UserError(_("You can't delete lines with Quantity in Progress on products\n%s") % "\n".join(block_unlink.mapped('product_id.name')))
    #     return super().unlink()
