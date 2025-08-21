from odoo import api, fields, models, _
from odoo.exceptions import UserError


class TaskProductPurchase(models.Model):
    _name = "project.task.product.purchase"
    _description = _("Task Product Purchase Fragment")
    _rec_name = "purchase_order_line_id"

    def _purchase_selection_state(self):
        return self.env['purchase.order']._fields['state'].selection

    task_product_id = fields.Many2one("project.task.product", _("Task Product"), ondelete="cascade", required=True)
    task_id = fields.Many2one("project.task", _("Task"), store=True, related="task_product_id.task_id")
    project_id = fields.Many2one("project.project", _("Project"), store=True, related="task_product_id.task_id.project_id")
    purchase_order_line_id = fields.Many2one("purchase.order.line", _("Task Product"), ondelete="cascade", required=True)
    planned_qty = fields.Float(_("Planned Product Quantity"), required=True)
    purchase_qty = fields.Float(_("Purchase Product Quantity"), compute="_compute_in_qty", store=True)
    received_qty = fields.Float(_("Received Product Quantity"), compute="_compute_in_qty", store=True)
    billed_qty = fields.Float(_("Billed Product Quantity"), compute="_compute_in_qty", store=True)
    state = fields.Selection(selection=_purchase_selection_state, compute="_compute_state", string=_("Status"), store=True)
    warehouse_id = fields.Many2one("stock.warehouse")
    company_id = fields.Many2one("res.company", default=lambda x: x.env.user.company_id.id)

    @api.depends('purchase_order_line_id.order_id.state')
    def _compute_state(self):
        for s in self:
            s.update({
                'state':s.purchase_order_line_id and s.purchase_order_line_id.order_id.state,
                })

    @api.depends(
        'purchase_order_line_id.product_uom_qty',
        'purchase_order_line_id.qty_received',
        'purchase_order_line_id.qty_invoiced',
        )
    def _compute_in_qty(self):
        for s in self:
            values = {
                'purchase_qty': 0,
                'received_qty': 0,
                'billed_qty': 0,
                }

            for line in s.purchase_order_line_id._distribute_qty('product_uom_qty'):
                if line[0]!=s.id:
                    continue
                values['purchase_qty'] = line[1]
                break

            for line in s.purchase_order_line_id._distribute_qty('qty_received'):
                if line[0]!=s.id:
                    continue
                values['received_qty'] = line[1]
                break

            for line in s.purchase_order_line_id._distribute_qty('qty_invoiced'):
                if line[0]!=s.id:
                    continue
                values['billed_qty'] = line[1]
                break
            s.update(values)

    def write(self, values):
        for s in self:
            if values.get('state', s.state)=='purchase' and values.get('purchase_qty', None):
                values['planned_qty'] = values.get('purchase_qty')
        if values.get('state', None)=='cancel':
            values.update({
                'planned_qty':0,
                'purchase_qty':0,
                'received_qty':0,
                'billed_qty':0,
                })
        if self.state == 'cancel' and values.get('state', None)=='draft':
            raise UserError(_("Cannot convert to draft this purchase, delete it instad and regenerate purchase"))
        return super(TaskProductPurchase, self).write(values)
