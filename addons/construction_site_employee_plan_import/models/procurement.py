from odoo import models, fields
from odoo.exceptions import ValidationError


class ProjectProcurement(models.Model):
    _inherit = "project.site.procurement"
    
    def _agregate(self, line):
        cols = self.env['project.task.product.import']._rowDict()
        vals = super(ProjectProcurement, self)._agregate(line)
        hours_qty = cost = 0
        if len(line) < 5:
            return vals
        if len(line) >= 5 and line[cols.get('hours_qty', 4)]:
            hours_qty = float(line[cols.get('hours_qty', 4)]) #nr ore
        if len(line) >= 6 and line[cols.get('hours_cost', 5)]:
            cost = float(line[cols.get('hours_cost', 5)]) #cost/ora
        vals.update({
            'hours_qty': hours_qty,
            'hours_cost': cost,
            })
        return vals


    def _setItemLineKey(self, d):
        key = super(ProjectProcurement, self)._setItemLineKey(d)
        return f"{key}-{d.get('hours_cost')}"
    
    def _updateProductItem(self, old, new):
        value = super(ProjectProcurement, self)._updateProductItem(old, new)
        value.update({
                'hours_qty': float(old.get('hours_qty', 0)) + float(new.get('hours_qty', 0)),
                'hours_cost': float(new.get('hours_cost'))
            })
        return value
    
    def _generateProcurementItemValue(self, itemline):
        value = super(ProjectProcurement, self)._generateProcurementItemValue(itemline)
        value.update({
                'planned_hours': itemline.get('hours_qty', 0),
                'hourly_cost': itemline.get('hours_cost', 0)
            })
        return value
        
    def executeProcurement(self):
        res = super(ProjectProcurement, self).executeProcurement()
        if self.state == 'to-purchase':
            self.task_product_ids.action_add_employee_plan()
        return res
    

class MakeProcurementProduct(models.Model):
    _inherit = "project.site.procurement.product"
    
    planned_hours = fields.Float()
    hourly_cost = fields.Float()
    
    def action_add_employee_plan(self):
        for s in self:
            if s.planned_hours==0:
                continue
            s.task_id.task_employee_ids = [
                (0, 0, {
                    'planned_hours': s.planned_hours,
                    'hourly_cost': s.hourly_cost,
                    'procurement_line_id': s.id,
                    })
                ]
