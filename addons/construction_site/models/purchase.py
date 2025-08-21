# Copyright 2023 Dakai SOFT SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    construction_project_count = fields.Integer(compute="_project_construction")
    construction_project_ids = fields.Many2many(comodel_name="project.project", compute="_project_construction")
    project_id = fields.Many2one("project.project", domain=[('is_construction_site', '=', True)])

    @api.onchange('project_id')
    def onclick_project_id(self):
        if self.project_id:
            self.order_line.project_id = self.project_id.id

    def _project_construction(self):
        for s in self:
            project_ids = s.order_line.mapped("task_product_ids.project_id.id")
            s.construction_project_count = len(project_ids)
            s.construction_project_ids = [(6, 0, project_ids)]

    def action_view_projects(self):
        act = self.env.ref('project.open_view_project_all_config').read()[0]
        act.update({
            'domain': [('id','in',self.construction_project_ids.ids)]
            })
        return act
    
    def message_post(self, *args, **kwargs):
        res = super(PurchaseOrder, self).message_post(*args, **kwargs)
        if res and self.order_line.mapped("procurement_ids") and not self._context.get('prevent_recursion', None):
            self.with_context(prevent_recursion=True).order_line.mapped("procurement_ids").message_post(*args, **kwargs)
        return res
    
    # TODO: de verificat functionalitatea.
    #
    # def copy(self, values=None):
    #     if self.mapped("order_line.task_product_ids"):
    #         raise UserError(_("Duplicate this purchase order is forbiden"))
    #     return super(PurchaseOrder, self).copy(values)
    
    def button_confirm(self):
        self.mapped('order_line')._pushProductToTask()
        return super(PurchaseOrder, self).button_confirm()

    def _get_destination_location(self):
        location_id = super(PurchaseOrder, self)._get_destination_location()
        task_locations = []
        for line in self.order_line.filtered(lambda x: x.task_id != False and x.product_id.type in ['product', 'consu']):
            if line.task_id.location_id or line.task_id.project_id.warehouse_id.lot_stock_id:
                location = line.task_id.location_id and line.task_id.location_id.id or line.task_id.project_id.warehouse_id.lot_stock_id.id
                if task_locations and location in task_locations:
                    raise ValidationError(_("You cannot have 2 different project locations on same purchase!"))
                return location
        return location_id


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    project_id = fields.Many2one("project.project", string="Project", index=True)
    task_id = fields.Many2one("project.task", string="Task", index=True)
    task_product_ids = fields.One2many("project.task.product.purchase", "purchase_order_line_id", string=_("Task Product"))
    
    procurement_ids = fields.Many2many("project.site.procurement", 
                                       relation="procurement_purchase_objs", 
                                       column2="procurement_id", 
                                       column1="purchase_order_line_id", 
                                       string="Purchase Line")

    @api.model
    def _prepare_purchase_order_line_from_procurement(self, product_id, product_qty, product_uom, company_id, values, po):
        res = super(PurchaseOrderLine, self)._prepare_purchase_order_line_from_procurement(product_id, product_qty, product_uom, company_id, values, po)
        if values.get('task_product_id', None):
            task_product = values.get('task_product_id')
            res['task_product_ids'] = [(0, 0, {
                'task_product_id':task_product.id,
                'planned_qty': task_product.planned_qty,
                'warehouse_id': po.picking_type_id.warehouse_id.id,
                })]
            res['task_id'] = task_product.task_id.id
            res['procurement_ids'] = values.get('procurement_ids')
            res['analytic_distribution'] = {
                task_product.task_id.project_id.analytic_account_id.id: 100
            }
        return res

    def _prepare_account_move_line(self, move=False):
        res = super(PurchaseOrderLine, self)._prepare_account_move_line(move)
        res.update({
            'task_id': self.task_id.id
        })
        return res

    def prepare_invoice(self):
        invoice_vals = super(PurchaseOrderLine, self).prepare_invoice()
        invoice_vals['task_product_ids'] = [(6, 0, self.task_product_ids.mapped("task_product_id").ids)],
        return invoice_vals

    @api.onchange("task_id")
    def _onchange_task_id(self):
        if self.task_id:
            self.analytic_distribution = {
                self.task_id.project_id.analytic_account_id.id: 100
            }
            task_product = self.task_id.task_product_ids.filtered(lambda x: x.product_id == self.product_id)
            if task_product:
                self.task_product_ids = [(0, 0, {'task_product_id':task_product.id, 'planned_qty': task_product.planned_qty})]
                #[(4, _tp_id) for _tp_id in task_product.ids]
        else:
            self.analytic_distribution = False


    def _prepare_stock_move_vals(self, picking, price_unit, product_uom_qty, product_uom):
        res = super(PurchaseOrderLine, self)._prepare_stock_move_vals(picking, price_unit, product_uom_qty, product_uom)
        if self.order_id.picking_type_id.warehouse_id in self.task_product_ids.mapped("task_product_id.task_id.project_id.warehouse_id"):
            add_task_rel = {
                'task_id': self.task_id.id if self.task_id  else None,
                'task_product_ids': [(6, 0, self.task_product_ids.mapped("task_product_id").ids)],
                }
            res.update(add_task_rel)
        return res

    def _prepare_stock_moves(self, picking):
        res = super(PurchaseOrderLine, self)._prepare_stock_moves(picking)
        out_res = []
        for values in res:
            lines = self.task_product_ids.filtered(lambda x: x.purchase_order_line_id.id == values.get('purchase_line_id', None))
            if lines:
                value = values.copy()
                value.update({
                    'task_id': lines[0].task_id.id,
                    'task_product_ids': [(4, line.task_product_id.id) for line in lines],
                    'procurement_ids': [(6, 0, self.procurement_ids.ids)],
                    })
                out_res.append(value)
            else:
                out_res.append(values)
        return out_res

    def _distribute_qty(self, field_name):
        qty = getattr(self, field_name)
        res = []
        for task_prod in self.task_product_ids:
            convert_qty = task_prod.task_product_id.uom_id._compute_quantity(qty, self.product_uom)
            reserved_qty = convert_qty
            res.append((task_prod.id, reserved_qty))
            qty -= self.product_uom._compute_quantity(reserved_qty, task_prod.task_product_id.uom_id)
            if qty <= 0:
                break
        return res
    
    @api.model_create_multi
    def create(self, vals_list):
        res = super(PurchaseOrderLine, self).create(vals_list)
        if res.mapped('task_id') and any([order.state=='purchase' for order in res.mapped("order_id")]):
            res.filtered(lambda x: x.order_id.state=='purchase')._pushProductToTask()
        return res
    
    def write(self, value):
        res = super(PurchaseOrderLine, self).write(value)
        if value.get('task_id') and any([order.state=='purchase' for order in self.mapped("order_id")]):
            res_self = self.filtered(lambda x: x.order_id.state=='purchase')._pushProductToTask()
            res_self._pushProductToTask()
        return res
    
    def _pushProductToTask(self):
        proc = None
        def __create_procurement(line):
            procObj = self.env['project.site.procurement']
            existing = procObj.search([('purchase_line_ids','in', line.ids)])
            if existing:
                return existing
            task = line.task_id
            project = line.task_id.project_id
            route_ids = procObj._getRoutes(project)
            route_id = procObj._getDefaultRoute(route_ids)
            proc_type = 'in_site'
            if line.order_id.picking_type_id.default_location_dest_id.warehouse_id == project.supply_warehouse_id:
                proc_type = 'in_supply_warehouse'
            seq = procObj._getSequence()
            return procObj.create({
                'task_id': task.id,
                'name': seq.next_by_id(),
                'project_id': project.id,
                'warehouse_id': line.order_id.picking_type_id.default_location_dest_id.warehouse_id.id,
                'route_id':route_id,
                'route_type':'buy',
                'procurement_type': proc_type,
                'state': 'done',
                })
        for s in self:
            if s.task_id and not s.task_product_ids and s.product_id.type=='product':
                if not proc:
                    proc = __create_procurement(s)
                #create_project_task_product
                project_task_product = self.env['project.task.product'].create(
                    {
                        'sequence': 1000,
                        'company_id': s.order_id.company_id.id,
                        'task_id': s.task_id.id,
                        'product_id': s.product_id.id,
                        'planned_qty': s.product_qty,
                        'planned_date': s.order_id.date_planned,
                        'material_planned_cost': s.price_subtotal,
                    })
                #create_project_task_product_purchase_id
                project_task_product_purchase = self.env['project.task.product.purchase'].create({
                    'task_product_id': project_task_product.id,
                    'purchase_order_line_id': s.id,
                    'planned_qty': s.product_qty,
                    'warehouse_id': s.task_id.project_id.warehouse_id.id,
                    'company_id': s.order_id.company_id.id
                })
                #procurement_line
                procurement_line = self.env['project.site.procurement.product'].create({
                    'product_id': s.product_id.id,
                    'task_id': s.task_id.id,
                    'project_id': s.task_id.project_id.id,
                    'task_product_id': project_task_product.id,
                    'to_procure_qty': s.product_qty,
                    'procurement_id': proc.id
                })
                s.write({
                    #'task_product_ids': [(0, 0, {
                    #        'product_id': s.product_id.id,
                    #        'planned_qty': s.product_qty,
                    #        'purchase_line_ids': [(4, s.id)],
                    #        'task_id': s.task_id.id,
                    #    })],
                    'project_id': s.task_id.project_id.id,
                    'procurement_ids': [(4, proc.id)]
                    })
