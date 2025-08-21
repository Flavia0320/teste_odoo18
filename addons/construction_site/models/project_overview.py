# Copyright 2023 Dakai Soft SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).

# from random import randint

from odoo import fields, models, _


class ProjectProject(models.Model):
    _inherit = "project.project"

    purchase_order_ids = fields.Many2many("purchase.order", compute="_computePurchaseOrder")
    picking_ids = fields.Many2many("stock.picking", compute="_computePicking")
    picking_in_ids = fields.Many2many("stock.picking", compute="_computePicking")
    picking_s_in_ids = fields.Many2many("stock.picking", compute="_computePicking")
    picking_out_ids = fields.Many2many("stock.picking", compute="_computePicking")
    picking_consume_ids = fields.Many2many("stock.picking", compute="_computePicking")
    invoice_in_ids = fields.Many2many("account.move", compute="_computeInvoice")
    invoice_out_ids = fields.Many2many("account.move", compute="_computeInvoice")

    to_consume = fields.Boolean(compute="_compute_need_btn")
    to_invoice = fields.Boolean(compute="_compute_need_btn")

    def _compute_need_btn(self):
        for s in self:
            s.to_consume = any(s.task_ids.mapped("need_consume"))
            s.to_invoice = any(s.task_ids.mapped("need_invoice"))

    def _computePurchaseOrder(self):
        for s in self:
            purchase_orders = []
            if self.env.user.has_group('purchase.group_purchase_user'):
                if self.is_construction_site:
                    purchase_orders = self.env['project.task.product.purchase'].search(
                        [
                            ('project_id','=',s.id)
                        ]).mapped('purchase_order_line_id.order_id.id')
                else:
                    purchase_orders = self.env['purchase.order.line'].search(
                        [
                            ('account_analytic_id', '=', s.analytic_account_id.id)
                            ]
                        ).mapped('order_id.id')
            s.purchase_order_ids = [(6, 0, purchase_orders)]

    def _computeInvoice(self):
        for s in self:
            account_in_invoices = self.env['account.move.line'].search(
                [
                    ('analytic_account_id', '=', s.analytic_account_id.id),
                    ('move_id.move_type', 'in', ['in_invoice', 'in_refund'])
                    ]
                ).mapped('move_id')
            account_out_invoices = self.env['account.move.line'].search(
                [
                    ('analytic_account_id', '=', s.analytic_account_id.id),
                    ('move_id.move_type', 'in', ['out_invoice', 'out_refund'])
                    ]
                ).mapped('move_id')
            s.invoice_in_ids = [(6, 0, account_in_invoices.ids)]
            s.invoice_out_ids = [(6, 0, account_out_invoices.ids)]

    def _computePicking(self):
        for s in self:
            wh = s.warehouse_id
            swh = s.supply_warehouse_id
            consum = wh.l10n_ro_wh_consume_loc_id
            pickings = s.mapped("task_ids.task_product_ids.stock_move_ids.picking_id")
            s.picking_ids = [(6, 0, pickings.ids)]
            s.picking_in_ids = [(
                    6, 0,
                    pickings.filtered(lambda x:x.location_dest_id.warehouse_id == wh and x.location_dest_id!=consum).ids
                    )]
            s.picking_s_in_ids = [(
                    6, 0,
                    pickings.filtered(lambda x:x.location_dest_id.warehouse_id == swh).ids
                    )]
            s.picking_out_ids = [(
                    6, 0,
                    pickings.filtered(lambda x:x.location_id.warehouse_id == swh).ids +  pickings.filtered(lambda x: wh and x.location_id.warehouse_id == wh and x.location_dest_id!=consum).ids #+ aviz de lichidare
                    )]
            s.picking_consume_ids = [(
                    6, 0,
                    pickings.filtered(lambda x:x.location_dest_id == consum).ids
                    )]

    def purchase_order_by_state(self, state):
        if state=='complete':
            return self.purchase_order_ids.filtered(lambda x: all(x.order_line.mapped(lambda y: y.product_qty == y.qty_received == y.qty_invoiced)))
        elif state=='no-invoice':
            return self.purchase_order_ids.filtered(lambda x: all(x.order_line.mapped(lambda y: y.product_qty == y.qty_received > y.qty_invoiced)))
        elif state=='no-receive':
            return self.purchase_order_ids.filtered(lambda x: all(x.order_line.mapped(lambda y: y.product_qty > y.qty_received)))
        return self.env['purchase.order']

    def action_view_timesheet(self):
        self.ensure_one()
        if self.is_construction_site:
            return self.action_view_timesheet_plan()
        return super().action_view_timesheet()
