from odoo import api, fields, models
from .common_decl import inv_origin, op_type, partner_type
from odoo.tools import config
import threading


class AccountMove(models.Model):
    _name = "account.move"
    _inherit = ["account.move", "l10n.ro.mixin"]

    d394_id = fields.Many2one("l10_romania.report.d394")

    def l10n_ro_parse_vat_partner(self):
        partner = self.partner_id
        if (partner.parent_id and
                (partner.type == 'invoice' or partner.is_company)
            ) or not partner.parent_id:
            return partner
        elif (partner.parent_id
              and partner.type != 'invoice'
              and not partner.is_company):
            return self.commercial_partner_id
        return self.commercial_partner_id

    l10n_ro_special_regim = fields.Boolean("Ro Special Regime")
    l10n_ro_simple_invoice = fields.Boolean("Ro Simple Invoice")

    @api.onchange("l10n_ro_simple_invoice")
    def _onchange_l10n_ro_simple_invoice(self):
        if self.l10n_ro_simple_invoice and self.is_l10n_ro_record:
            self.l10n_ro_has_vat_number = True

    l10n_ro_has_vat_number = fields.Boolean("Ro Has VAT Number")

    l10n_ro_invoice_partner_display_vat = fields.Char(
        "Ro VAT Number",
        compute="_compute_l10n_ro_invoice_partner_display_vat",
        store=True,
    )

    @api.depends("commercial_partner_id", "partner_id")
    def _compute_l10n_ro_invoice_partner_display_vat(self):
        for s in self:
            l10n_ro_partner_vat = ""
            if s.is_l10n_ro_record:
                l10n_ro_partner_vat = (
                    s.l10n_ro_parse_vat_partner().vat or ""
                )
            s.l10n_ro_invoice_partner_display_vat = (
                l10n_ro_partner_vat
            )

    l10n_ro_invoice_origin_d394 = fields.Selection(
        inv_origin(), string="Document type", default="1"
    )

    l10n_ro_operation_type = fields.Selection(
        op_type(),
        compute="_compute_l10n_ro_operation_type",
        string="Operation Type",
        store=True,
    )

    @api.depends(
        "partner_id",
        "move_type",
        "fiscal_position_id",
        "l10n_ro_partner_type",
        "l10n_ro_invoice_origin_d394",
        "l10n_ro_simple_invoice",
        "l10n_ro_has_vat_number",
        "state",
    )
    def _compute_l10n_ro_operation_type(self):
        for inv in self:
            if inv.is_l10n_ro_record:
                fp = inv.company_id.l10n_ro_property_inverse_taxation_position_id
                if not fp:
                    fp = self.env["account.fiscal.position"].search(
                        [
                            ("company_id", "=", inv.company_id.id),
                            ("name", "=", "Regim Taxare Inversa"),
                        ]
                    )
                tva_fp = inv.company_id.l10n_ro_property_vat_on_payment_position_id
                if not tva_fp:
                    tva_fp = self.env["account.fiscal.position"].search(
                        [
                            ("company_id", "=", inv.company_id.id),
                            ("name", "=", "Regim TVA la Incasare"),
                        ]
                    )
                is_receipt = (
                    inv.move_type == "in_receipt"
                    and not inv.l10n_ro_simple_invoice
                    and not inv.l10n_ro_has_vat_number
                )
                if inv.commercial_partner_id:
                    identifier_type = inv.commercial_partner_id.l10n_ro_partner_type
                    if inv.move_type in ("out_invoice", "out_refund", "out_receipt"):
                        if inv.fiscal_position_id == fp:
                            oper_type = "V"
                        elif (
                            identifier_type in ("1", "2") and inv.l10n_ro_special_regim
                        ):
                            oper_type = "LS"
                        elif identifier_type in ("3", "4"):
                            oper_type = "V"
                        else:
                            oper_type = "L"
                    else:
                        if (
                            inv.l10n_ro_partner_type == "2"
                            and inv.l10n_ro_invoice_origin_d394
                        ):
                            oper_type = "N"
                        elif inv.l10n_ro_partner_type in ("3", "4"):
                            oper_type = "C"
                        elif inv.fiscal_position_id == fp:
                            oper_type = "C"
                        elif inv.l10n_ro_special_regim or is_receipt:
                            oper_type = "AS"
                        elif inv.fiscal_position_id == tva_fp:
                            oper_type = "AI"
                            vatp = inv.partner_id.with_context(
                                check_date=inv.invoice_date or fields.Date.today()
                            )._check_vat_on_payment()
                            test_enable = True
                            if (
                                not getattr(threading.currentThread(), "testing", False)
                                and not config.get("test_enable")
                                and not config.get("test_file")
                            ):
                                test_enable = False

                            if not vatp and not test_enable:
                                oper_type = "A"
                        else:
                            oper_type = "A"
                    inv.l10n_ro_operation_type = oper_type
        return True
    #
    # @api.onchange("partner_id", "company_id")
    # def _onchange_partner_id(self):
    #     """If partner is an affiliated person, use normal fiscal position,
    #     in case of changed done in vat on payment
    #     """
    #     result = super(AccountMove, self)._onchange_partner_id()
    #     if self.is_l10n_ro_record:
    #         delivery_partner = self.env['res.partner'].browse(
    #             self.partner_shipping_id.id
    #             or self.partner_id.address_get(['delivery'])['delivery']
    #         )
    #
    #         if self.partner_id in self.company_id.l10n_ro_affiliated_person_ids:
    #             self.fiscal_position_id = self.env[
    #                 "account.fiscal.position"
    #             ].get_fiscal_position(
    #                 self.partner_id.id, delivery_id=delivery_partner
    #             )
    #             self._recompute_dynamic_lines()
    #     return result
    #
    #
    # def _recompute_dynamic_lines(
    #     self, recompute_all_taxes=False, recompute_tax_base_amount=False
    # ):
    #     """Allow automatic calculation of inverse taxation with limit"""
    #     for inv in self:
    #         if inv.invoice_line_ids and inv.invoice_date and inv.is_l10n_ro_record:
    #             l10n_ro_anaf_inv_tax_limit = (
    #                 self.env["ir.config_parameter"]
    #                 .sudo()
    #                 .get_param("l10n_ro_anaf_inv_tax_limit")
    #             )
    #             l10n_ro_anaf_inv_tax_date = (
    #                 self.env["ir.config_parameter"]
    #                 .sudo()
    #                 .get_param("l10n_ro_anaf_inv_tax_date")
    #             )
    #             fp = inv.company_id.l10n_ro_property_inverse_taxation_position_id
    #             if not fp:
    #                 fp = self.env["account.fiscal.position"].search(
    #                     [
    #                         ("company_id", "=", inv.company_id.id),
    #                         ("name", "=", "Regim Taxare Inversa"),
    #                     ]
    #                 )
    #             is_anaf_inverse_tax = False
    #             if fp and inv.move_type not in ("out_receipt", "in_receipt"):
    #                 if (
    #                     l10n_ro_anaf_inv_tax_limit
    #                     and l10n_ro_anaf_inv_tax_date
    #                     and inv.l10n_ro_partner_type == "1"
    #                     and inv.invoice_date
    #                     <= fields.Date.to_date(l10n_ro_anaf_inv_tax_date)
    #                 ):
    #                     is_anaf_inverse_tax = True
    #             if is_anaf_inverse_tax:
    #                 anaf_codes = ["29", "30", "31"]
    #                 prod_lines = inv.invoice_line_ids.filtered(
    #                     lambda l: l.product_id.categ_id.anaf_code in anaf_codes
    #                 )
    #                 if prod_lines:
    #                     base_amount = sum(
    #                         line.tax_base_amount or -line.balance
    #                         for line in prod_lines
    #                     )
    #                     if base_amount >= int(l10n_ro_anaf_inv_tax_limit):
    #                         for line in prod_lines:
    #                             tax_ids = fp.map_tax(line.product_id.taxes_id)
    #                             line.tax_ids = tax_ids
    #                     else:
    #                         for line in prod_lines:
    #                             tax_ids = inv.fiscal_position_id.map_tax(
    #                                 line.product_id.taxes_id
    #                             )
    #                             line.tax_ids = tax_ids
    #     return super(AccountMove, self)._recompute_dynamic_lines(
    #         recompute_all_taxes, recompute_tax_base_amount
    #     )
