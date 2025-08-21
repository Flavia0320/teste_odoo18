from odoo import api, fields, models
from odoo.tools.translate import _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime
from odoo.models import _logger
from odoo.tools.misc import clean_context

#class MakeProcurement(models.TransientModel):
class MakeProcurement(models.Model):
    _name = "project.site.procurement"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = _("Procurement Document")

    name = fields.Char(default='/')
    task_id = fields.Many2one("project.task", _("Parent Task"), ondelete="cascade")
    project_id = fields.Many2one("project.project", _("Project"))
    posible_wh_ids = fields.Many2many("stock.warehouse", compute="_compute_wh_ids")
    warehouse_id = fields.Many2one("stock.warehouse", string=_("Warehouse"))
    location_id = fields.Many2one("stock.location", related="warehouse_id.lot_stock_id", string=_("Warehouse"))
    task_product_ids = fields.One2many("project.site.procurement.product", "procurement_id", string=_("Replenishment tasks"))
    route_id = fields.Many2one("stock.route", _("Prefered Route"))
    route_type = fields.Selection([
                ('buy', 'Buy'),
                ('transfer', 'Transfer'),
                ])
    procurement_type = fields.Selection([
            ('in_site',_("To Construction Site")),
            ('in_supply_warehouse', _("To supply warehouse"))
            ], string=_("Procurement Type"), default='in_site', required=True)
    state = fields.Selection(
        [
            ('draft','Draft'),
            ('to-purchase','Procure'),
            ('done','Done'),
            ('cancel','Cancel'),
            ], default="draft")
    stock_move_ids = fields.Many2many("stock.move", relation="procurement_move_objs", column1="procurement_id", column2="stock_move_id", string="Stock Move")
    purchase_line_ids = fields.Many2many("purchase.order.line", 
                                         relation="procurement_purchase_objs", 
                                         column1="procurement_id", 
                                         column2="purchase_order_line_id", 
                                         string="Purchase Line")
    executed_date = fields.Datetime()
    stock_user_ids = fields.Many2many("res.users")

    stock_inform_user_ids = fields.Many2many("res.users", relation="stock_procurement_inform")
    permit_stock_inform_user_ids = fields.Many2many("res.users", related="project_id.stock_inform_user_ids")
    purchase_inform_user_ids = fields.Many2many("res.users", relation="purchase_procurement_inform")
    permit_purchase_inform_user_ids = fields.Many2many("res.users", related="project_id.purchase_inform_user_ids")
    
    purchase_count = fields.Integer(compute="_compute_documents")
    picking_count = fields.Integer(compute="_compute_documents")
    
    company_id = fields.Many2one("res.company", related="warehouse_id.company_id", store=True)
    tag_ids = fields.Many2many(comodel_name="project.tags")
    
    def name_get(self):
        values = dict(self._fields['procurement_type'].selection)
        res = {}
        for s in self:
            res[s.id] = f"{values[s.procurement_type]} => {s.route_id.display_name}/{s.task_id.display_name}"
        return res

    @api.depends('project_id')
    def _compute_wh_ids(self):
        for s in self:
            posible_wh_ids = []
            if s.project_id.warehouse_id:
                posible_wh_ids += [(4, s.project_id.warehouse_id.id)]
            if s.project_id.supply_warehouse_id:
                posible_wh_ids += [(4, s.project_id.supply_warehouse_id.id)]
            s.posible_wh_ids = posible_wh_ids

    def _compute_documents(self):
        for s in self:
            s.purchase_count = len(s.purchase_line_ids.mapped("order_id"))
            s.picking_count = len(s.stock_move_ids.mapped("picking_id"))

    def _getRoutes(self, project):
        routes = project.warehouse_id.resupply_route_ids.ids
        if project.warehouse_id.buy_to_resupply:
            routes = [project.warehouse_id.buy_pull_id.route_id.id] + routes
        return routes

    def _getDefaultRoute(self, routes):
        if not routes:
            raise ValidationError(_("No routes found for project! Make sure you have created a project warehouse."))
        return routes[0]

    @api.onchange('project_id')
    def _change_project(self):
        ids = []
        if self.project_id:
            ids = self._getRoutes(self.project_id)
        res = {
            'domain':{
                'route_id': [('id','in',ids)],
                },
            }
        if ids:
            res.update({
                'value':{
                    'route_id': self._getDefaultRoute(ids)
                    }
                })
        return res

    @api.onchange('route_id')
    def _change_route(self):
        res = {}
        if self.route_id and self.project_id:
            _Pool = None
            _route_type = None
            if self.project_id.warehouse_id.buy_pull_id.route_id == self.route_id:
                _Pool = self.project_id.purchase_inform_user_ids
                _route_type = 'buy'
            else:
                _Pool = self.project_id.stock_inform_user_ids
                _route_type = 'transfer'
            res = {
                    'values': {
                        'route_type': _route_type,
                        },
                    'domain':{
                        'purchase_inform_user_ids': [('id','in', _Pool.ids)]
                        },
                }
        return res

    @api.returns('self')
    def _colect_project_subtask(self, task, mode = 'in_site'):
        taskObj = self.env['project.task']
        if task.need_procurement:
            taskObj |= task
        index = mode=='in_site' and 1 or 0
        for t in task.child_ids.filtered(lambda x: x.task_product_ids.compute_purchase_move()[index] > 0 or x.child_ids):
            qty = t.task_product_ids.compute_purchase_move()[index]
            if t.child_ids:
                taskObj |= self._colect_project_subtask(t, mode = mode)
            elif qty > 0:
                taskObj |= t
        return taskObj


    @api.depends('task_id','project_id', 'procurement_type')
    def _colect_task_products(self):
        task_ids = []
        if self.task_id:
            task_ids = self._colect_project_subtask(self.task_id)
        else:
            task_ids = self.project_id.task_ids.mapped(lambda x: self._colect_project_subtask(x, mode = self.procurement_type))
        self.task_product_ids = [(6, 0, task_ids.mapped('task_product_ids').ids)]

    def _load_materials(self):
        res = {}
        task_ids = None
        if self.task_id:
            task_ids = self._colect_project_subtask(self.task_id)
        elif self.project_id:
            task_ids = self.project_id.task_ids.mapped(lambda x: self._colect_project_subtask(x, mode = self.procurement_type))
        if task_ids:
            res['task_product_ids'] = [(0, 0, {
                'project_id': t.task_id.project_id.id,
                'task_id': t.task_id.id,
                'task_product_id': t.id,
                'product_id': t.product_id.id,
                'to_procure_qty': t.planned_qty - t.requested_qty,
                'planned_date': t.planned_date
            }) for t in task_ids.mapped('task_product_ids') if t.planned_qty - t.requested_qty > 0]
        return res

    # def default_get(self, fieldlist):
    #     res = super(MakeProcurement, self).default_get(fieldlist)
    #     task_ids = []
    #     if res.get('task_id'):
    #         task = self.env['project.task'].browse(res.get('task_id'))
    #         if task:
    #             task_ids = self._colect_project_subtask(task)
    #     elif res.get('project_id'):
    #         project_id = self.env['project.project'].browse(res.get('project_id'))
    #         task_ids = project_id.task_ids.mapped(lambda x: self._colect_project_subtask(x, mode = self.procurement_type))
    #     if task_ids:
    #         res['task_product_ids'] = [(0, 0, {
    #             'project_id': t.task_id.project_id.id,
    #             'task_id': t.task_id.id,
    #             'task_product_id': t.id,
    #             'product_id': t.product_id.id,
    #             'to_procure_qty': t.planned_qty - t.requested_qty,
    #             'planned_date': t.planned_date
    #         }) for t in task_ids.mapped('task_product_ids') if t.planned_qty - t.requested_qty > 0]
    #     return res

    def message_post(self, *args, **kwargs):
        res = super(MakeProcurement, self).message_post(*args, **kwargs)
        if res and (self.purchase_line_ids or self.stock_move_ids) and not self._context.get('prevent_recursion', None):
            self_prevent = self.with_context(prevent_recursion=True)
            if self.purchase_line_ids:
                self_prevent.purchase_line_ids.mapped("order_id").message_post(*args, **kwargs)
            if self.stock_move_ids:
                for s in self_prevent.stock_move_ids.mapped("picking_id"):
                    s.message_post(*args, **kwargs)
        return res

    def informUsers(self):
        #notificari
        targetObj = (self.purchase_line_ids or self.stock_move_ids) or None
        if self.purchase_inform_user_ids:
            
            def postAction(objs=None, user=None):
                if not objs or not user:
                    return None
                objs.activity_schedule(
                    'mail.mail_activity_data_todo',
                    note=_('TODO: %(user)s require for %(object_name)s',
                        user=self.env.user.name,
                        object_name=objs._description),
                    user_id=user.id
                    )
            if self.purchase_inform_user_ids:
                for user in self.purchase_inform_user_ids:
                    postAction(objs=self or None, user=user)

            if self.stock_inform_user_ids:
                for user in self.stock_inform_user_ids:
                    postAction(objs=self or None, user=user)

        #Comunicare atasamente.
        attachement_ids = self.env['ir.attachment'].search([('res_id','=',self.id),('res_model','=',self._name)])
        messages = self.message_ids[1:]
        # if attachement_ids:
        #     for p in self.purchase_line_ids.mapped("order_id"):
        #         attachement_ids.copy({
        #             'res_model': p._name,
        #             'res_id': p.id,
        #             })
        #     for pik in self.stock_move_ids.mapped("picking_id"):
        #         attachement_ids.copy({
        #             'res_model': pik._name,
        #             'res_id': pik.id,
        #             })
        
        #comunicare mesaje
        if messages:
            for message in messages:
                for p in self.purchase_line_ids.mapped("order_id"):
                    message.copy({
                        'res_id': p.id,
                        'model': p._name,
                        })
                for pik in self.stock_move_ids.mapped("picking_id"):
                    message.copy({
                        'res_id': pik.id,
                        'model': pik._name,
                        })

    def _getSequence(self):
        seq_id = None
        seqObj = self.env['ir.sequence'].sudo()
        code = f'sequence.procurement.{self.company_id.id}'
        seq_ids = seqObj.search([('code', '=', code), ('company_id', 'in', [self.company_id.id, False])], order='company_id')
        if not seq_ids:
            seq_id = seqObj.create({
                        'name': f'Procurement Sequence {self.company_id.name}',
                        'prefix': f"PROC/{self.company_id.id}/",
                        'padding': 5,
                        'code': code,
                        'company_id': self.company_id.id,
                        'implementation': 'no_gap',
                    })
        else:
            seq_id = seq_ids[0]
        return seq_id

    def executeProcurement(self):
        if self.state == 'done':
            raise ValidationError(_("Execution on done procurement is not permited"))

        if self.state=='draft':
            seq = self._getSequence()
            if not seq:
                raise ValidationError("No procurement Sequence\nContact Developer")
            if not self.purchase_inform_user_ids and self.route_type == 'buy':
                raise ValidationError(_("Puchase inform users is required"))
            if not self.stock_inform_user_ids and self.route_type == 'transfer':
                raise ValidationError(_("Stock inform users is required"))
            self.informUsers()
            self.state = 'to-purchase'
            self.name = seq.next_by_id()
            return True
        
        # Save match names
        self.action_presave_form()
        
        if self.env.user not in self.purchase_inform_user_ids:
            raise ValidationError("Action forbiden!\nYou'r not one of the purchase users.")

        if not all(self.task_product_ids.mapped(lambda x: len(x.supplier_id)==1)):
            raise ValidationError("All product for procurement need at last one supplier:\n" +
                                  "\n".join([f"{p.product_id.display_name} -> [--]" for p in self.task_product_ids.filtered(lambda x: not x.supplier_id)]))

        # Match Products from procurement with product task.
        for t in self.task_product_ids:
            task_product = t.task_id.task_product_ids.filtered(lambda x: x.product_id.id == t.product_id.id and x.planned_date == t.planned_date)
            if task_product:
                t.task_product_id = task_product[0].id
            else:
                #TODO: fix, bug... produs nou adaugat nu e cazul sa fie cautat. Il avem deja.
                # t.task_id.task_product_ids = [(0, 0, {
                #     'product_id': t.product_id.id,
                #     'planned_qty': 0,
                #     'planned_date': t.planned_date
                # })]
                task_product = self.env['project.task.product'].create({
                    'product_id': t.product_id.id,
                    'planned_qty': 0,
                    'task_id': t.task_id.id,
                    'planned_date': t.planned_date
                })
                #task_product = t.task_id.task_product_ids.filtered(lambda x: x.product_id.id == t.product_id.id and x.planned_date == t.planned_date)
                #task_product = t.task_id.task_product_ids.filtered(lambda x: x.product_id.id == t.product_id.id and x.planned_date == t.planned_date)
                t.task_product_id = task_product.id
                
        task_ids = self.task_product_ids.mapped("task_id")
        project_id = task_ids.mapped("project_id")
        need_procurement_tasks = task_ids and task_ids.filtered(lambda x: x.need_procurement) or project_id.mapped('task_ids').filtered(lambda x: x.need_procurement)

        # Recheck supplier
        self.action_check_supplier()

        procure_in_tasks = self.task_id.ids
        if self._context.get('entyre_projects') or not procure_in_tasks:
            procure_in_tasks = need_procurement_tasks.ids

        for proc in self:
            wh = proc.procurement_type != 'in_site' and proc.task_id.project_id.supply_warehouse_id or None
            proc.task_product_ids.runProcurement(route=proc.route_id, wh=wh)
            
        self.state = 'done'
        self.executed_date = fields.Datetime().now()
        if self.purchase_line_ids:
            self.purchase_line_ids.mapped("order_id").write({
                'user_id': self.env.user.id,
                })
        self.informUsers()
        return True
                    
    def action_open_procurement(self, domain):
        action = self.sudo().env.ref('construction_site.project_site_procurement_action').read()[0]
        if self._context.get('create_procurement', None):
            action.update({
                'context': self._context.copy(),
                'views': [(False, 'form'),(False, 'list')],
                'search_view': "{}"
            })
        else:
            action.update({
                'domain': domain
                })
        return action
    
    def action_view_transfer(self):
        action = self.sudo().env.ref('stock.action_picking_tree_all').read()[0]
        action.update({
            'domain': [('id','in',self.stock_move_ids.mapped("picking_id.id"))]
            })
        return action
    
    def action_view_purchases(self):
        action = self.sudo().env.ref('purchase.purchase_rfq').read()[0]
        action.update({
            'domain': [('id','in',self.purchase_line_ids.mapped("order_id.id"))]
            })
        return action
    
    def action_check_supplier(self):
        for s in self:
            s.task_product_ids._reCheckSupplier()
            
    def action_presave_form(self):
        for s in self:
            s.task_product_ids._SaveForm()

    def load_materials_planned(self):
        res = self._load_materials()
        self.write(res)

    def _incrementParentTask(self, tasks=None):
        if tasks:
            tasks._incrementCostTask()
        else:
            self.mapped("task_id")._incrementCostTask()

    def cancelProcurement(self):
        if self.write({'state': 'cancel'}):
            self._incrementParentTask()

    def unlink(self):
        if any([s.state not in ['cancel'] for s in self]):
            raise UserError(_("Delete procurement is permited just in status Cancel"))
        tasks = self.mapped("task_id")
        super().unlink()
        return self._incrementParentTask(tasks=tasks)

    def _get_report_base_filename(self):
        return self.name.replace('/', '_')

