# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.misc import clean_context
from datetime import datetime
import json

class Project(models.Model):
    _inherit = "project.project"

    pricelist_id = fields.Many2one("product.pricelist", compute="_setPriceList", store=True)
    is_construction_site = fields.Boolean(_("Is Construction Site"))
    need_procurement = fields.Boolean(compute="_compute_procurement_need")
    need_consume = fields.Boolean(compute="_compute_consume_need")
    invoice_method = fields.Selection([
        ('consume', _("Consummed QTY")),
        ('received', _("Received QTY")),
        ('planned', _("Planned QTY")),
        ], default="consume")
    
    stock_inform_user_ids = fields.Many2many("res.users", relation="stock_project_inform")
    purchase_inform_user_ids = fields.Many2many("res.users", relation="purchase_project_inform")
    
    procurement_count = fields.Integer(compute="_compute_count_docs")

    def _compute_count_docs(self):
        procurement_obj = self.env['project.site.procurement']
        for s in self:
            s.procurement_count = len(procurement_obj.search([('project_id', '=', s.id)]))

    @api.depends('task_ids.need_procurement')
    def _compute_procurement_need(self):
        for project in self:
            project.need_procurement = any(project.task_ids.mapped(lambda x: x.need_procurement))

    @api.depends('task_ids.need_consume')
    def _compute_consume_need(self):
        for project in self:
            project.need_consume = any([task.need_consume for task in project.task_ids])

    @api.depends('partner_id')
    def _setPriceList(self):
        for s in self:
            pl = s.sale_order_id.pricelist_id or s.partner_id.property_product_pricelist or None
            s.pricelist_id = pl and pl.id

    def consumeProducts(self):
        try:
            self.ensure_one()
        except:
            raise UserError(_("Only one project at a time can be randered"))
        for task in self.task_ids:
            task.consumeProducts(force=True)

    def _get_report_base_filename(self, docType):
        dtype = ""
        if docType=='deviz':
            dtype= _("Fisa Deviz")
        if docType=='decont':
            dtype= _("Fisa Decont")
        return "-".join([dtype, self.name])

    def runReverseMaterials(self, task_ids=None):
        wh = self.supply_warehouse_id
        route=None
        route = self.env['stock.route'].search([
                ('rule_ids.location_dest_id','child_of', wh.view_location_id.id),
                ('rule_ids.location_src_id','child_of', self.warehouse_id.view_location_id.id),
                #('rule_ids.picking_type_id.sequence_code','=','INT'),
                ], limit=1)
        if not route:
            raise UserError(_("No route for internal transfer\n project_project/runReverseMaterials"))
        procurements = []
        replenishment = self.env['procurement.group'].create({
            'partner_id': self.user_id.partner_id.id,
            #'task_id': self.task_id.id
        })
        for product_line, qty, location in self._prepareRemainingMaterialsTransfer(task_ids=task_ids):
            proc = product_line.launch_replenishment(qty, replenishment, wh, route=route, planned_date=datetime.now())
            if proc:
                procurements.append(proc)
        self.env['procurement.group'].with_context(clean_context(self.env.context)).run(procurements)
        #TODO: de continuat


    def _prepareRemainingMaterialsTransfer(self, task_ids=None):
        self.ensure_one()
        wh = self.warehouse_id
        consu = self.consume_loc_id
        if not task_ids:
            task_ids = self.task_ids
        task_products = task_ids.mapped("task_product_ids")
        location_ids = self.env['stock.location'].with_context(active_test=False).search(
            [
                ('location_id', 'child_of', wh.view_location_id.id),
                ('usage', '=', 'internal')
                ]
            )
        products = []
        for loc in location_ids:
            if loc==consu:
                continue
            products += [
                (pline, pline.product_id.qty_available, loc)
                for pline in task_products.with_context({'location':loc.id}).filtered(lambda x: x.product_id.qty_available>0)
                ]
        return products

    def get_panel_data(self):
        panel_data = super(Project, self).get_panel_data()
        if not self.env.user.has_groups('project.group_project_user'):
            return panel_data
        if self.is_construction_site:
            panel_data['is_construction_site'] = self.is_construction_site

            purchase_orders = []
            if self.env.user.has_group('purchase.group_purchase_user'):
                if self.is_construction_site:
                    purchase_orders = self.env['project.task.product.purchase'].search(
                        [
                            ('project_id','=',self.id)
                        ]).mapped('purchase_order_line_id.order_id.id')
                else:
                    purchase_orders = self.env['purchase.order.line'].search(
                        [
                            ('account_id', '=', self.account_id.id)
                            ]
                        ).mapped('order_id.id')
            panel_data['purchase_order_ids'] = purchase_orders

            panel_data['profitability_items'] = self._get_profitability_items()
            panel_data['profitability_labels'] = self._get_profitability_labels()

            tasks = self.task_ids.filtered(lambda x: not x.parent_id)
            for task in tasks:
                panel_data['profitability_labels'][task.id] = task.name
                args = ['construction_task', [('id', 'in', task.ids)], task.id]
                panel_data['profitability_items']['revenues']['data'] += [{
                    'id': task.id,
                    'action': {'name': 'action_profitability_items', 'type': 'object', 'args': json.dumps(args)},
                    'invoiced': task.revenue,
                    'sequence':task.id,
                    'to_invoice': task.planned_revenue - task.revenue
                }]
            panel_data['profitability_items']['revenues']['total'] = {
                'invoiced': sum(tasks.mapped('revenue')),
                'to_invoice': sum(tasks.mapped('planned_revenue')) - sum(tasks.mapped('revenue'))
            }

            pickings = self.mapped("task_ids.task_product_ids.stock_receive_ids.picking_id")
            purchases_picking = self.mapped("task_ids.task_product_ids.purchase_line_ids.purchase_order_line_id.order_id.picking_ids")
            transfer_pickings = pickings.filtered(lambda x: x.id not in purchases_picking.ids)

            query_in = self.env['account.move.line']._search([('move_id.move_type', 'in', self.env['account.move'].get_purchase_types())])
            query_in.order = None
            query_in.add_where('analytic_distribution ? %s', [str(self.account_id.id)])
            query_in_string, query_in_param = query_in.select('DISTINCT account_move_line.move_id')
            self._cr.execute(query_in_string, query_in_param)
            account_in_invoices = [line.get('move_id') for line in self._cr.dictfetchall()]

            query_out = self.env['account.move.line']._search([('move_id.move_type', 'in', self.env['account.move'].get_sale_types())])
            query_out.order = None
            query_out.add_where('analytic_distribution ? %s', [str(self.account_id.id)])
            query_out_string, query_out_param = query_out.select('DISTINCT account_move_line.move_id')
            self._cr.execute(query_out_string, query_out_param)
            account_out_invoices = [line.get('move_id') for line in self._cr.dictfetchall()]

            panel_data['invoice_in_ids'] = account_in_invoices
            panel_data['invoice_out_ids'] = account_out_invoices

            account_in_invoices_data = {
                'text': _("Bills"),
                'sequence': 4
            }
            account_out_invoices_data = {
                'text': _("Invoices"),
                'sequence': 4
            }

            for i in range(len(panel_data['buttons'])):
                if panel_data['buttons'][i]['action'] == 'action_open_project_vendor_bills':
                    account_in_invoices_data = {
                        'text': panel_data['buttons'][i]['text'],
                        'sequence': panel_data['buttons'][i]['sequence']
                    }
                    del panel_data['buttons'][i]
                    break

            for i in range(len(panel_data['buttons'])):
                if panel_data['buttons'][i]['action'] == 'action_open_project_invoices':
                    account_out_invoices_data = {
                        'text': panel_data['buttons'][i]['text'],
                        'sequence': panel_data['buttons'][i]['sequence']
                    }
                    del panel_data['buttons'][i]
                    break

            if account_in_invoices:
                panel_data['buttons'] += [{
                    'action': 'action_open_account_in_invoices',
                    'action_type': 'object',
                    'icon': 'pencil-square-o',
                    'number': len(account_in_invoices),
                    'sequence': account_in_invoices_data['text'],
                    'show': True,
                    'text': account_in_invoices_data['text']
                }]

            if account_out_invoices:
                panel_data['buttons'] += [{
                    'action': 'action_open_account_out_invoices',
                    'action_type': 'object',
                    'icon': 'pencil-square-o',
                    'number': len(account_out_invoices),
                    'sequence': account_out_invoices_data['text'],
                    'show': True,
                    'text': account_out_invoices_data['text']
                }]

            if transfer_pickings:
                panel_data['buttons'] += [{
                    'action': 'action_open_construction_picking',
                    'action_type': 'object',
                    'icon': 'truck',
                    'number': len(transfer_pickings),
                    'sequence': 5,
                    'show': True,
                    'text': _("Supply WH Pickings")
                }]
                panel_data['profitability_labels']['construction_picking'] = _("Delivery from Supply WH")
                args = ['construction_picking', [('id', 'in', transfer_pickings.ids)]]
                if len(transfer_pickings) == 1:
                    args.append(transfer_pickings[0].id)
                panel_data['profitability_items']['costs']['data'] += [{
                    'id': 'construction_picking',
                    'action': {'name': 'action_profitability_items', 'type': 'object', 'args': json.dumps(args)},
                    'billed': -sum(transfer_pickings.mapped("move_ids.stock_valuation_layer_ids.value")),
                    'sequence':20,
                    'to_bill': 0
                }]
                panel_data['profitability_items']['costs']['total']['billed'] -= sum(transfer_pickings.mapped("move_ids.stock_valuation_layer_ids.value"))
        return panel_data

    def action_profitability_items(self, section_name, domain=None, res_id=False):
        if section_name == 'construction_task':
            action = {
                'name': _('Task'),
                'type': 'ir.actions.act_window',
                'res_model': 'project.task',
                'views': [[False, 'form']],
                'res_id': res_id,
                'view_mode': 'form'
            }
            return action

        if section_name == 'construction_picking':
            action = {
                'name': _('Picking Items'),
                'type': 'ir.actions.act_window',
                'res_model': 'stock.picking',
                'views': [[False, 'list'], [False, 'form']],
                'domain': domain,
                'context': {
                    'create': False,
                    'edit': False,
                },
            }
            if res_id:
                action['res_id'] = res_id
                if 'views' in action:
                    action['views'] = [
                        (view_id, view_type)
                        for view_id, view_type in action['views']
                        if view_type == 'form'
                    ] or [False, 'form']
                action['view_mode'] = 'form'
            return action

        return super().action_profitability_items(section_name, domain, res_id)

    def action_open_construction_picking(self):
        pickings = self.mapped("task_ids.task_product_ids.stock_receive_ids.picking_id")
        purchases_picking = self.mapped("task_ids.task_product_ids.purchase_line_ids.purchase_order_line_id.order_id.picking_ids")
        transfer_pickings = pickings.filtered(lambda x: x.id not in purchases_picking.ids)
        action_window = {
            'name': _('Picking Items'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'views': [[False, 'list'], [False, 'form']],
            'domain': [('id', 'in', transfer_pickings.ids)],
            'context': {
                'project_id': self.id,
            }
        }
        if len(transfer_pickings) == 1:
            action_window['views'] = [[False, 'form']]
            action_window['res_id'] = transfer_pickings[0].id
        return action_window

    def action_open_account_in_invoices(self):

        query_in = self.env['account.move.line']._search(
            [('move_id.move_type', 'in', self.env['account.move'].get_purchase_types())])
        query_in.order = None
        query_in.add_where('analytic_distribution ? %s', [str(self.account_id.id)])
        query_in_string, query_in_param = query_in.select('DISTINCT account_move_line.move_id')
        self._cr.execute(query_in_string, query_in_param)
        account_in_invoices = [line.get('move_id') for line in self._cr.dictfetchall()]

        action_window = {
            'name': _('Invoices'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'views': [[False, 'list'], [False, 'form']],
            'domain': [('id', 'in', account_in_invoices)],
            'context': {
                'project_id': self.id,
            }
        }
        if len(account_in_invoices) == 1:
            action_window['views'] = [[False, 'form']]
            action_window['res_id'] = account_in_invoices[0]
        return action_window

    def action_open_account_out_invoices(self):

        query_out = self.env['account.move.line']._search(
            [('move_id.move_type', 'in', self.env['account.move'].get_sale_types())])
        query_out.order = None
        query_out.add_where('analytic_distribution ? %s', [str(self.account_id.id)])
        query_out_string, query_out_param = query_out.select('DISTINCT account_move_line.move_id')
        self._cr.execute(query_out_string, query_out_param)
        account_out_invoices = [line.get('move_id') for line in self._cr.dictfetchall()]

        action_window = {
            'name': _('Bills'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'views': [[False, 'list'], [False, 'form']],
            'domain': [('id', 'in', account_out_invoices)],
            'context': {
                'project_id': self.id,
            }
        }
        if len(account_out_invoices) == 1:
            action_window['views'] = [[False, 'form']]
            action_window['res_id'] = account_out_invoices[0]
        return action_window

    def create_manual_bill(self):
        ctx = self.env.context.copy()
        ctx.update({
            'default_ref': self.partner_id.name,
            'default_move_type': 'in_invoice',
            'default_invoice_origin': self.name,
            'default_invoice_user_id': self.user_id.id,
            'default_currency_id': self.pricelist_id.currency_id.id,
            'default_payment_reference': self.name,
            'default_project_id': self.id,
        })
        return {
            "name": "Create Project Bill",
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "view_mode": "form",
            "target": "current",
            "context": ctx,
        }

    def action_open_procurement(self):
        action = self.env['project.site.procurement'].action_open_procurement([('project_id','=',self.id)])
        return action
    
    def action_open_reports_balance(self):
        action = self.sudo().env.ref('construction_site.project_task_revenu_report_action').read()[0]
        action.update({'domain':[('project_id','=',self.id), ('parent_id','=',False)]})
        return action

    def action_open_reports_material(self):
        action = self.sudo().env.ref('construction_site.project_task_product_report_action').read()[0]
        action.update({'domain':[('project_id','=',self.id)]})
        return action

    def action_open_reports_moves(self):
        action = self.sudo().env.ref('construction_site.project_task_move_report_action').read()[0]
        action.update({'domain':[('project_id','=',self.id)]})
        return action
    
    def action_open_reports(self):
        pass

    def action_open_decont(self):
        action = self.sudo().env.ref('construction_site.project_site_invoice_action2').read()[0]
        action.update({
            'domain':[('project_id','=',self.id)],
            })
        return action
    
    def _destroy_any_managing_task(self):
        taskModel = self.env['project.task']
        taskModel.search([('project_id','in',self.ids), ('construction_organiser','=',True)]).write({
            'site_management': False,
            'planned_extra_cost': 0,
            })
        
    
    def _create_site_management_task(self):
        taskModel = self.env['project.task']
        stageModel = self.env['project.task.type']
        for s in self:
            stage = stageModel.search([('project_ids','in',[s.id])], limit=1, order='sequence ASC')
            taskmanagement = taskModel.search([('project_id', '=', s.id), ('site_management','=',True)])
            if not taskmanagement:
                taskModel.create({
                    'name': _("Construction Management"),
                    'site_management': True,
                    'project_id': s.id,
                    'stage_id': stage and stage.id or None,
                    'sale_line_id': None,
                    })
    
    @api.model_create_multi
    def create(self, vals_list):
        res = super(Project, self).create(vals_list)
        for s in res.filtered(lambda x: x.is_construction_site):
            s._create_site_management_task()
        return res
    
    def write(self, value):
        res = super(Project, self).write(value)
        for s in self.filtered(lambda x: x.is_construction_site):
            s._create_site_management_task()
        if value.get('is_construction_site', None) == False:
            self._destroy_any_managing_task()
        return res
