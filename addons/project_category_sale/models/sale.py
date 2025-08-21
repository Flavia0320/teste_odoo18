from odoo import models

class SaleLineProjectObjective(models.Model):
    _inherit = "sale.order.line"

    def _timesheet_create_project_prepare_values(self):
        vals = super(SaleLineProjectObjective, self)._timesheet_create_project_prepare_values()
        if self.product_id.project_category_id:
            vals['category_id'] = self.product_id.project_category_id.id
        return vals