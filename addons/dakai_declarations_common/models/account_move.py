from odoo import api, fields, models
from .common_decl import partner_type


class AccountMove(models.Model):
    _name = "account.move"
    _inherit = ["account.move", "l10n.ro.mixin"]

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

    l10n_ro_correction = fields.Boolean("Ro Correction Invoice")

    l10n_ro_partner_type = fields.Selection(
        partner_type(),
        compute="_compute_l10n_ro_partner_type",
        string="D394 Partner Type",
        store=True,
    )

    @api.depends("commercial_partner_id", "partner_id")
    def _compute_l10n_ro_partner_type(self):
        for s in self:
            identifier_type = "1"
            if s.is_l10n_ro_record and s.commercial_partner_id:
                identifier_type = s.l10n_ro_parse_vat_partner().l10n_ro_partner_type
            s.l10n_ro_partner_type = identifier_type

    @api.onchange("partner_id", "company_id")
    def _onchange_partner_id(self):
        """If partner is an affiliated person, use normal fiscal position,
        in case of changed done in vat on payment
        """
        result = super(AccountMove, self)._onchange_partner_id()
        if self.is_l10n_ro_record:
            delivery_partner = self.env['res.partner'].browse(
                self.partner_shipping_id.id
                or self.partner_id.address_get(['delivery'])['delivery']
            )

            if self.partner_id in self.company_id.l10n_ro_affiliated_person_ids:
                self.fiscal_position_id = self.env[
                    "account.fiscal.position"
                ].get_fiscal_position(
                    self.partner_id.id, delivery_id=delivery_partner
                )
                self._recompute_dynamic_lines()
        return result


    def _recompute_dynamic_lines(
        self, recompute_all_taxes=False, recompute_tax_base_amount=False
    ):
        """Allow automatic calculation of inverse taxation with limit"""
        for inv in self:
            if inv.invoice_line_ids and inv.invoice_date and inv.is_l10n_ro_record:
                l10n_ro_anaf_inv_tax_limit = (
                    self.env["ir.config_parameter"]
                    .sudo()
                    .get_param("l10n_ro_anaf_inv_tax_limit")
                )
                l10n_ro_anaf_inv_tax_date = (
                    self.env["ir.config_parameter"]
                    .sudo()
                    .get_param("l10n_ro_anaf_inv_tax_date")
                )
                fp = inv.company_id.l10n_ro_property_inverse_taxation_position_id
                if not fp:
                    fp = self.env["account.fiscal.position"].search(
                        [
                            ("company_id", "=", inv.company_id.id),
                            ("name", "=", "Regim Taxare Inversa"),
                        ]
                    )
                is_anaf_inverse_tax = False
                if fp and inv.move_type not in ("out_receipt", "in_receipt"):
                    if (
                        l10n_ro_anaf_inv_tax_limit
                        and l10n_ro_anaf_inv_tax_date
                        and inv.l10n_ro_partner_type == "1"
                        and inv.invoice_date
                        <= fields.Date.to_date(l10n_ro_anaf_inv_tax_date)
                    ):
                        is_anaf_inverse_tax = True
                if is_anaf_inverse_tax:
                    anaf_codes = ["29", "30", "31"]
                    prod_lines = inv.invoice_line_ids.filtered(
                        lambda l: l.product_id.categ_id.anaf_code in anaf_codes
                    )
                    if prod_lines:
                        base_amount = sum(
                            line.tax_base_amount or -line.balance
                            for line in prod_lines
                        )
                        if base_amount >= int(l10n_ro_anaf_inv_tax_limit):
                            for line in prod_lines:
                                tax_ids = fp.map_tax(line.product_id.taxes_id)
                                line.tax_ids = tax_ids
                        else:
                            for line in prod_lines:
                                tax_ids = inv.fiscal_position_id.map_tax(
                                    line.product_id.taxes_id
                                )
                                line.tax_ids = tax_ids
        return super(AccountMove, self)._recompute_dynamic_lines(
            recompute_all_taxes, recompute_tax_base_amount
        )
