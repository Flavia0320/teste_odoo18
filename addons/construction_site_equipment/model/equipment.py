from odoo import fields, models, _


class Equipment(models.Model):
    _inherit = "maintenance.equipment"

    sale_hour_price = fields.Float()
    currency_id = fields.Many2one('res.currency',
                                  string=_('Currency'),
                                  default=lambda self: self.env.user.company_id.currency_id)
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle')
