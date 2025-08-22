from odoo import fields, models, _


class Journal(models.Model):
    _inherit="pos.payment.method"

    def _load_pos_data_fields(self, config_id):
        res = super()._load_pos_data_fields(config_id)
        res.append('fp_type')
        return res