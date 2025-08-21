from odoo import models, fields
from odoo.exceptions import ValidationError


class ProjectProcurement(models.Model):
    _inherit = "project.site.procurement"
    
    def _agregate(self, line):
        cols = self.env['project.task.product.import']._rowDict()
        vals = super(ProjectProcurement, self)._agregate(line)
        hours_qty = cost = 0
        if len(line) < 7:
            return vals
        if len(line) >= 7 and line[cols.get('ehours_qty', 6)]:
            hours_qty = float(line[cols.get('ehours_qty', 6)]) #nr ore
        if len(line) >= 8 and line[cols.get('ehours_cost', 7)]:
            cost = float(line[cols.get('ehours_cost', 7)]) #cost/ora
        vals.update({
            'ehours_qty': hours_qty,
            'ehours_cost': cost,
            })
        return vals


    def _setItemLineKey(self, d):
        key = super(ProjectProcurement, self)._setItemLineKey(d)
        return f"{key}-{d.get('hours_cost')}"
    
    def _updateProductItem(self, old, new):
        value = super(ProjectProcurement, self)._updateProductItem(old, new)
        value.update({
                'ehours_qty': float(old.get('ehours_qty', 0)) + float(new.get('ehours_qty', 0)),
                'ehours_cost': float(new.get('ehours_cost')),
            })
        return value
    
    def _generateProcurementItemValue(self, itemline):
        value = super(ProjectProcurement, self)._generateProcurementItemValue(itemline)
        value.update({
                'e_planned_hours': itemline.get('ehours_qty', 0),
                'e_hourly_cost': itemline.get('ehours_cost', 0)
            })
        return value
        
    def executeProcurement(self):
        res = super(ProjectProcurement, self).executeProcurement()
        if self.state == 'to-purchase':
            self.task_product_ids.action_add_equipment_plan()
        return res
    

class MakeProcurementProduct(models.Model):
    _inherit = "project.site.procurement.product"
    
    e_planned_hours = fields.Float()
    e_hourly_cost = fields.Float()
    
    def action_add_equipment_plan(self):
        for s in self:
            if s.e_planned_hours == 0:
                continue
            s.task_id.task_equipment_ids = [
                (0, 0, {
                    'planned_hours': s.e_planned_hours,
                    'hour_cost': s.e_hourly_cost,
                    'procurement_line_id': s.id,
                    })
                ]
