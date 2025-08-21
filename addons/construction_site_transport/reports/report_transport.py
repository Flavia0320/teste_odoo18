from odoo import api, fields, models, _


class ReportTransports(models.Model):
    _name = "project.task.transport.report"
    _description = "Project Transport"
    _auto = False
    _rec_name = "transport_id"


    # def _purchase_selection_state(self):
    #     return self.env['purchase.order']._fields['state'].selection
    #
    # def _task_product_requested_state(self):
    #     return self.env['project.task.product']._fields['requested_state'].selection

    transport_id = fields.Many2one("fleet.vehicle", _("Transport"))
    planned_kms = fields.Float(_("Planned km"))
    planned_cost = fields.Float(_("Planned Cost"))
    effective_kms = fields.Float(_("Effective km"))
    effective_cost = fields.Float(_("Effective Cost"))
    task_id = fields.Many2one("project.task", _("Task"))
    parent_id = fields.Many2one("project.task", _("Parent Task"))
    user_ids = fields.Many2many("res.users", _("Responsible"), related="task_id.user_ids")
    stage_id = fields.Many2one("project.task.type", _("Task Stage"))

    project_id = fields.Many2one("project.project", _("Project"))
    project_status_id = fields.Many2one("project.project.stage", _("Project State"))
    manager_id = fields.Many2one("res.users", _("Project Manager"))

    company_id = fields.Many2one("res.company")


    def _select(self):
        return """
    SELECT
        tp.id as id,
        tp.transport_id as transport_id,
        tp.planned_kms as planned_kms,
        tp.planned_cost*(-1) as planned_cost,
        tp.effective_kms as effective_kms,
        tp.effective_cost*(-1) as effective_cost,
        pt.id as task_id,
        pt.parent_id as parent_id,
        pt.stage_id as stage_id,

        pp.id as project_id,
        pp.user_id as manager_id,
        pp.stage_id as project_status_id,

        pp.company_id as company_id
    """

    def _from(self):
        return """
            FROM project_task_transport tp
            LEFT JOIN project_task pt on (tp.task_id=pt.id)
            LEFT JOIN project_project pp on (pt.project_id=pp.id)
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


