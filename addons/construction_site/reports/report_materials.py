from odoo import api, fields, models, _


class ReportMaterials(models.Model):
    _name = "project.task.product.report"
    _description = "Project Product Purchase"
    _auto = False
    _order = 'create_date desc'
    _rec_name = "product_id"


    def _purchase_selection_state(self):
        return self.env['purchase.order']._fields['state'].selection

    def _task_product_requested_state(self):
        return self.env['project.task.product']._fields['requested_state'].selection

    create_date = fields.Datetime(_("Create date"))
    product_id = fields.Many2one("product.product", _("Product"))
    task_id = fields.Many2one("project.task", _("Task"))
    parent_id = fields.Many2one("project.task", _("Parent Task"))
    user_ids = fields.Many2many("res.users", _("Responsible"), related="task_id.user_ids")
    stage_id = fields.Many2one("project.task.type", _("Task Stage"))

    project_id = fields.Many2one("project.project", _("Project"))
    project_status_id = fields.Many2one("project.project.stage", _("Project State"))
    manager_id = fields.Many2one("res.users", _("Project Manager"))

    required_qty = fields.Float(_("Required Product Quantity"))
    planned_qty = fields.Float(_("Planned Product Quantity"))
    purchase_qty = fields.Float(_("Purchase Product Quantity"))
    received_qty = fields.Float(_("Received Product Quantity"))
    billed_qty = fields.Float(_("Billed Product Quantity"))
    
    task_product_id = fields.Many2one("project.task.product", string=_("Task Product"))
    requested_state = fields.Selection(selection=_task_product_requested_state, related="task_product_id.requested_state", string=_("Requested State"))
    state = fields.Selection(selection=_purchase_selection_state, string=_("State"))

    warehouse_id = fields.Many2one("stock.warehouse")

    purchase_user_id = fields.Many2one("res.users", _("Purchase User"))
    purchase_id = fields.Many2one("purchase.order", _("Purchase Order"))
    purchase_date = fields.Date(_("Purchase Date"))
    company_id = fields.Many2one("res.company")


    def _select(self):
        return """
    SELECT
        tpp.id as id,
        tpp.create_date as create_date,
        tp.product_id as product_id,
        tp.id as task_product_id,
        --tp.requested_state as requested_state,
        pt.id as task_id,
        pt.parent_id as parent_id,
        pt.stage_id as stage_id,

        pp.id as project_id,
        pp.user_id as manager_id,
        pp.stage_id as project_status_id,

        tp.planned_qty as required_qty,
        tpp.planned_qty as planned_qty,
        tpp.purchase_qty as purchase_qty,
        tpp.received_qty as received_qty,
        tpp.billed_qty as billed_qty,
        tpp.state as state,
        tpp.warehouse_id as warehouse_id,

        po.id as purchase_id,
        po.user_id as purchase_user_id,
        DATE(po.date_order) as purchase_date,

        tpp.company_id as company_id
    """

    def _from(self):
        return """
            FROM project_task_product_purchase tpp
            LEFT JOIN project_task_product tp ON (tpp.task_product_id = tp.id)
            LEFT JOIN purchase_order_line pol ON (tpp.purchase_order_line_id = pol.id)
            LEFT JOIN purchase_order po ON (po.id=pol.order_id)
            LEFT JOIN project_task pt ON (pt.id=tpp.task_id)
            LEFT JOIN project_project pp ON (pp.id = tpp.project_id)
        """


    @api.model
    def _where(self):
        return '''
        '''
        #    WHERE move.move_type IN ('out_invoice', 'out_refund', 'in_invoice', 'in_refund', 'out_receipt', 'in_receipt')
        #        AND line.account_id IS NOT NULL
        #        AND NOT line.exclude_from_invoice_tab

    @property
    def _table_query(self):
        return '%s %s %s' % (self._select(), self._from(), self._where())


