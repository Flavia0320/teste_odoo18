from odoo import models, _
from odoo.exceptions import UserError

class PosSession(models.Model):
    _inherit = "pos.session"

    def _loader_params_pos_payment_method(self):
        res = super()._loader_params_pos_payment_method()
        res['search_params']['fields'].append('fp_type')
        return res

#    def try_cash_in_out(self, _type, amount, reason, extras):
#        sign = 1 if _type == 'in' else -1
#        sessions = self.filtered('cash_journal_id')
#        if sign == -1:
#            for s in sessions:
#                if s.cash_register_balance_end - amount < 0:
#                    raise UserError(_("There is not enough cash in this Pos Session."))
#        super().try_cash_in_out(_type, amount, reason, extras)
