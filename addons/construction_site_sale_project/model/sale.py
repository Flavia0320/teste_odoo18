from odoo import fields, models, _

class SaleProjectConstruction(models.Model):
    _inherit = "sale.order"

    obiectiv = fields.Char(_("Obiectiv"))

    def _prepare_analytic_account_data(self, prefix=None):
        res = super()._prepare_analytic_account_data(prefix=prefix)
        if self.obiectiv:
            res.update({
                'name': self.obiectiv,
                })
        return res

    def chackConstructionName(self, email=False):
        construction_order_ids = []
        for order in self:
            if order.order_line.mapped('product_id').filtered(lambda x: x.is_construction) and not order.obiectiv:
                construction_order_ids += [order.id]
        if construction_order_ids:
            ctx = self.env.context.copy()
            ctx.update({
                'default_order_ids': [(6,0,self.ids)],
                'default_email': email
            })
            if len(construction_order_ids) == 1:
                ctx.update({
                    'default_construction_order_id': construction_order_ids[0],
                })
            else:
                ctx.update({
                    'default_construction_order_ids': [(0, 0, {
                        'construction_order_id': co_id
                    }) for co_id in construction_order_ids],
                })
            return {
                "name": "Set Construction Project Name",
                "type": "ir.actions.act_window",
                "res_model": "sale.order.construction.name",
                "view_mode": "form",
                "target": "new",
                "context": ctx,
            }
        return False

    def action_quotation_send(self):
        res = self.chackConstructionName(True)
        return res or super().action_quotation_send()

    def action_confirm(self):
        res = self.chackConstructionName()
        return res or super().action_confirm()

class SaleLineProjectObjective(models.Model):
    _inherit = "sale.order.line"

    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        self_non_construction_sale = self.filtered(lambda x: not x.order_id.obiectiv)
        return super(SaleLineProjectObjective, self_non_construction_sale)._action_launch_stock_rule(previous_product_uom_qty)

    def _timesheet_service_generation(self):
        super(SaleLineProjectObjective, self)._timesheet_service_generation()
        for line in self:
            if line.product_id.type == 'product':
                project_id = self.mapped('project_id')
                section = self.filtered(lambda x: x.sequence < line.sequence and x.display_type == 'line_section').sorted(lambda x: x.sequence, reverse=True)
                task_name = section and section[0].name or 'Products Task'
                if project_id:
                    task = self.env['project.task'].search([('name', '=', task_name), ('project_id', '=', project_id.id)])
                    task_sum = task.planned_revenue
                    if not task:
                        task = self.env['project.task'].create({
                            'name': task_name,
                            'project_id': project_id.id,
                            'partner_id': line.order_id.partner_id.id,
                        })
                    task.task_product_ids = [(0, 0, {
                        'task_id': task.id,
                        'product_id': line.product_id.id,
                        'planned_qty': line.product_uom_qty,
                        'stock_move_ids': [(6, 0, line.move_ids.ids)],
                    })]
                    task.planned_revenue = task_sum + (line.price_unit * (1-line.discount/100) * line.product_uom_qty)

    def _timesheet_create_task_prepare_values(self, project):
        values = super(SaleLineProjectObjective, self)._timesheet_create_task_prepare_values(project)
        values['planned_revenue'] = self.price_subtotal
        return values