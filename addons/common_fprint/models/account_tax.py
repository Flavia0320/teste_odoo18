from odoo import api, fields, models, _

class AccountTaxPython(models.Model):
    _inherit = "account.tax"

    fp_tax_group_id = fields.Integer()

    def _load_pos_data_fields(self, config_id):
        res = super()._load_pos_data_fields(config_id)
        res.append('fp_tax_group_id')
        return res

    #invoice type