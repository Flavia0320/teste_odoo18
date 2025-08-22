from odoo import models

class AccountEdiXmlUBLRO(models.AbstractModel):
    _inherit = "account.edi.xml.ubl_ro"

    def _export_invoice_vals(self, invoice):
        vals_list = super()._export_invoice_vals(invoice)
        if invoice.pos_order_ids and invoice.is_storno == False:
            vals_list["vals"]["document_type_code"] = 751
        return vals_list
