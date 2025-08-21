from odoo import api, fields, models, _


class ReportSubcontracting(models.Model):
    _name = "project.task.subcontracting.report"
    _description = "Project Subcontracting Purchase"
    _auto = False
    _rec_name = "product_id"


    product_id = fields.Many2one("product.product", _("Product"))
    planned_qty = fields.Float(_("Planned Qty"))
    planned_cost = fields.Float(_("Planned Cost"))
    effective_qty = fields.Float(_("Effective Qty"))
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
        tp.product_id as product_id,
        tp.planned_qty as planned_qty,
        tp.planned_cost*(-1) as planned_cost,
        tp.effective_qty as effective_qty,
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
            FROM project_task_subcontracting tp
            LEFT JOIN project_task pt on (tp.task_id=pt.id)
            LEFT JOIN project_project pp on (pt.project_id=pp.id)
        """


    @api.model
    def _where(self):
        return '''
        '''

    @property
    def _table_query(self):
        return '%s %s %s' % (self._select(), self._from(), self._where())


