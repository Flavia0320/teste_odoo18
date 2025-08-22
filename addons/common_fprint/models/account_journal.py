from odoo import fields, models, _


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    fp_payment_method = fields.Selection([('cash', "Numerar"), ('card', "Card"), ('unknown', "Altă metodă")],
                                 _("Metodă de plată"))

class Journal(models.Model):
    _inherit="pos.payment.method"

    fp_type = fields.Selection([
            ("cash", _("Numerar")),
            ("check",_("Check")),
            ("card", _("Payment by card")),
            ("coupons",_("Payment with coupons")),
            ("card-numeral-back",_("Payment with card and numeral back")),
            ("ext-coupons", _("With external for the organization coupons")),
            ("packaging",_("With returning the packaging")),
            ("internal-usage",_("Internal usage")),
            ("damage", _("Payments damage")),
            ("bank", _("Bank Transfer")),
            ("reserved1", _("Reserved payment SR1")),
            ("reserved2", _("Reserved payment SR2"))], string=_("POS Payment Type"),
            help=_("Payment Type used in FP")
        )