class MakeProcurementProduct(models.Model):
    _name = "project.site.procurement.product"

    procurement_id = fields.Many2one("project.site.procurement", ondelete="cascade")
    project_id = fields.Many2one("project.project", _("Project"), required=True)
    task_id = fields.Many2one("project.task", _("Task"), required=True, ondelete="cascade",  domain="[('project_id', '=', project_id)]")
    task_product_id = fields.Many2one("project.task.product")
    product_id = fields.Many2one("product.product", string=_("Product"), required=True)
    to_procure_qty = fields.Float(string=_("Procure Qty"), required=True)
    product_uom_id = fields.Many2one("uom.uom", string=_("UOM"), related="product_id.uom_id", store=True)
    planned_date = fields.Date(string=_("Planned Receive Date"), default=fields.Date.today)
    supplier_id = fields.Many2one("res.partner")
    restrict_product = fields.Boolean(default=False)
    
    @api.onchange('restrict_product')
    def _onchange_restrict_product(self):
        vals = {'domain':{}}
        if self.restrict_product and self.task_id:
            vals['domain'].update({'product_id': [('id','in',self.task_id.task_product_ids.mapped("product_id.id"))]})
        elif not self.restrict_product:
            vals['domain'].update({'product_id': []})
        return vals
    
    @api.onchange('task_id')
    def _onchange_task_id(self):
        vals = {'domain':{}}
        if self.task_id and self.restrict_product:
            vals['domain'].update({'product_id': [('id','in',self.task_id.task_product_ids.mapped("product_id.id"))]})
        elif not self.restrict_product:
            vals['domain'].update({'product_id': []})
        return vals
    
    @api.onchange('task_id')
    def _onchange_task(self):
        self.planned_date = self.task_id.planned_date_begin or fields.Date.today()

    @api.model_create_multi
    def create(self, values):
        for value in values:
            value['supplier_id'] = self._getSupplier(value)
        return super(MakeProcurementProduct, self).create(values)

    def _reCheckSupplier(self):
        for s in self.filtered(lambda x: not x.supplier_id):
            data = s.read(['to_procure_qty','planned_date','product_id'])[0]
            data.update({'product_id':s.product_id.id})
            s.supplier_id = self._getSupplier(data)

    def _createSupplierValues(self, **kw):
        value = {}
        prod_supplier = self.env['product.supplierinfo']
        for index, val in prod_supplier._fields.items():
            if index in kw:
                value[index] = kw.get(index)
        return value

    def createSupplier(self, product_id=None, partner_id=None, **kw):
        if product_id:
            kw.update({
                'product_id': product_id,
                })
        if partner_id:
            kw.update({
                'partner_id': partner_id,
                })
        value = self._createSupplierValues(**kw)
        prod_supplier = self.env['product.supplierinfo']
        return prod_supplier.create(value)

    def _SaveForm(self):
        return True

    def write(self, value):
        if value.get('product_id'):
            if len(self)==1:
                val = self.read(['to_procure_qty','planned_date','product_id'])[0]
                val.update(value)
                if not self.supplier_id and not value.get('supplier_id', None):
                    value['supplier_id'] = self._getSupplier(val)
        return super(MakeProcurementProduct, self).write(value)

    def _getSupplier(self, value):
        supplier = None
        try:
            if value.get('product_id', None):
                product_id = self.env['product.product'].browse(value.get('product_id'))
                if value.get('planned_date') and isinstance(value.get('planned_date'), str):
                    value['planned_date'] = datetime.strptime(value.get('planned_date'),'%Y-%m-%d').date()
    
                if product_id:
                    supplier = product_id.with_company(self.env.company.id)._select_seller(
                        quantity=value.get('to_procure_qty', 0),
                        date=max(value.get('planned_date'), fields.Date.today()),
                        uom_id=product_id.uom_id
                        )
                if 'supplier_id' in value:

                    getSupl = lambda y: product_id.supplier_ids.filtered(lambda x: x.partner_id.id==y)

                    if supplier and supplier.partner_id.id != value.get('supplier_id'):
                        supplier = getSupl(value.get('supplier_id'))
                        if not supplier:
                            product_id.supplier_ids = [(0, 0, {
                                'partner_id': value.get('supplier_id')
                                })]
                            supplier = getSupl(value.get('supplier_id'))
        except Exception as e:
            models._logger.info(f"Error on filter supplier {e}")
        return supplier and supplier.partner_id.id or None

    def unlink(self):
        self.write({'to_procure_qty':0})
        return super().unlink()


    def launch_replenishment(self, qty, replenishment, wh=None, route=None, location=None, planned_date=None):
        uom_reference = self.product_id.uom_id

        quantity = self.product_uom_id._compute_quantity(qty, uom_reference)
        if not any([wh, location]):
            raise UserError(_("No warehouse or stock location [project_task_product/launch_replenishment]"))
        try:
            values = {
                    'warehouse_id': wh,
                    'date_planned': planned_date or datetime.now().date(),
                    'group_id': replenishment,
                    'task_id': self.task_id.id,
                    'task_product_ids': [(4, self.task_product_id.id)],
                    'task_product_id': self.task_product_id,
                    'project_id': self.project_id,
                }
            proc_line = self
            line_values = {
                'product_id': self.product_id.id,
                'product_name': self.product_id.name,
                'partner_id': self.supplier_id.id,
            }
            supplier = self.createSupplier(**line_values)
            values.update({
                    'procurement_ids': [(4, self.procurement_id.id)],
                    'supplierinfo_id': supplier,
                    'supplierinfo_name': proc_line.supplier_id or None
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
                    "%s / %s" % (self.task_id.project_id.name, self.task_id.name),
                    "%s / %s" % (self.task_id.project_id.name, self.task_id.name),
                    self.procurement_id.company_id,
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
        index = project.warehouse_id == wh and 1 or 0
        procurements = []

        replenishment = self.env['procurement.group'].create({
            'partner_id': project.user_id.partner_id.id,
            'task_id': self.task_id.id
        })

        for product_line in self:
            proc = product_line.launch_replenishment(
                product_line.to_procure_qty,
                replenishment,
                wh,
                route=route,
                planned_date=product_line.planned_date
                )
            if proc:
                procurements.append(proc)
        self.env['procurement.group'].with_context(clean_context(self.env.context)).run(procurements)
