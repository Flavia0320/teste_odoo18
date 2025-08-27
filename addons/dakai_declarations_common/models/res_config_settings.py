from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    l10n_ro_decalaration_url = fields.Char(string="Declaration Url", config_parameter='dakai_declarations_common.l10n_ro_decalaration_url')

