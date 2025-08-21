from odoo import api, fields, models, _

class MakeInvoice(models.Model):
    _inherit = "project.site.invoice"

    def _createInvLines(self):
        res = super(MakeInvoice, self)._createInvLines()
        self_sudo = self.sudo()
        ptime_id = self_sudo.env.ref('sale_timesheet.time_product_product_template')
        if self.invoicing_type=='detailed':
            for task in self.task_ids:
                if task.task_equipment_ids:
                    res += [(0, 0, {'name': _('Equipment %s') % task.name, 'display_type':'line_section'})]
                    res += [
                    (0, 0, {
                        'name': " ".join([str(p.effective_hours), _("hours"), "-", p.equipment_id.name]),
                        'price_unit': p.price_unit,
                        'quantity': p.effective_hours,
                        'product_id': ptime_id and ptime_id.id or None,
                        'product_uom_id': ptime_id and ptime_id.uom_id.id or None,
                        'tax_ids': [(6, 0, self.project_id.company_id.account_sale_tax_id.ids)],
                        'task_id': task.id,
                        'analytic_account_id': self.project_id.analytic_account_id.id,
                    }) for p in task.task_equipment_ids]
        return res
