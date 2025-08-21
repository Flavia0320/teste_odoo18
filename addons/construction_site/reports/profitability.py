from odoo import fields, models
from odoo import tools


class ProjectProfitability(models.Model):
    _name = "project.task.revenu.report"
    _description = "Revenu report"
    _auto = False

    project_id = fields.Many2one("project.project")
    task_id = fields.Many2one("project.task")
    parent_id = fields.Many2one("project.task")
    project_manager_id = fields.Many2one("res.users")
    partner_id = fields.Many2one("res.partner", string="Customer")
    assigned_users = fields.Char()
    purchase_users = fields.Char()
    stock_users = fields.Char()

    planned_revenue = fields.Float()
    real_revenue = fields.Float()
    future_revenue = fields.Float()
    
    planned_cost = fields.Float()
    real_cost = fields.Float()
    future_cost = fields.Float()

    planned_profit = fields.Float()
    real_profit = fields.Float()

    employee_cost = fields.Float()
    subcontracting_cost = fields.Float()
    equipment_cost = fields.Float()
    transport_cost = fields.Float()
    material_cost = fields.Float()

    def _select(self):
        return """
    SELECT
        t.id as id,
        p.id as project_id,
        t.id as task_id,
        t.parent_id as parent_id,
        p.user_id as project_manager_id,

        -- Concat Task Userii
        array_to_string(array_agg(
            upt.name
            ), ', ', '') as assigned_users,

        -- Concat Purchase Userii
        array_to_string(array_agg(
            prp.name
            ), ', ', '') as purchase_users,

        -- Concat Stock Userii
        array_to_string(array_agg(
            srp.name
            ), ', ', '') as stock_users,

       -- Show Revenu
       t.planned_revenue as planned_revenue,
       t.revenue as real_revenue,
       (CASE WHEN t.revenue < t.planned_revenue
            THEN t.planned_revenue - t.revenue
            ELSE 0
       END) as future_revenue,

       -- Show Cost
       t.planned_cost as planned_cost,
       t.cost as real_cost,
       (CASE WHEN t.cost < t.planned_cost
            THEN t.planned_cost - t.cost
            ELSE 0
       END) as future_cost,

       (t.planned_revenue + t.planned_cost) as planned_profit,
       (t.revenue + t.cost) as real_profit,
       t.employee_cost as employee_cost,
       t.subcontracting_cost as subcontracting_cost,
       t.equipment_cost as equipment_cost,
       t.transport_cost as transport_cost,
       t.material_cost as material_cost
       -- TODO: ceva calcule de randament ar fi utile: real_profit/planned_profit ar trebui sa fie >= 1

    """

    def _from(self):
        return """
    FROM project_task t
        LEFT JOIN project_project p on (t.project_id=p.id)

        -- Concat Task Useri
        LEFT JOIN project_task_user_rel ptur on (t.id=ptur.task_id)
        LEFT JOIN res_users ru on (ru.id=ptur.user_id)
        LEFT JOIN res_partner upt on (ru.partner_id=upt.id)

        -- Concat Stock Useri
        LEFT JOIN stock_project_inform spi on (p.id=spi.project_project_id)
        LEFT JOIN res_users sru on (sru.id=spi.res_users_id)
        LEFT JOIN res_partner srp on (sru.partner_id=srp.id)

        -- Concat Purchase Useri
        LEFT JOIN purchase_project_inform ppi on (p.id=ppi.project_project_id)
        LEFT JOIN res_users pru on (pru.id=ppi.res_users_id)
        LEFT JOIN res_partner prp on (pru.partner_id=prp.id)
    """

    def _where(self):
        return """ WHERE t.is_construction_site = TRUE """

    def _groupby(self):
        return " GROUP BY t.id, p.id"

    @property
    def _table_query(self):
        return '%s %s %s %s' % (self._select(), self._from(), self._where(), self._groupby())
