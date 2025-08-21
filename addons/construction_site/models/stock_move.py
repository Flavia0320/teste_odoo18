# Copyright 2020 Dakai SOFT SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).

from odoo import api, fields, models, _


class StockPicking(models.Model):
    _inherit = "stock.picking"

    project_id = fields.Many2one("project.project", compute="_getProject", store=True)
    construction_invoice_id = fields.Many2one("account.move")
    
    @api.depends('move_ids')
    def _getProject(self):
        for s in self:
            project = s.move_ids.mapped("task_id.project_id.id")
            s.project_id = project and project[0] or None

    def checkIfTrue(self):
        pick = self
        res = False
        if not pick.construction_invoice_id:
            pass
        elif pick.construction_invoice_id.state in ['draft', 'posted']:
            res = True
        return res
    
    def message_post(self, *args, **kwargs):
        res = super(StockPicking, self).message_post(*args, **kwargs)
        if res and not self._context.get('prevent_recursion', None) and self.move_ids.mapped("procurement_ids"):
            construction_procurement = self.with_context(prevent_recursion=True).mapped("move_ids.procurement_ids")
            for procurement in construction_procurement:
                procurement.message_post(*args, **kwargs)
        return res


class StockMove(models.Model):
    _inherit = "stock.move"

    task_id = fields.Many2one("project.task", string=_("Task"), index=True)
    task_product_ids = fields.Many2many(comodel_name="project.task.product",
                                       relation="stock_move_task_product_rel",
                                       column1="move_id",
                                       column2="task_product_id",
                                       string=_("Task Product"), index=True)
    procurement_ids = fields.Many2many('project.site.procurement', relation="procurement_move_objs", column2="procurement_id", column1="stock_move_id", string="Stock Move")
    
    @api.model
    def create(self, values):
        move = super(StockMove, self).create(values)
        if move.group_id and move.group_id.task_id:
            task = move.group_id.task_id
            move.origin = "%s / %s" % (task.project_id.name,task.name)
        return move

    def _prepare_procurement_values(self):
        res = super(StockMove, self)._prepare_procurement_values()
        if self.task_id:
            res['task_id'] = self.task_id.id
        if self.task_product_ids:
            res['task_product_ids'] = [(6, 0, self.task_product_ids.ids)]
        if self.procurement_ids:
            res['procurement_ids'] = [(6, 0, self.procurement_ids.ids)]
        return res
    

    @api.model
    def _prepare_merge_moves_distinct_fields(self):
        distinct_fields = super(StockMove, self)._prepare_merge_moves_distinct_fields()
        distinct_fields.append('procurement_ids')
        return distinct_fields

    def _action_cancel(self):
        if super()._action_cancel():
            self.mapped("procurement_ids")._incrementParentTask()

class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _get_custom_move_fields(self):
        fields = super(StockRule, self)._get_custom_move_fields()
        fields.append('procurement_ids')
        return fields
