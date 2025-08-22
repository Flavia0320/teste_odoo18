import requests
from odoo.addons.point_of_sale.wizard.pos_box import PosBox

class FPrintPosBox(PosBox):
    _register = False

    def run(self):
        active_model = self.env.context.get('active_model', False)
        active_ids = self.env.context.get('active_ids', [])

        if active_model == 'pos.session':
            session = self.env[active_model].browse(active_ids)[0]
            if session.config_id.fp_active:
                requests.post("%s/cashinout" % (self.config_id.fp_server_url,), json = {
                    'user': session.config_id.fp_server_user,
                    'secret': session.config_id.fp_server_secret,
                    'amount': self.amount
                })
        super(FPrintPosBox, self).run()