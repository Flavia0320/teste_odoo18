from odoo import fields, models


class StockPicking(models.Model):
    _name = "stock.picking"
    _inherit = ["stock.picking", "l10n.ro.mixin"]

    d390_id = fields.Many2one("l10_romania.report.d390")

    #TODO De verificat posibile fluxuri de implementare
    # l10n_ro_new_contact = fields.Many2one(
    #     "res.partner",
    #     "New Contact",
    #     check_company=True,
    #     help="The new partner to replace the first, "
    #     "the goods are sent to his warehouse",
    # )
    # l10n_ro_date_transfer_new_contact = fields.Datetime(
    #     "New Date of Transfer", help="Date at which the new partner replace the first"
    # )

    def _is_delivery(self):
        self.ensure_one()
        if self.location_dest_id.usage == "customer":
            return bool(len(self.move_ids.filtered(lambda x: x._is_out())))
        return False