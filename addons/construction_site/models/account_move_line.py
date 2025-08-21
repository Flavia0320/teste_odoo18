# Copyright 2023 Dakai SOFT SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).

from odoo import api, fields, models
from odoo.tools.translate import _

class AccountMove(models.Model):
    _inherit = "account.move"

    project_id = fields.Many2one("project.project")
    task_id = fields.Many2one("project.task")
    project_picking_ids = fields.One2many(
        "stock.picking",
        "construction_invoice_id",
        string=_("Construction Site Related Pickings"),
        help="Related pickings "
        "(only when the invoice has been generated from a construction project).",
    )

    def _setStateDecont(self, force_signal=None):
        decont_ids = self.env['project.site.invoice'].search([('invoice_id','in',self.ids)])
        if decont_ids:
            decont_ids.check_state(force_signal=force_signal)
        
    
    def post(self):
        res = super(AccountMove, self).post()
        self._setStateDecont()
        return res
    
    def unlink(self):
        self._setStateDecont(force_signal='unlink')
        return super(AccountMove, self).unlink()
        

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    project_id = fields.Many2one("project.project")
    task_id = fields.Many2one("project.task", string="Task", index=True, compute="_compute_task_id", inverse="_inverse_task_id", store=True)
    task_product_id = fields.Many2one("project.task.product", string="Task", index=True)
    synthetic_project_task_product_ids = fields.Many2many(
        comodel_name="project.task.product",
        relation="project_task_account_line_synthetic",
        column1="account_move_line_id",
        column2="project_task_product_id",
        )

    @api.depends("move_id.task_id")
    def _compute_task_id(self):
        for s in self:
            if not s.task_id:
                s.task_id = s.move_id.task_id and s.move_id.task_id.id or None

    def _inverse_task_id(self):
        for s in self:
            s.move_id.task_id = s.task_id.id
            s.move_id.project_id = s.task_id.project_id.id

    @api.onchange('project_id')
    def onchange_project_id(self):
        domain = []
        if self.project_id:
            domain = [('project_id', '=', self.project_id.id)]
        return {'domain': {'task_id': domain}}

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        return res

    @api.model
    def default_get(self, fields):
        res = super(AccountMoveLine, self).default_get(fields)
        if self._context.get('active_model', '') == 'project.project':
            res['project_id'] = self._context.get('active_id', False)
        return res

    @api.onchange("task_id")
    def _onchange_task_id(self):
        if self.task_id:
            self.analytic_distribution = {
                self.task_id.project_id.analytic_account_id.id: 100
            }
            self.project_id = self.task_id.project_id.id
        else:
            self.analytic_distribution = False
