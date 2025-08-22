from odoo import api, fields, models, _
from odoo.exceptions import UserError
import requests

class PosConfig(models.Model):
    _inherit = "pos.config"
    
    fp_active = fields.Boolean(_("Fiscal Print active"))
    fp_access = fields.Selection([('internet', "Prin Internet"),('network', "In retea"), ('local', "Doar local")], _("Fiscal Print mode"))
    fp_server_url = fields.Char(_("Fprint Server URL"))
    fp_network_server_url = fields.Char(_("Fprint Network Server URL"))
    fp_localhost_server_url = fields.Char(_("Fprint Localhost Server URL"))
    fp_printer_name = fields.Char(_("Fprint Server Name"))
    fp_tax_group_ids = fields.One2many(
        "pos.config.tva",
        "config_id",
        _("FP Tax Group"),
        help="Mapare pentru TVA daca pe casa de marcat nu se poate face maparea automat.")
    fp_permit_comment = fields.Boolean(_("FP Permit comment bottom"))
    fp_userprotect = fields.Boolean(_("FP Protect User"))
    fp_operator = fields.Integer(_("FP Operator"))
    fp_password = fields.Integer(_("FP Password"))
    fp_async = fields.Boolean(_("FP Async"))
    fp_server_user = fields.Char(_("User Server casa de marcat"))
    fp_server_secret = fields.Char(_("Parola Server casa de marcat"))
    fp_report = fields.Many2one('ir.actions.report', string=_('FP Report'))
    fp_report_view = fields.Char(_("FP Report View"), help="View for FP report, if empty will use default report view")
    fp_report_dispo = fields.Many2one('ir.actions.report', string=_('FP Report'))
    fp_report_dispo_view = fields.Char(_("FP Report View"),help="View for FP report, if empty will use default report view")

    @api.onchange('fp_report', 'fp_report_dispo')
    def _compute_fp_report_view(self):
        self.fp_report_view = self.fp_report.report_name
        self.fp_report_dispo_view = self.fp_report_dispo.report_name

    def cmarcat_raport(self):
        r = requests.post("%s/raport" % (self.fp_server_url,), json=self._context)
    
class PosTVA(models.Model):
    _name = "pos.config.tva"
    _rec_name = 'tax_id'
    
    config_id = fields.Many2one("pos.config", _("Config ID"))
    tax_id = fields.Many2one("account.tax", _("Tax"), domain="[('type_tax_use','=','sale')]", required=True)
    tax_group = fields.Integer(_("Tax Group"), required=True)

    def getTax(self, tax_id):
        tax = self.filtered(lambda x: x.tax_id==tax_id)
        if not tax:
            raise UserError(_("No FP tax defined for %s") % tax_id.name)
        return tax.tax_group
    
