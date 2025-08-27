from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = "product.template"

    #TODO: de facut lista si indicatii in help/Label mai clare.
    #https://unserver.ro/info/winmentor/Nomenclator_Coduri_D394.pdf
    l10n_ro_anaf_code = fields.Char(string="Cod produs")

