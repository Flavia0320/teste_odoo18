from odoo import api, fields, models

class MrpCostStructure(models.AbstractModel):
    _name = 'report.construction_site.construction_cost_structure'
    _description = 'Construction Project Cost Structure Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        project = self.env['project.project'].browse(docids)
        return {'project': project}

