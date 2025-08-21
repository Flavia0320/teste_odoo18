from odoo import _, fields, models

class ProjectCategory(models.Model):
    _inherit = "project.category"

    l10n_ro_accounting_location_id = fields.Many2one("stock.location", _("Accounting Location"), domain="[('l10n_ro_accounting_location', '=', True)]")