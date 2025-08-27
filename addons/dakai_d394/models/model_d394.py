from dateutil.relativedelta import relativedelta

from odoo import fields, models


class Declaratie394(models.TransientModel):
    _name = "l10n.ro.anaf.d394.v4"
    _inherit = "l10n.ro.anaf.d394"
    _description = "declaratie D394, v4"

    def build_file(self):
        xmldict = self.generate_xmldict()
        data_file = self.generate_data_file(xmldict)
        return data_file

    def generate_xmldict(self):
        year, month = self.get_year_month()
        months = self.get_months_number()
        tip_D394 = "L"
        if months == 3:
            tip_D394 = "T"
        elif months == 6:
            tip_D394 = "S"
        elif months == 12:
            tip_D394 = "A"
        period_invoices = self.get_period_invoices(
            ["out_invoice", "out_refund", "in_invoice", "in_refund"], cancel=True
        )
        fsbf_domain = [
            ("move_type", "=", "in_receipt"),
            ("date", ">=", self.date_from),
            ("date", "<=", self.date_to),
            ("state", "=", "posted"),
            "|",
            ("company_id", "=", self.company_id.id),
            ("company_id", "in", self.company_id.child_ids.ids),
        ]
        fsbf_inv = (
            self.env["account.move"]
            .search(
                fsbf_domain,
                order="date, name, ref",
            )
            .filtered(lambda l: l.l10n_ro_simple_invoice or l.l10n_ro_has_vat_number)
        )
        period_invoices |= fsbf_inv
        period_invoices = period_invoices.sorted("date")
        decl_invoices = period_invoices.filtered(
            lambda i: i.l10n_ro_partner_type in ["1", "2"]
        )
        invoices = decl_invoices.filtered(lambda i: i.state == "posted")
        op1 = self._get_op1(invoices)
        op1 = [op for op in op1 if op["tip"] != "AS"]
        out_receipts = self.get_period_invoices(["out_receipt"])
        out_receipts = out_receipts.filtered(lambda i: i.journal_id.l10n_ro_fiscal_receipt)
        op2 = self._get_op2(out_receipts)

        payments = self._get_payments()

        xmldict = {
            "luna": month,
            "an": year,
            "tip_D394": tip_D394,
            "optiune": int(self.optiune),
            "prsAfiliat": int(self.prsAfiliat),
            "informatii": self._generate_informatii(decl_invoices, payments, op1, op2),
            "rezumat1": self._generate_rezumat1(op1),
            "rezumat2": self._generate_rezumat2(op1, op2),
            "serieFacturi": self._get_inv_series(period_invoices),
            "lista": self._generate_lista(),
            "facturi": self.generate_facturi(),
            "op1": [op for op in op1 if not op.get("simple_invoice")],
            "op2": op2,
        }

        for op in op1:
            if "simple_invoice" in op:
                del op["simple_invoice"]

        if self.schimb_optiune:
            xmldict["schimb_optiune"] = int(self.schimb_optiune)
            xmldict["optiune"] = int(self.schimb_optiune)
        if invoices or op2:
            xmldict.update({"op_efectuate": 1})
        else:
            xmldict.update({"op_efectuate": 0})
        totalPlataA = 0
        totalPlataA += (
            xmldict["informatii"]["nrCui1"]
            + xmldict["informatii"]["nrCui2"]
            + xmldict["informatii"]["nrCui3"]
            + xmldict["informatii"]["nrCui4"]
        )
        for line in xmldict["rezumat2"]:
            totalPlataA += line["bazaA"] + line["bazaL"] + line["bazaAI"]
        xmldict.update({"totalPlata_A": totalPlataA})

        company_data = self.generate_company_data()
        xmldict.update(company_data)

        sign = self.generate_sign()
        xmldict.update(sign)

        representative = self.generate_representative()
        xmldict.update(representative)
        return xmldict

    def generate_data_file(self, xmldict):
        data_file = """<?xml version="1.0" encoding="UTF-8"?>
                    <declaratie394
                    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                    xsi:schemaLocation="mfp:anaf:dgti:d394:declaratie:v4 D394.xsd"
                    xmlns="mfp:anaf:dgti:d394:declaratie:v4"
                    """
        for key, val in xmldict.items():
            if key not in (
                "informatii",
                "rezumat1",
                "rezumat2",
                "serieFacturi",
                "lista",
                "facturi",
                "op1",
                "op2",
            ):
                data_file += """{}="{}" """.format(key, val)
        data_file += """>"""
        data_file += """
        <informatii """
        for key, val in xmldict["informatii"].items():
            data_file += """{}="{}" """.format(key, val)
        data_file += """
        />"""
        for client in xmldict["rezumat1"]:
            data_file += """
        <rezumat1 """
            for key, val in client.items():
                if key != "detaliu":
                    data_file += """{}="{}" """.format(key, val)
            if client["detaliu"]:
                data_file += """>"""
                for line in client["detaliu"]:
                    data_file += """
            <detaliu """
                    for det_key, det_val in line.items():
                        data_file += """{}="{}" """.format(det_key, det_val)
                    data_file += """/>"""
                data_file += """
        </rezumat1>"""
            else:
                data_file += """/>"""
        for client in xmldict["rezumat2"]:
            data_file += """
        <rezumat2 """
            for key, val in client.items():
                data_file += """{}="{}" """.format(key, val)
            data_file += """/>"""
        for client in xmldict["serieFacturi"]:
            data_file += """
        <serieFacturi """
            for key, val in client.items():
                data_file += """{}="{}" """.format(key, val)
            data_file += """/>"""
        for client in xmldict["lista"]:
            data_file += """
        <lista """
            for key, val in client.items():
                data_file += """{}="{}" """.format(key, val)
            data_file += """/>"""
        for client in xmldict["facturi"]:
            data_file += """
        <facturi """
            for key, val in client.items():
                data_file += """{}="{}" """.format(key, val)
            data_file += """/>"""
        for client in xmldict["op1"]:
            data_file += """
        <op1 """
            for key, val in client.items():
                if key != "op11":
                    data_file += """{}="{}" """.format(key, val)
            if client.get("op11"):
                data_file += """>"""
                for line in client["op11"]:
                    data_file += """<op11 """
                    for key, val in line.items():
                        data_file += """{}="{}" """.format(key, val)
                    data_file += """/>"""
                data_file += """
        </op1>"""
            else:
                data_file += """/>"""
        for client in xmldict["op2"]:
            data_file += """
        <op2 """
            for key, val in client.items():
                data_file += """{}="{}" """.format(key, val)
            data_file += """/>"""
        data_file += """
        </declaratie394>"""
        if not self.optiune and self.schimb_optiune:
            self.company_id.l10n_ro_optiune = True
        elif self.optiune and self.schimb_optiune:
            self.company_id.l10n_ro_optiune = False
        return data_file

    def generate_company_data(self):
        if self.company_id.partner_id.l10n_ro_vat_number.find("RO") == 1:
            cui = int(self.company_id.partner_id.l10n_ro_vat_number[2:])
        else:
            cui = int(self.company_id.partner_id.l10n_ro_vat_number)
        comm_partner = self.company_id.partner_id.commercial_partner_id
        ctx = dict(self._context)
        ctx.update({"check_date": self.date_to})
        vat_payment = comm_partner.with_context(ctx)._check_vat_on_payment()
        data = {
            "cui": cui,
            "den": self.company_id.name.replace("&", "-").replace('"', ""),
            "adresa": self.company_id.partner_id._display_address(
                without_company=True
            ).replace("\n", ","),
            "telefon": self.company_id.phone,
            "mail": self.company_id.email,
            "caen": self.company_id.l10n_ro_caen_code,
            "sistemTVA": 1 if vat_payment else 0,
        }
        return data

    def generate_representative(self):
        representative = self.representative_id
        partner = self.company_id.partner_id
        if representative and representative != partner:
            partner = representative
        if partner.l10n_ro_vat_number.find("RO") == 1:
            cui = int(partner.l10n_ro_vat_number[2:])
        else:
            cui = int(partner.l10n_ro_vat_number)
        data = {
            "cifR": cui,
            "denR": partner.name.replace("&", "-").replace('"', ""),
            "functie_reprez": partner.function,
            "adresaR": partner._display_address(without_company=True).replace(
                "\n", ","
            ),
        }
        if representative and partner.id != representative.id:
            data.update(
                {
                    "telefonR": partner.phone,
                    "faxR": partner.fax,
                    "mailR": partner.email,
                }
            )
        return data

    def generate_sign(self):
        signer = self.signature_id
        if signer.type == "company":
            data = {
                "tip_intocmit": 0,
                "den_intocmit": signer.name.replace("&", "-").replace('"', ""),
                "cif_intocmit": signer.vat,
                "calitate_intocmit": signer.quality,
            }
        else:
            data = {
                "tip_intocmit": 1,
                "den_intocmit": signer.name.replace("&", "-").replace('"', ""),
                "cif_intocmit": signer.vat,
                "functie_intocmit": signer.quality,
            }
        return data

    def generate_facturi(self):
        tag_config = {
            "baza19": {"base_19"},
            "tva19": {"tva_19"},
            "baza9": {"base_9"},
            "tva9": {"tva_9"},
            "baza5": {"base_5"},
            "tva5": {"tva_5"},
        }
        inv_type_dict = {
            "baza24": 0,
            "baza20": 0,
            "baza19": 0,
            "baza9": 0,
            "baza5": 0,
            "tva24": 0,
            "tva20": 0,
            "tva19": 0,
            "tva9": 0,
            "tva5": 0,
        }
        facturi = []
        invoices1 = self.get_period_invoices(cancel=True)
        invoices = invoices1.filtered(
            lambda r: r.move_type == "out_refund"
            or r.state == "cancel"
            or r.journal_id.l10n_ro_sequence_type in ("autoinv1", "autoinv2")
        )

        for inv in invoices:
            inv_type = False
            if inv.move_type in ("out_invoice", "out_refund"):
                if inv.state == "cancel":
                    inv_type = 2
                elif inv.journal_id.l10n_ro_sequence_type == "autoinv1":
                    inv_type = 3
                elif inv.move_type == "out_refund":
                    inv_type = 1
            elif inv.journal_id.l10n_ro_sequence_type == "autoinv2":
                inv_type = 4
            if inv_type:
                new_dict = {
                    "tip_factura": inv_type,
                    "serie": inv.sequence_prefix,
                    "nr": inv.sequence_number,
                }
                if inv_type == 3:
                    new_dict.update(inv_type_dict)
                    vals = self.get_journal_line_vals(inv)
                    for key, value in tag_config.items():
                        if key not in new_dict:
                            new_dict[key] = 0
                        for tagx in value:
                            new_dict[key] += vals.get(tagx)
                    for key, value in new_dict.items():
                        if key in inv_type_dict:
                            new_dict[key] = int(round(value, 2))
                facturi.append(new_dict)
        return facturi

    def _get_payments(self):
        tag_config = {
            "base_19": {"base_19"},
            "tva_19": {"tva_19"},
            "base_9": {"base_9"},
            "tva_9": {"tva_9"},
            "base_5": {"base_5"},
            "tva_5": {"tva_5"},
        }
        pay_type_dict = {
            "base_24": 0,
            "base_20": 0,
            "base_19": 0,
            "base_9": 0,
            "base_5": 0,
            "tva_24": 0,
            "tva_20": 0,
            "tva_19": 0,
            "tva_9": 0,
            "tva_5": 0,
        }
        payments = []
        types = ["out_invoice", "out_refund", "in_invoice", "in_refund"]
        vatp_invoices = self.get_period_vatp_invoices(types)
        for inv1 in vatp_invoices:
            pay = {"type": inv1.move_type, "vat_on_payment": True}
            pay.update(pay_type_dict)
            vals = self.get_journal_line_vals(inv1)
            for _key, value in tag_config.items():
                if _key == "payments":
                    for inv_pay in value.get("payments"):
                        for tagx in inv_pay:
                            pay[tagx] += vals.get(tagx)
            payments.append(pay)
        return payments

    def _get_cota_list(self, partner_type, invoice_lines, oper_type):
        cota_list = []
        for inv_line in invoice_lines:
            sign = 1
            if "refund" in inv_line.move_id.move_type:
                sign = -1
            cotas = self.get_cota_vals(inv_line, sign=sign)
            for line in cotas:
                cota_line = list(
                    filter(
                        lambda r: r["cota"] == line.get("cota")
                        and r.get("anaf_code") == line.get("anaf_code"),
                        cota_list,
                    )
                )
                if cota_line:
                    cota_line = cota_line[0]
                    if inv_line.move_id.id not in cota_line["invoices"]:
                        cota_line["nr_fact"] += line.get("nr_fact")
                        cota_line["invoices"] += inv_line.move_id.ids
                    cota_line["base"] += line.get("base")
                    cota_line["vat"] += line.get("vat")
                else:
                    new_vals = {
                        "cota": line.get("cota"),
                        "nr_fact": line.get("nr_fact"),
                        "base": line.get("base"),
                        "vat": line.get("vat"),
                        "invoices": inv_line.move_id.ids,
                        "simple_invoice": (
                            inv_line.move_id.l10n_ro_simple_invoice
                            or inv_line.move_id.l10n_ro_has_vat_number
                        ),
                    }
                    require_code = False
                    if oper_type in ("V", "C"):
                        require_code = True
                    if (
                        partner_type == "2"
                        and line.get("cota") == 0
                        and oper_type == "N"
                    ):
                        require_code = True
                    if require_code:
                        new_vals["anaf_code"] = line.get("anaf_code")
                    cota_list.append(new_vals)
        return cota_list

    def _get_partner_type(self, invoices):
        # Get list of invoices by partner_type
        partner_type = {}
        for part_type in list(set(invoices.mapped("l10n_ro_partner_type"))):
            partner_type[part_type] = invoices.filtered(
                lambda i: i.l10n_ro_partner_type == part_type
            )
        return partner_type

    def _get_operation_type(self, invoices):
        # Get list of invoices by operation_type
        operation_type = {}
        for invoice in invoices:
            inv_lines = invoice.invoice_line_ids
            for line in inv_lines:
                new_oper_type = line.move_id.l10n_ro_operation_type
                is_inverse_tax = False
                for tax in line.tax_ids:
                    if "invers" in tax.name.lower():
                        is_inverse_tax = True
                if is_inverse_tax:
                    if line.move_id.move_type in ["out_invoice", "out_refund"]:
                        new_oper_type = "V"
                    else:
                        new_oper_type = "C"
                if new_oper_type in operation_type:
                    operation_type[new_oper_type] |= line
                else:
                    operation_type[new_oper_type] = line
        return operation_type

    def _get_partner_data(self, new_dict, partner, partner_type):
        if partner_type == "1":
            new_dict["cuiP"] = partner._split_vat(partner.vat)[1]
        elif partner_type == "2":
            if partner.vat:
                new_dict["cuiP"] = partner._split_vat(partner.vat)[1]
            else:
                if partner.country_id:
                    new_dict["taraP"] = (
                        partner.country_id and partner.country_id.code.upper()
                    )
                if partner.city:
                    new_dict["locP"] = partner.city
                if partner.state_id:
                    new_dict["judP"] = (
                        partner.state_id and partner.state_id.l10n_ro_order_code
                    )
                if partner.street:
                    new_dict["strP"] = partner.street
                else:
                    new_dict["strP"] = ""
                if partner.street2:
                    new_dict["strP"] += partner.street2
                    new_dict["detP"] = partner.street2
                if "strP" in new_dict.keys():
                    new_dict["strP"] = new_dict["strP"][:75]
        else:
            new_dict["cuiP"] = partner._split_vat(partner.vat)[1]
        return new_dict

    def _get_vat_data(self, part_invoices, partner, partner_type, doc_type=False):
        denP = partner.name.replace("&", "-").replace('"', "")
        line = self._get_operation_type(part_invoices)
        res_dict = []
        for oper_type, move_lines in line.items():
            partner_dict = {
                "tip": oper_type,
                "tip_partener": partner_type,
                "denP": denP,
            }
            if oper_type == "N" and doc_type:
                partner_dict["tip_document"] = doc_type
            partner_dict = self._get_partner_data(
                partner_dict, partner.commercial_partner_id, partner_type
            )
            cota_list = self._get_cota_list(partner_type, move_lines, oper_type)
            for line_list in cota_list:
                new_oper_type = oper_type

                cota = line_list.get("cota")
                if cota == 0:
                    if cota == 0 and new_oper_type in ("A", "AI"):
                        new_oper_type = "AS"
                    elif cota == 0 and new_oper_type == "L":
                        new_oper_type = "LS"
                cota_lines = list(
                    filter(
                        lambda r: r["cota"] == line_list.get("cota")
                        and r["tip"] == new_oper_type
                        and r["simple_invoice"] == line_list.get("simple_invoice"),
                        res_dict,
                    )
                )
                if cota_lines:
                    for cota_line in cota_lines:
                        cota_line["nrFact"] += line_list.get("nr_fact")
                        cota_line["baza"] += line_list.get("base")
                        if cota != 0:
                            cota_line["tva"] += line_list.get("vat")
                        if line_list.get("anaf_code", "") != "":
                            anaf_code_line = list(
                                filter(
                                    lambda r: r["codPR"] == line_list.get("anaf_code"),
                                    cota_line["op11"],
                                )
                            )
                            if anaf_code_line:
                                cota_line["nrFactPR"] += line_list.get("nr_fact")
                                cota_line["bazaPR"] += line_list.get("base")
                                if cota != 0:
                                    cota_line["tvaPR"] += line_list.get("vat")
                            else:
                                op11_dict = {
                                    "nrFactPR": line_list.get("nr_fact"),
                                    "bazaPR": line_list.get("base"),
                                    "codPR": line_list.get("anaf_code"),
                                }
                                if cota != 0:
                                    op11_dict.update({"tvaPR": line_list.get("vat")})
                                cota_line["op11"].append(op11_dict)
                else:
                    new_dict = partner_dict.copy()
                    new_dict.update(
                        {
                            "cota": line_list.get("cota"),
                            "nrFact": line_list.get("nr_fact"),
                            "baza": line_list.get("base"),
                            "tip": new_oper_type,
                            "simple_invoice": line_list.get("simple_invoice"),
                        }
                    )
                    if cota != 0:
                        new_dict.update({"tva": line_list.get("vat")})
                    if line_list.get("anaf_code", "") != "":
                        op11_dict = {
                            "nrFactPR": line_list.get("nr_fact"),
                            "bazaPR": line_list.get("base"),
                            "codPR": line_list.get("anaf_code"),
                        }
                        if cota != 0:
                            op11_dict.update({"tvaPR": line_list.get("vat")})
                        new_dict["op11"] = [op11_dict]
                    res_dict.append(new_dict)
        for line in res_dict:
            line["baza"] = int(round(line["baza"]))
            if "tva" in line:
                line["tva"] = int(round(line["tva"]))
            if line.get("op11"):
                for op11 in line["op11"]:
                    op11["bazaPR"] = int(round(op11["bazaPR"]))
                    if "tvaPR" in op11:
                        op11["tvaPR"] = int(round(op11["tvaPR"]))
        return res_dict

    def _get_op1(self, invoices):
        self.ensure_one()
        op1 = []
        partner_types = self._get_partner_type(invoices)
        for partner_type, part_types_inv in partner_types.items():
            partners = part_types_inv.mapped("commercial_partner_id")
            for partner in partners:
                part_invoices = part_types_inv.filtered(
                    lambda r: r.commercial_partner_id.id == partner.id
                )
                new_dict = {}
                if partner_type == "2":
                    doc_types = list(
                        set(part_invoices.mapped("l10n_ro_invoice_origin_d394"))
                    )
                    for doc_type in doc_types:
                        doctype_invoices = part_invoices.filtered(
                            lambda r: r.l10n_ro_invoice_origin_d394 == doc_type
                        )
                        new_dict = self._get_vat_data(
                            doctype_invoices, partner, partner_type, doc_type
                        )
                else:
                    doctype_invoices = part_invoices
                    new_dict = self._get_vat_data(
                        doctype_invoices, partner, partner_type
                    )
                if new_dict:
                    op1 += new_dict
        return op1

    def compute_invoice_taxes_ammount(self, invoices):
        """Helper to get the taxes grouped according their account.tax.group.
        This method is only used when printing the invoice.
        """
        ress = []
        for move in invoices:
            inv_groups = move.amount_by_group
            for group in inv_groups:
                found = False
                for group_f in ress:
                    if group_f[0] == group[0]:
                        group_f[1]["base"] += group[1]
                        group_f[1]["amount"] += group[2]
                        found = True
                if not found:
                    ress.append(group)
        return ress

    def _get_op2(self, receipts):
        op2 = []
        oper_type = "I1"
        months = {fields.Date.from_string(receipt.date).month for receipt in receipts}
        for month in months:
            month_rec = receipts.filtered(
                lambda r: fields.Date.from_string(r.date).month == month
            )
            nrAMEF = len({receipt.journal_id.id for receipt in month_rec})
            nrBF = len(month_rec)
            total = 0
            baza20 = baza19 = baza9 = baza5 = 0
            tva20 = tva19 = tva9 = tva5 = 0
            for receipt in month_rec:
                line_vals = self.get_journal_line_vals(receipt)
                total += line_vals.get("total")
                baza19 += line_vals.get("base_19")
                tva19 += line_vals.get("tva_19")
                baza9 += line_vals.get("base_9")
                tva9 += line_vals.get("tva_9")
                baza5 += line_vals.get("base_5")
                tva5 += line_vals.get("tva_5")
            if month_rec:
                op2.append(
                    {
                        "tip_op2": oper_type,
                        "luna": list(months)[0],
                        "nrAMEF": int(round(nrAMEF)),
                        "nrBF": int(round(nrBF)),
                        "total": int(round(total)),
                        "baza20": int(round(baza20)),
                        "baza19": int(round(baza19)),
                        "baza9": int(round(baza9)),
                        "baza5": int(round(baza5)),
                        "TVA20": int(round(tva20)),
                        "TVA19": int(round(tva19)),
                        "TVA9": int(round(tva9)),
                        "TVA5": int(round(tva5)),
                    }
                )
        return op2

    def _generate_rezumat1(self, op1):
        self.ensure_one()
        rezumat1 = []
        partner_types = {x["tip_partener"] for x in op1}
        for partner_type in partner_types:
            cotas = {x["cota"] for x in op1 if x["tip_partener"] == partner_type}
            for cota in cotas:
                if partner_type == "2":
                    doc_types = {
                        x["tip_document"]
                        for x in op1
                        if x["tip_partener"] == partner_type and x["tip"] == "N"
                    }
                    for doc_type in doc_types:
                        op1s = [
                            x
                            for x in op1
                            if x["tip_partener"] == partner_type
                            and x["cota"] == cota
                            and x["tip"] == "N"
                            and x.get("tip_document") == doc_type
                        ]
                        if op1s:
                            rezumat1.append(self.generate_rezumat1(op1s))
                    op1s = [
                        x
                        for x in op1
                        if x["tip_partener"] == partner_type
                        and x["cota"] == cota
                        and x["tip"] != "N"
                    ]
                    if op1s:
                        rezumat1.append(self.generate_rezumat1(op1s))
                else:
                    op1s = [
                        x
                        for x in op1
                        if x["tip_partener"] == partner_type and x["cota"] == cota
                    ]
                    if op1s:
                        rezumat1.append(self.generate_rezumat1(op1s))
        return rezumat1

    def get_sum_conditional(
        self, op1s, tag, field=False, value=False, cota=False, simple_invoices=True
    ):
        result = 0

        if not simple_invoices:
            op1s = list(filter(lambda r: not r.get("simple_invoice"), op1s))

        if cota and field and value:
            domain_op1s = [
                op for op in op1s if op[field] == value and op["cota"] == cota
            ]
        elif field and value:
            domain_op1s = [op for op in op1s if op[field] == value]
        elif cota:
            domain_op1s = [op for op in op1s if op["cota"] == cota]
        else:
            domain_op1s = op1s
        try:
            result = int(round(sum(op[tag] for op in domain_op1s)))
        except Exception:
            pass
        return result

    def generate_rezumat1(self, op1s):
        self.ensure_one()
        partner_type = op1s[0]["tip_partener"]
        cota_amount = int(op1s[0]["cota"])
        rezumat1 = {}
        rezumat1["tip_partener"] = op1s[0]["tip_partener"]
        rezumat1["cota"] = op1s[0]["cota"]
        if cota_amount != 0:
            rezumat1["facturiL"] = self.get_sum_conditional(
                op1s, "nrFact", "tip", "L", rezumat1["cota"], simple_invoices=False
            )
            rezumat1["bazaL"] = self.get_sum_conditional(
                op1s, "baza", "tip", "L", rezumat1["cota"], simple_invoices=False
            )
            rezumat1["tvaL"] = self.get_sum_conditional(
                op1s, "tva", "tip", "L", rezumat1["cota"], simple_invoices=False
            )
        if partner_type in ("1", "2") and cota_amount == 0:
            if op1s[0].get("tip_document") == "1":
                rezumat1["facturiLS"] = 0
                rezumat1["bazaLS"] = 0
            elif not op1s[0].get("tip_document"):
                rezumat1["facturiLS"] = self.get_sum_conditional(
                    op1s, "nrFact", "tip", "LS", rezumat1["cota"]
                )
                rezumat1["bazaLS"] = self.get_sum_conditional(
                    op1s, "baza", "tip", "LS", rezumat1["cota"]
                )
        if partner_type == "1" and cota_amount != 0:
            rezumat1["facturiA"] = self.get_sum_conditional(
                op1s, "nrFact", "tip", "A", rezumat1["cota"], simple_invoices=False
            )
            rezumat1["bazaA"] = self.get_sum_conditional(
                op1s, "baza", "tip", "A", rezumat1["cota"], simple_invoices=False
            )
            rezumat1["tvaA"] = self.get_sum_conditional(
                op1s, "tva", "tip", "A", rezumat1["cota"], simple_invoices=False
            )
        if partner_type == "1" and cota_amount != 0:
            rezumat1["facturiAI"] = self.get_sum_conditional(
                op1s, "nrFact", "tip", "AI", rezumat1["cota"], simple_invoices=False
            )
            rezumat1["bazaAI"] = self.get_sum_conditional(
                op1s, "baza", "tip", "AI", rezumat1["cota"], simple_invoices=False
            )
            rezumat1["tvaAI"] = self.get_sum_conditional(
                op1s, "tva", "tip", "AI", rezumat1["cota"], simple_invoices=False
            )
        if partner_type in ("1", "3", "4") and cota_amount == 0:
            rezumat1["facturiAS"] = self.get_sum_conditional(
                op1s, "nrFact", "tip", "AS", rezumat1["cota"]
            )
            rezumat1["bazaAS"] = self.get_sum_conditional(
                op1s, "baza", "tip", "AS", rezumat1["cota"]
            )
        if (partner_type == "1") and (cota_amount == 0):
            rezumat1["facturiV"] = self.get_sum_conditional(
                op1s, "nrFact", "tip", "V", rezumat1["cota"]
            )
            rezumat1["bazaV"] = self.get_sum_conditional(
                op1s, "baza", "tip", "V", rezumat1["cota"]
            )
        if (partner_type != "2") and (cota_amount != 0):
            rezumat1["facturiC"] = self.get_sum_conditional(
                op1s, "nrFact", "tip", "C", rezumat1["cota"]
            )
            rezumat1["bazaC"] = self.get_sum_conditional(
                op1s, "baza", "tip", "C", rezumat1["cota"]
            )
            rezumat1["tvaC"] = self.get_sum_conditional(
                op1s, "tva", "tip", "C", rezumat1["cota"]
            )
        if op1s[0]["tip_partener"] == "2" and ("tip_document" in op1s[0]):
            rezumat1["facturiN"] = self.get_sum_conditional(
                op1s, "nrFact", "tip", "N", rezumat1["cota"]
            )
            rezumat1["document_N"] = op1s[0]["tip_document"]
            rezumat1["bazaN"] = self.get_sum_conditional(
                op1s, "baza", "tip", "N", rezumat1["cota"]
            )
        op1s = [x for x in op1s if "op11" in x]
        rez_detaliu = self._get_detaliu(op1s, partner_type)

        rezumat1["detaliu"] = rez_detaliu
        return rezumat1

    def _get_detaliu(self, op1s, partner_type):
        def init_detaliu(op1, partner_type, val):
            # if op1["tip"] == "L" and not val.get("nrLiv"):
            #     val["nrLiv"] = int(round(line["nrFactPR"]))
            #     val["bazaLiv"] = int(round(line["bazaPR"]))
            #     val["tvaLiv"] = int(round(line["tvaPR"]))
            if op1["tip"] == "V" and not val.get("nrLivV"):
                val["nrLivV"] = int(round(line["nrFactPR"]))
                val["bazaLivV"] = int(round(line["bazaPR"]))
                # val['tvaLivV'] = int(round(line['tvaPR']))
            # if op1["tip"] == "A" and not val.get("nrAchiz"):
            #     val["nrAchiz"] = int(round(line["nrFactPR"]))
            #     val["bazaAchiz"] = int(round(line["bazaPR"]))
            #     val["tvaAchiz"] = int(round(line["tvaPR"]))
            # if op1["tip"] == "AI" and not val.get("nrAchizAI"):
            #     val["nrAchizAI"] = int(round(line["nrFactPR"]))
            #     val["bazaAchizAI"] = int(round(line["bazaPR"]))
            #     val["tvaAchizAI"] = int(round(line["tvaPR"]))
            if op1["tip"] == "C" and not val.get("nrAchizC"):
                val["nrAchizC"] = int(round(line["nrFactPR"]))
                val["bazaAchizC"] = int(round(line["bazaPR"]))
                val["tvaAchizC"] = int(round(line["tvaPR"]))
            if op1["tip"] == "N" and partner_type == "2" and not val.get("nrN"):
                val["nrN"] = int(round(line["nrFactPR"]))
                val["valN"] = int(round(line["bazaPR"]))
            return val

        obj_d394_code = self.env["l10n.ro.anaf.product.code"]
        rez_detaliu = []
        for op1 in op1s:
            for line in op1["op11"]:
                code = line["codPR"]
                new_code = obj_d394_code.search([("name", "=", code)])
                if len(new_code) >= 2:
                    new_code = new_code[0]
                if new_code and new_code.parent_id:
                    new_code = new_code.parent_id
                found = False
                for val in rez_detaliu:
                    if new_code.name == val["bun"]:
                        found = True
                if found:
                    for val in rez_detaliu:
                        if new_code.name == val["bun"]:
                            val = init_detaliu(op1, partner_type, val)
                            # if op1["tip"] == "L":
                            #     val["nrLiv"] += int(round(line["nrFactPR"]))
                            #     val["bazaLiv"] += int(round(line["bazaPR"]))
                            #     val["tvaLiv"] += int(round(line["tvaPR"]))
                            if op1["tip"] == "V" and op1["cota"] == 0:
                                val["nrLivV"] += int(round(line["nrFactPR"]))
                                val["bazaLivV"] += int(round(line["bazaPR"]))
                                # val['tvaLivV'] += int(round(line['tvaPR']))
                            # if op1["tip"] == "A":
                            #     val["nrAchiz"] += int(round(line["nrFactPR"]))
                            #     val["bazaAchiz"] += int(round(line["bazaPR"]))
                            #     val["tvaAchiz"] += int(round(line["tvaPR"]))
                            # if op1["tip"] == "AI":
                            #     val["nrAchizAI"] += int(round(line["nrFactPR"]))
                            #     val["bazaAchizAI"] += int(round(line["bazaPR"]))
                            #     val["tvaAchizAI"] += int(round(line["tvaPR"]))
                            if op1["tip"] == "C" and op1["cota"] != 0:
                                val["nrAchizC"] += int(round(line["nrFactPR"]))
                                val["bazaAchizC"] += int(round(line["bazaPR"]))
                                val["tvaAchizC"] += int(round(line["tvaPR"]))
                            if op1["tip"] == "N" and partner_type == "2":
                                val["nrN"] += int(round(line["nrFactPR"]))
                                val["valN"] += int(round(line["bazaPR"]))
                else:
                    val = init_detaliu(op1, partner_type, {})
                    val["bun"] = new_code.name
                    rez_detaliu.append(val)
        return rez_detaliu

    def generate_rezumat2(
        self,
        cota,
        op1s,
        op2,
        out_receipts_slcod_op1,
        out_receipts_sl_op1,
        in_receipts_fsa_op1,
        in_receipts_fsai_op1,
        in_receipts_bfai_op1,
    ):
        self.ensure_one()
        rezumat2 = {}
        cota_amount = int(cota)
        rezumat2["cota"] = cota

        rezumat2["bazaFSLcod"] = self.get_sum_conditional(
            out_receipts_slcod_op1, "baza", cota=rezumat2["cota"]
        )
        rezumat2["TVAFSLcod"] = self.get_sum_conditional(
            out_receipts_slcod_op1, "tva", cota=rezumat2["cota"]
        )
        rezumat2["bazaFSL"] = self.get_sum_conditional(
            out_receipts_sl_op1, "baza", cota=rezumat2["cota"]
        )
        rezumat2["TVAFSL"] = self.get_sum_conditional(
            out_receipts_sl_op1, "tva", cota=rezumat2["cota"]
        )

        rezumat2["bazaFSA"] = self.get_sum_conditional(
            in_receipts_fsa_op1, "baza", cota=rezumat2["cota"]
        )
        rezumat2["TVAFSA"] = self.get_sum_conditional(
            in_receipts_fsa_op1, "tva", cota=rezumat2["cota"]
        )
        rezumat2["bazaFSAI"] = self.get_sum_conditional(
            in_receipts_fsai_op1, "baza", cota=rezumat2["cota"]
        )
        rezumat2["TVAFSAI"] = self.get_sum_conditional(
            in_receipts_fsai_op1, "tva", cota=rezumat2["cota"]
        )
        rezumat2["bazaBFAI"] = self.get_sum_conditional(
            in_receipts_bfai_op1, "baza", cota=rezumat2["cota"]
        )
        rezumat2["TVABFAI"] = self.get_sum_conditional(
            in_receipts_bfai_op1, "tva", cota=rezumat2["cota"]
        )

        rezumat2["nrFacturiL"] = self.get_sum_conditional(op1s, "nrFact", "tip", "L")
        rezumat2["bazaL"] = self.get_sum_conditional(op1s, "baza", "tip", "L")
        rezumat2["tvaL"] = self.get_sum_conditional(op1s, "tva", "tip", "L")

        rezumat2["nrFacturiA"] = self.get_sum_conditional(
            op1s, "nrFact", "tip", "A", simple_invoices=False
        ) + self.get_sum_conditional(op1s, "nrFact", "tip", "C")
        rezumat2["bazaA"] = self.get_sum_conditional(
            op1s, "baza", "tip", "A", simple_invoices=False
        ) + self.get_sum_conditional(op1s, "baza", "tip", "C")
        rezumat2["tvaA"] = self.get_sum_conditional(
            op1s, "tva", "tip", "A", simple_invoices=False
        ) + self.get_sum_conditional(op1s, "tva", "tip", "C")
        rezumat2["nrFacturiAI"] = self.get_sum_conditional(
            op1s, "nrFact", "tip", "AI", simple_invoices=False
        )
        rezumat2["bazaAI"] = self.get_sum_conditional(
            op1s, "baza", "tip", "AI", simple_invoices=False
        )
        rezumat2["tvaAI"] = self.get_sum_conditional(
            op1s, "tva", "tip", "AI", simple_invoices=False
        )

        if cota_amount == 5:
            rezumat2["baza_incasari_i1"] = self.get_sum_conditional(
                op2, "baza5", "tip_op2", "I1"
            )
            rezumat2["tva_incasari_i1"] = self.get_sum_conditional(
                op2, "TVA5", "tip_op2", "I1"
            )
            rezumat2["baza_incasari_i2"] = self.get_sum_conditional(
                op2, "baza5", "tip_op2", "I2"
            )
            rezumat2["tva_incasari_i2"] = self.get_sum_conditional(
                op2, "TVA5", "tip_op2", "I2"
            )
        elif cota_amount == 9:
            rezumat2["baza_incasari_i1"] = self.get_sum_conditional(
                op2, "baza9", "tip_op2", "I1"
            )
            rezumat2["tva_incasari_i1"] = self.get_sum_conditional(
                op2, "TVA9", "tip_op2", "I1"
            )
            rezumat2["baza_incasari_i2"] = self.get_sum_conditional(
                op2, "baza9", "tip_op2", "I2"
            )
            rezumat2["tva_incasari_i2"] = self.get_sum_conditional(
                op2, "TVA9", "tip_op2", "I2"
            )
        elif cota_amount == 19:
            rezumat2["baza_incasari_i1"] = self.get_sum_conditional(
                op2, "baza19", "tip_op2", "I1"
            )
            rezumat2["tva_incasari_i1"] = self.get_sum_conditional(
                op2, "TVA19", "tip_op2", "I1"
            )
            rezumat2["baza_incasari_i2"] = self.get_sum_conditional(
                op2, "baza19", "tip_op2", "I2"
            )
            rezumat2["tva_incasari_i2"] = self.get_sum_conditional(
                op2, "TVA19", "tip_op2", "I2"
            )
        else:
            rezumat2["baza_incasari_i1"] = 0
            rezumat2["tva_incasari_i1"] = 0
            rezumat2["baza_incasari_i2"] = 0
            rezumat2["tva_incasari_i2"] = 0

        rezumat2["bazaL_PF"] = 0
        rezumat2["tvaL_PF"] = 0
        return rezumat2

    def _generate_rezumat2(self, op1, op2):
        self.ensure_one()
        fp = self.company_id.l10n_ro_property_vat_on_payment_position_id
        if not fp:
            fp = self.env["account.fiscal.position"].search(
                [
                    ("company_id", "=", self.company_id.id),
                    ("name", "=", "Regim TVA la Incasare"),
                ]
            )
        rezumat2 = []
        out_receipts = self.get_period_invoices(["out_receipt"])
        out_receipts_slcod = out_receipts.filtered(
            lambda i: i.l10n_ro_partner_type in ["1", "2"]
            and i.line_ids.mapped("tax_ids")
            and i.l10n_ro_simple_invoice
            and i.l10n_ro_has_vat_number
        )
        out_receipts_sl = out_receipts.filtered(
            lambda i: i.l10n_ro_partner_type in ["1", "2"]
            and i.line_ids.mapped("tax_ids")
            and i.l10n_ro_simple_invoice
            and not i.l10n_ro_has_vat_number
        )

        in_receipts = self.get_period_invoices(["in_receipt"])
        in_receipts_fsa = in_receipts.filtered(
            lambda i: i.l10n_ro_partner_type in ["1", "2"]
            and i.line_ids.mapped("tax_ids")
            and i.l10n_ro_simple_invoice
            and i.l10n_ro_has_vat_number
        )
        in_receipts_fsai = in_receipts.filtered(
            lambda i: i.l10n_ro_partner_type in ["1", "2"]
            and i.line_ids.mapped("tax_ids")
            and i.l10n_ro_simple_invoice
            and i.l10n_ro_has_vat_number
            and i.fiscal_position_id == fp
        )
        in_receipts_bfai = in_receipts.filtered(
            lambda i: i.l10n_ro_partner_type in ["1", "2"]
            and i.line_ids.mapped("tax_ids")
            and not i.l10n_ro_simple_invoice
            and i.l10n_ro_has_vat_number
        )

        out_receipts_slcod_op1 = self._get_op1(out_receipts_slcod)
        out_receipts_sl_op1 = self._get_op1(out_receipts_sl)
        in_receipts_fsa_op1 = self._get_op1(in_receipts_fsa)
        in_receipts_fsai_op1 = self._get_op1(in_receipts_fsai)
        in_receipts_bfai_op1 = self._get_op1(in_receipts_bfai)

        cotas = set([x["cota"] for x in op1 if x["cota"] != 0] + [5, 9, 19])
        for cota in cotas:
            op1s = [x for x in op1 if x["cota"] == cota]
            rezumat2.append(
                self.generate_rezumat2(
                    cota,
                    op1s,
                    op2,
                    out_receipts_slcod_op1,
                    out_receipts_sl_op1,
                    in_receipts_fsa_op1,
                    in_receipts_fsai_op1,
                    in_receipts_bfai_op1,
                )
            )
        return rezumat2

    def _generate_lista(self):
        self.ensure_one()
        obj_tax = self.env["account.tax"]
        obj_invoice = self.env["account.move"]
        obj_inv_line = self.env["account.move.line"]
        comp_curr = self.company_id.currency_id
        caens = [
            "1071",
            "4520",
            "4730",
            "47761",
            "47762",
            "4932",
            "55101",
            "55102",
            "55103",
            "5630",
            "0812",
            "9313",
            "9602",
            "9603",
        ]
        lista = []
        invoices = obj_invoice.search(
            [
                ("move_type", "in", ["out_invoice", "out_refund"]),
                ("payment_state", "in", ["paid"]),
                ("date", ">=", self.date_from),
                ("date", "<=", self.date_to),
                ("move_type", "!=", "out_receipt"),
                "|",
                ("company_id", "=", self.company_id.id),
                ("company_id", "in", self.company_id.child_ids.ids),
            ]
        )

        companies = set(invoices.mapped("company_id.id"))

        for company in self.env["res.company"].browse(companies):

            if company.l10n_ro_caen_code.zfill(4) in caens:
                comp_inv = invoices.filtered(lambda r: r.company_id.id == company.id)
                cotas = []
                for invoice in comp_inv:
                    for line in invoice.invoice_line_ids:
                        cotas += [tax.id for tax in line.tax_ids]
                cotas = set(cotas)
                for cota in obj_tax.browse(cotas):
                    cota_amount = 0
                    if cota.amount_type == "percent":
                        if cota.children_tax_ids:
                            cota_amount = int(abs(cota.child_ids[0].amount) * 100)
                        else:
                            cota_amount = int(cota.amount * 100)
                    elif cota.amount_type == "amount":
                        cota_amount = int(cota.amount)
                    cota_inv = comp_inv.filtered(
                        lambda r: cota.id in r.invoice_line_ids.tax_ids.ids
                    )
                    inv_lines = obj_inv_line.search([("move_id", "in", cota_inv.ids)])
                    bazab = bazas = tvab = tvas = 0
                    for line in inv_lines:
                        inv_curr = line.move_id.currency_id
                        inv_date = line.move_id.date
                        if line.product_id.type in ("product", "consu"):
                            bazab += inv_curr._convert(
                                line.price_subtotal,
                                comp_curr,
                                line.company_id,
                                inv_date,
                            )
                            tvab += inv_curr._convert(
                                line.tax_base_amount,
                                comp_curr,
                                line.company_id,
                                inv_date,
                            )
                        else:
                            bazas += inv_curr._convert(
                                line.price_subtotal,
                                comp_curr,
                                line.company_id,
                                inv_date,
                            )
                            tvas += inv_curr._convert(
                                line.tax_base_amount,
                                comp_curr,
                                line.company_id,
                                inv_date,
                            )
                    if bazab != 0:
                        bdict = {
                            "caen": company.l10n_ro_caen_code.zfill(4),
                            "cota": cota_amount,
                            "operat": 1,
                            "valoare": int(round(bazab)),
                            "tva": int(round(tvab)),
                        }
                        lista.append(bdict)
                    if bazas != 0:
                        sdict = {
                            "caen": company.l10n_ro_caen_code.zfill(4),
                            "cota": cota_amount,
                            "operat": 2,
                            "valoare": int(round(bazas)),
                            "tva": int(round(tvas)),
                        }
                        lista.append(sdict)
        return lista

    def _get_inv_series(self, invoices):
        # Se declara toate secventele, plus plaja de numere alocate
        ctx = self._context.copy()
        year, month = self.get_year_month()
        ctx["fiscalyear_id"] = year
        date_from = fields.Date.from_string(self.date_from)
        year_date_from = date_from + relativedelta(day=1, month=1)

        yearly_anaf = self.env["l10n.ro.anaf.mixin"].create(
            {
                "company_id": self.company_id.id,
                "date_from": year_date_from,
                "date_to": self.date_to,
            }
        )

        yearly_invoices = yearly_anaf.get_period_invoices(
            ["out_invoice", "out_refund", "in_invoice", "in_refund"]
        )

        journal_obj = self.env["account.journal"]
        journal_ids = set(yearly_invoices.mapped("journal_id.id"))
        seq_dict = []
        for journal in journal_obj.browse(journal_ids):
            journal = journal.sudo()
            if journal.type == "sale" or journal.l10n_ro_sequence_type == "autoinv2":
                tip = 1
                nr_init = nr_last = 1
                partner = journal.l10n_ro_partner_id
                journal_invoices = invoices.filtered(
                    lambda r: r.journal_id.id == journal.id
                )
                year_journal_invoices = yearly_invoices.filtered(
                    lambda r: r.journal_id.id == journal.id
                )
                seria = ""
                if journal_invoices:
                    first_name = min(journal_invoices._origin.mapped("name"))
                    (
                        formatt,
                        format_values,
                    ) = journal_invoices._get_sequence_format_param(
                        journal_invoices[-1].name
                    )
                    seria = str(formatt).split("{seq:")[0].format(**format_values)
                elif year_journal_invoices:
                    first_name = min(year_journal_invoices._origin.mapped("name"))
                    (
                        formatt,
                        format_values,
                    ) = year_journal_invoices._get_sequence_format_param(
                        year_journal_invoices[-1].name
                    )
                    seria = str(formatt).split("{seq:")[0].format(**format_values)
                if not seria:
                    seria = journal.code

                # Add allocated numbers
                if journal.l10n_ro_journal_sequence_number_id:
                    date_ranges = (
                        journal.l10n_ro_journal_sequence_number_id.date_range_ids
                    )
                    year_range = date_ranges.filtered(
                        lambda dr: dr.date_from == year_date_from
                    )
                    if year_range:
                        nr_init = year_range.number_first
                        nr_last = year_range.number_last
                else:
                    no_digit = format_values["seq_length"]
                    nr_last = 10 ^ no_digit - 1
                dict_serie = {
                    "tip": tip,
                    "serieI": seria,
                    "nrI": str(nr_init),
                    "nrF": str(nr_last),
                }
                seq_dict.append(dict_serie)

                # Add period numbers
                if journal_invoices:
                    if journal.l10n_ro_sequence_type == "normal":
                        tip = 2
                    elif journal.l10n_ro_sequence_type == "autoinv1":
                        tip = 3
                    else:
                        tip = 4
                    type_reset = journal_invoices._deduce_sequence_number_reset(
                        first_name
                    )
                    dict_series1 = {"tip": tip, "serieI": seria}
                    if partner and tip in (3, 4):
                        dict_series1["den"] = partner.name
                        dict_series1["cui"] = partner._split_vat(partner.vat)[1]
                    if type_reset == "month":
                        dict_series1.update({"nrI": 1, "nrF": format_values["seq"]})
                    else:
                        nr_init = format_values["seq"] - len(journal_invoices) + 1
                        if nr_init == 0:
                            nr_init = 1
                        dict_series1.update(
                            {
                                "nrI": str(nr_init),
                                "nrF": format_values["seq"],
                            }
                        )
                    seq_dict.append(dict_series1)
        return seq_dict

    def _generate_informatii(self, invoices, payments, op1, op2):
        informatii = {}
        informatii["nrCui1"] = len(
            {
                op["cuiP"]
                for op in op1
                if op["tip_partener"] == "1" and not op.get("simple_invoice")
            }
        )
        informatii["nrCui2"] = len([op for op in op1 if op["tip_partener"] == "2"])
        informatii["nrCui3"] = len(
            {op["cuiP"] for op in op1 if op["tip_partener"] == "3"}
        )
        informatii["nrCui4"] = len(
            {op["cuiP"] for op in op1 if op["tip_partener"] == "4"}
        )
        informatii["nr_BF_i1"] = sum(op["nrBF"] for op in op2 if op["tip_op2"] == "I1")
        informatii["incasari_i1"] = sum(
            op["total"] for op in op2 if op["tip_op2"] == "I1"
        )
        informatii["incasari_i2"] = sum(
            op["total"] for op in op2 if op["tip_op2"] == "I2"
        )
        informatii["nrFacturi_terti"] = len(
            set(
                invoices.filtered(
                    lambda r: r.journal_id.l10n_ro_sequence_type == "autoinv2"
                )
            )
        )

        informatii["nrFacturi_benef"] = len(
            set(
                invoices.filtered(
                    lambda r: r.journal_id.l10n_ro_sequence_type == "autoinv1"
                )
            )
        )
        informatii["nrFacturi"] = len(
            set(
                invoices.filtered(
                    lambda r: r.move_type in ("out_invoice", "out_refund")
                )
            )
        )
        informatii["nrFacturiL_PF"] = 0
        informatii["nrFacturiLS_PF"] = 0
        informatii["val_LS_PF"] = 0
        informatii["tvaDedAI24"] = int(
            round(
                sum(
                    op["tva_24"]
                    for op in payments
                    if op["type"] in ("in_invoice", "in_refund")
                    and op["vat_on_payment"] is True
                )
            )
        )
        informatii["tvaDedAI20"] = int(
            round(
                sum(
                    op["tva_20"]
                    for op in payments
                    if op["type"] in ("in_invoice", "in_refund")
                    and op["vat_on_payment"] is True
                )
            )
        )
        informatii["tvaDedAI19"] = int(
            round(
                sum(
                    op["tva_19"]
                    for op in payments
                    if op["type"] in ("in_invoice", "in_refund")
                    and op["vat_on_payment"] is True
                )
            )
        )
        informatii["tvaDedAI9"] = int(
            round(
                sum(
                    op["tva_9"]
                    for op in payments
                    if op["type"] in ("in_invoice", "in_refund")
                    and op["vat_on_payment"] is True
                )
            )
        )
        informatii["tvaDedAI5"] = int(
            round(
                sum(
                    op["tva_5"]
                    for op in payments
                    if op["type"] in ("in_invoice", "in_refund")
                    and op["vat_on_payment"] is True
                )
            )
        )

        comm_partner = self.company_id.partner_id.commercial_partner_id
        ctx = dict(self._context)
        ctx.update({"check_date": self.date_to})

        if comm_partner.with_context(ctx)._check_vat_on_payment():
            informatii["tvaDed24"] = int(
                round(
                    sum(
                        op["tva_24"]
                        for op in payments
                        if op["type"] in ("in_invoice", "in_refund")
                        and op["vat_on_payment"] is False
                    )
                )
            )
            informatii["tvaDed20"] = int(
                round(
                    sum(
                        op["tva_20"]
                        for op in payments
                        if op["type"] in ("in_invoice", "in_refund")
                        and op["vat_on_payment"] is False
                    )
                )
            )
            informatii["tvaDed19"] = int(
                round(
                    sum(
                        op["tva_19"]
                        for op in payments
                        if op["type"] in ("in_invoice", "in_refund")
                        and op["vat_on_payment"] is False
                    )
                )
            )
            informatii["tvaDed9"] = int(
                round(
                    sum(
                        op["tva_9"]
                        for op in payments
                        if op["type"] in ("in_invoice", "in_refund")
                        and op["vat_on_payment"] is False
                    )
                )
            )
            informatii["tvaDed5"] = int(
                round(
                    sum(
                        op["tva_5"]
                        for op in payments
                        if op["type"] in ("in_invoice", "in_refund")
                        and op["vat_on_payment"] is False
                    )
                )
            )
            informatii["tvaCol24"] = int(
                round(
                    sum(
                        op["tva_24"]
                        for op in payments
                        if op["type"] in ("out_invoice", "out_refund")
                        and op["vat_on_payment"] is True
                    )
                )
            )
            informatii["tvaCol20"] = int(
                round(
                    sum(
                        op["tva_20"]
                        for op in payments
                        if op["type"] in ("out_invoice", "out_refund")
                        and op["vat_on_payment"] is True
                    )
                )
            )
            informatii["tvaCol19"] = int(
                round(
                    sum(
                        op["tva_19"]
                        for op in payments
                        if op["type"] in ("out_invoice", "out_refund")
                        and op["vat_on_payment"] is True
                    )
                )
            )
            informatii["tvaCol9"] = int(
                round(
                    sum(
                        op["tva_9"]
                        for op in payments
                        if op["type"] in ("out_invoice", "out_refund")
                        and op["vat_on_payment"] is True
                    )
                )
            )
            informatii["tvaCol5"] = int(
                round(
                    sum(
                        op["tva_5"]
                        for op in payments
                        if op["type"] in ("out_invoice", "out_refund")
                        and op["vat_on_payment"] is True
                    )
                )
            )
        informatii["incasari_ag"] = 0
        informatii["costuri_ag"] = 0
        informatii["marja_ag"] = 0
        informatii["tva_ag"] = 0
        informatii["pret_vanzare"] = 0
        informatii["pret_cumparare"] = 0
        informatii["marja_antic"] = 0
        informatii["tva_antic"] = 0
        informatii["solicit"] = int(self.solicit)
        if self.solicit:
            informatii["achizitiiPE"] = int(self.achizitiiPE)
            informatii["achizitiiCR"] = int(self.achizitiiCR)
            informatii["achizitiiCB"] = int(self.achizitiiCB)
            informatii["achizitiiCI"] = int(self.achizitiiCI)
            informatii["achizitiiA"] = int(self.achizitiiA)
            informatii["achizitiiB24"] = int(self.achizitiiB24)
            informatii["achizitiiB20"] = int(self.achizitiiB20)
            informatii["achizitiiB19"] = int(self.achizitiiB19)
            informatii["achizitiiB9"] = int(self.achizitiiB9)
            informatii["achizitiiB5"] = int(self.achizitiiB5)
            informatii["achizitiiS24"] = int(self.achizitiiS24)
            informatii["achizitiiS20"] = int(self.achizitiiS20)
            informatii["achizitiiS19"] = int(self.achizitiiS19)
            informatii["achizitiiS9"] = int(self.achizitiiS9)
            informatii["achizitiiS5"] = int(self.achizitiiS5)
            informatii["importB"] = int(self.importB)
            informatii["acINecorp"] = int(self.acINecorp)
            informatii["livrariBI"] = int(self.livrariBI)
            informatii["BUN24"] = int(self.BUN24)
            informatii["BUN20"] = int(self.BUN20)
            informatii["BUN19"] = int(self.BUN19)
            informatii["BUN9"] = int(self.BUN9)
            informatii["BUN5"] = int(self.BUN5)
            informatii["valoareScutit"] = int(self.valoareScutit)
            informatii["BunTI"] = int(self.BunTI)
            informatii["Prest24"] = int(self.Prest24)
            informatii["Prest20"] = int(self.Prest20)
            informatii["Prest19"] = int(self.Prest19)
            informatii["Prest9"] = int(self.Prest9)
            informatii["Prest5"] = int(self.Prest5)
            informatii["PrestScutit"] = int(self.PrestScutit)
            informatii["LIntra"] = int(self.LIntra)
            informatii["PrestIntra"] = int(self.PrestIntra)
            informatii["Export"] = int(self.Export)
            informatii["livINecorp"] = int(self.livINecorp)
            informatii["efectuat"] = int(self.solicit)
        return informatii

