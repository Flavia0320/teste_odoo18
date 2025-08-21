from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    purchase_force_qty = fields.Boolean(related="company_id.purchase_force_qty", readonly=False)