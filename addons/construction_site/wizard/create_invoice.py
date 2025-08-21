from odoo import api, fields, models
from odoo.tools.translate import _
from odoo.models import _logger
from odoo.exceptions import UserError


class MakeInvoice(models.Model):
    _name = "project.site.invoice"
    _description = _("Decont/invoicing")
    _rec_name = "task_id"

    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('done', 'Done'),
        ('cancel', 'Cancel'),
        ],_("State"), default="draft")
    company_id = fields.Many2one("res.company", related="project_id.company_id", string="Company", store=True)
    task_id = fields.Many2one("project.task", _("Parent Task"))
    project_id = fields.Many2one("project.project", _("Project"))
    task_ids = fields.Many2many(comodel_name="project.task",
                                relation="project_site_invoicing_task_rel",
                                column1="project_site_procurement_id",
                                column2="task_id",
                                string=_("Invoicing tasks"))
    stock_picking_ids = fields.Many2many("stock.picking")
    invoice_id = fields.Many2one("account.move")
    invoicing_type = fields.Selection([
            ('syntetic',_("Syntetic")),
            ('detailed', _("Detailed")) #TODO detaliat doar fara bon consum.
            ], string=_("Invoice Method"), default='syntetic', required=True)

    def default_get(self, field_list):
        res = super(MakeInvoice, self).default_get(field_list)
        task = project = None
        if res.get('task_id', None):
            task = self.env['project.task'].browse(res.get('task_id'))
        if res.get('project_id', None):
            task = self.env['project.project'].browse(res.get('project_id'))
        if task or project:
            res['task_ids'] = self._colect_tasks(task_id=task, project_id=project)
        return res
        

    @api.returns('self')
    def _colect_project_subtask(self, task):
        taskObj = self.env['project.task']
        if not task.account_move_line_ids.mapped('move_id').filtered(lambda x:x.move_type in self.env['account.move'].get_sale_types()) and not task.child_ids:
            taskObj |= task
        for t in task.child_ids:
            if t.child_ids:
                taskObj |= self._colect_project_subtask(t)
            elif not t.account_move_line_ids.mapped('move_id').filtered(lambda x:x.move_type in self.env['account.move'].get_sale_types()):
                taskObj |= t
        return taskObj

    #@api.depends('task_id','project_id', 'invoicing_type')
    def _colect_tasks(self, task_id=None, project_id=None):
        task_ids = []
        if task_id:
            task_ids = self._colect_project_subtask(self.task_id).ids
        elif project_id:
            task_ids = project_id.task_ids.ids
        return [(6, 0, task_ids)]

    @api.onchange('task_ids')
    def _onchangeTask2Pickings(self):
        picking_ids = []

        if self.task_ids:
            project = self.task_ids.mapped("project_id")[0]
            stock_type = None
            if project.invoice_method=='consume':
                stock_type = 'stock_consume_ids'
            elif project.invoice_method in ['received','planned']:
                stock_type = 'stock_receive_ids'
            stock_move_flow = f"task_product_ids.{stock_type}.picking_id"
            picking_ids = self.task_ids.mapped(stock_move_flow).filtered(lambda x: x.checkIfTrue() == False).ids
        self.stock_picking_ids = [(6, 0, picking_ids)]

    def executeInvoicing(self):
        if not self.project_id.partner_id:
            raise UserError(_("Custommer is required on project"))
        #inv = self._create_invoice()
        inv = self._create_invoice()
        self.stock_picking_ids.write({'construction_invoice_id': inv.id})
        return True

    def _create_invoice(self):
        invoice_vals = self._prepare_invoice_values()
        #migrare16 - acum campul este compute
        #invoice_vals['fiscal_position_id'] = self.env['account.fiscal.position'].get_fiscal_position(self.project_id.partner_id.id).id

        invoice = self.env['account.move'].with_company(self.project_id.company_id)\
            .sudo().create(invoice_vals).with_user(self.env.uid)
        invoice.message_post_with_source('mail.message_origin_link',
                    render_values={'self': invoice, 'origin': self.project_id},
                    subtype_id=self.env.ref('mail.mt_note').id)
        self.invoice_id = invoice.id
        self.state = 'open'
        return invoice

    def _prepare_invoice_values(self):
        project = self.project_id
        partner = project.partner_id
        line_values = self._createInvLines()
        invoice_vals = {
            'ref': partner.name,
            'move_type': 'out_invoice',
            'invoice_origin': project.name,
            'invoice_user_id': project.user_id.id,
            #'narration': self.project_id.description,
            'partner_id': partner.id,
            'partner_shipping_id': partner.id,
            'currency_id': project.pricelist_id.currency_id.id,
            'payment_reference': project.name,
            #'invoice_payment_term_id': partner.payment_term_id.id,
            #'partner_bank_id': order.company_id.partner_id.bank_ids[:1].id,
            #'team_id': order.team_id.id,
            #'campaign_id': order.campaign_id.id,
            #'medium_id': order.medium_id.id,
            #'source_id': order.source_id.id,
            'invoice_line_ids': line_values,
        }
        return invoice_vals

    def _createInvLines(self):
        res = []
        if self.invoicing_type=='syntetic':
            res += [
            (0, 0, {
                'name': task.name,
                'price_unit': task.planned_revenue,
                'quantity': 1.0,
                'product_id': task.sale_line_id and task.sale_line_id.product_id.id,
                #'product_uom_id': so_line.product_uom.id,
                'tax_ids': [(6, 0, self.project_id.company_id.account_sale_tax_id.ids)],
                'project_id': task.project_id.id,
                'task_id': task.id,
                'synthetic_project_task_product_ids': [(6, 0, task.task_product_ids.filtered(lambda x: x.to_invoice_qty > 0).ids)],
                'sale_line_ids': [(6, 0, task.sale_line_id.ids)],
                #'analytic_tag_ids': [(6, 0, so_line.analytic_tag_ids.ids)],
                'analytic_distribution': {
                    self.project_id.analytic_account_id.id: 100
                },
            }) for task in self.task_id]# if task.planned_revenue > 0 and not task.child_ids]
        elif self.invoicing_type=='detailed':
            res += [
            (0, 0, {
                'name': task.name,
                'price_unit': task.planned_revenue,
                'quantity': 1.0,
                'product_id': task.sale_line_id and task.sale_line_id.product_id.id,
                #'product_uom_id': so_line.product_uom.id,
                'tax_ids': [(6, 0, self.project_id.company_id.account_sale_tax_id.ids)],
                'project_id': task.project_id.id,
                'task_id': self.task_id.id,
                'synthetic_project_task_product_ids': [(6, 0, task.task_product_ids.filtered(lambda x: x.to_invoice_qty > 0).ids)],
                'sale_line_ids': [(6, 0, self.task_id.sale_line_id.ids)],
                #'analytic_tag_ids': [(6, 0, so_line.analytic_tag_ids.ids)],
                'analytic_distribution': {
                    self.project_id.analytic_account_id.id: 100
                },
            }) for task in self.task_ids if task.planned_revenue > 0 and not task.child_ids]
        # elif self.invoicing_type=='detailed':
        #     for task in self.task_ids:
        #         if task.task_product_ids and task.planned_revenue > 0 and not task.child_ids:
        #             res += [(0, 0, {'name': _('Products %s') % task.name, 'display_type':'line_section'})]
        #             res += [
        #             (0, 0, {
        #                 'name': p.product_id.name,
        #                 'price_unit': p.price_unit,
        #                 'quantity': p.received_qty,
        #                 'product_id': p.product_id.id,
        #                 'product_uom_id': p.uom_id.id,
        #                 'tax_ids': [(6, 0, p.product_id.taxes_id.ids)],
        #                 'task_id': task.id,
        #                 'task_product_id': p.id,
        #                 'analytic_distribution': {
        #                     self.project_id.analytic_account_id.id: 100
        #                 },
        #             }) for p in task.task_product_ids]
        return res
    
    def check_state(self, force_signal=None):
        for s in self:
            if force_signal=='unlink':
                s.state = 'draft'
                continue
            
            state = (s.invoice_id.state, s.invoice_id.payment_state)
            if state[0] == 'posted':
                s.state = 'open'
            elif state[0] == 'cancel':
                s.state = 'cancel'
            elif state[0] == 'posted' and state[1] not in ['paid']:
                s.state = 'done'
                
    def unlink(self):
        if any([x=='posted' for x in self.mapped("invoice_id.state")]):
            raise UserError(_("You cannot unlink %s if you have posted invoice") % self._description)
        return super(MakeInvoice, self).unlink()
