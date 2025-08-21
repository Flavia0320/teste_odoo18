from odoo import api, fields, models, _


class ReportMoveMaterials(models.Model):
    _name = "project.task.move.report"
    _description = "Project Product Move Report"
    _auto = False
    _order = 'create_date desc'
    _rec_name = "product_id"


    def _picking_selection_state(self):
        return self.env['stock.picking']._fields['state'].selection

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
    received_qty = fields.Float(_("Received Product Quantity"))
    state = fields.Selection(selection=_picking_selection_state, string=_("State"))
    location_id = fields.Many2one("stock.location")

    move_id = fields.Many2one("stock.move", _("Move"))
    picking_id = fields.Many2one("stock.picking", _("Picking"))
    picking_date = fields.Date(_("Picking Date"))
    effective_date = fields.Date(_("Effective Date"))
    company_id = fields.Many2one("res.company")


    def _select(self):
        return """
    SELECT
        (tp.id + sm.id) as id,
        sm.create_date as create_date,
        tp.product_id as product_id,
        pt.id as task_id,
        pt.parent_id as parent_id,
        pt.stage_id as stage_id,

        pp.id as project_id,
        pp.user_id as manager_id,
        pp.stage_id as project_status_id,

        tp.planned_qty as required_qty,
        sm.product_qty as planned_qty,
        (SELECT SUM(quantity) from stock_move_line where move_id=sm.id) as received_qty,
        sp.state as state,
        sm.location_dest_id as location_id,

        sp.id as picking_id,
        DATE(sp.scheduled_date) as picking_date,
        DATE(sp.date_done) as effective_date,

        tp.company_id as company_id
    """

    def _from(self):
        return """
            FROM project_task_product tp
            LEFT JOIN project_task pt on (tp.task_id=pt.id)
            LEFT JOIN project_project pp on (pt.project_id=pp.id)
            LEFT JOIN stock_move_task_product_rel smtpr on (smtpr.task_product_id=tp.id)
            LEFT JOIN stock_move sm ON (sm.id = smtpr.move_id)
            LEFT JOIN stock_picking sp ON (sp.id=sm.picking_id)
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


