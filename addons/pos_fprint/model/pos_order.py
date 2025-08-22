from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime
import requests


class FiscalPrinter(models.Model):
    _inherit = "pos.order"

    fp_active = fields.Boolean(_("FP active"), related="config_id.fp_active")
    fp_task_id = fields.Char(_("Task IP"), help=_("Async task ID"))
    fp_print_date = fields.Datetime(_("Print Time"))
    fp_result_date = fields.Datetime(_("Result Time"))
    fp_number = fields.Char(_("FP Recipt Number"))
    fp_state = fields.Selection([('draft', _("Draft")), ('to_print', _("Recipt to print")), ('printed', _("Printed"))],
                                string=_("FP Recipt State"), default='draft')
    cui = fields.Char(_("Cui BON"))

    def action_pos_order_paid(self):
        res = super(FiscalPrinter, self).action_pos_order_paid()
        if self.fp_active:
            self.fp_printFP()
        return res

    @api.model
    def fp_getInfoTask(self):
        for t in self.search([('fp_state', '=', 'to_print')]):
            if not t.config_id.fp_active:
                continue
            try:
                r = requests.get('%s/getbon/%s' % (t.config_id.fp_server_url, t.fp_task_id))
                data = r.json()
                if not data:
                    continue
                if data.get('state', 'open') == 'close' and data.get('nr', '0') != '0':
                    t.write({
                        'fp_number': data['nr'],
                        'fp_result_date': datetime.fromtimestamp(data['last_date']),
                    })
            except Exception as e:
                models._logger.error(_("Error: %s") % e)

    def fp_printFP(self):
        try:
            r = requests.post("%s/printbon" % (self.config_id.fp_server_url,), json=self._fp_PrepareFPRecipt())
            data = r.json()
            self.write({
                'fp_task_id': data['taskid'],
                'fp_print_date': fields.Datetime.now(),
                'fp_state': 'to_print',
            })
        except Exception as e:
            raise UserError(_("Error: %s") % e)

    def _fp_PrepareFPRecipt(self):
        """
        return {
              "uniqueSaleNumber": "DT279013-0001-0000001",
              "operator": "1", #optional
              "operatorPassword": "1", #optional
              "items": [
                {
                  "text": "Cheese",
                  "quantity": 1,
                  "unitPrice": 12,
                  "taxGroup": 2
                },
                {
                  "type": "comment",
                  "text": "Additional comment to the cheese..."
                },
                {
                  "text": "Milk",
                  "quantity": 2,
                  "unitPrice": 10,
                  "taxGroup": 2,
                  "priceModifierValue": 10,
                  "priceModifierType": "discount-percent"
                },
                {
                    "type": "discount-amount",
                    "amount": 10
                },
                {
                  "type": "footer-comment",
                  "text": "YOU ARE WELCOME!"
                }
              ],
              "payments": [
                {
                  "amount": 20,
                  "paymentType": "cash"
                }
              ]
            }
            """
        self.ensure_one()
        items = []
        # tax_ids = self.config_id.fp_tax_group_ids
        for line in self.lines:
            # taxGroup = tax_ids.getTax(line.tax_ids_after_fiscal_position.filtered(lambda x:x.type_tax_use=='sale'))
            # taxQ = line.tax_ids_after_fiscal_position.filtered(lambda x: x.type_tax_use == 'sale')
            # taxQamount = taxQ.mapped("amount")
            item = {
                'text': line.product_id.name,
                'quantity': line.qty,
                'unitPrice': line.price_unit_included,
                'subtotal': line.price_subtotal_incl,
                'uom': line.product_id.uom_id.name,
                'taxGroup': line.tax_group,
                # 'taxPercent': line.tax_qamount,
                'discount': line.discount or None,
            }
            if line.discount != 0:
                item.update({
                    'priceModifierValue': line.discount,
                    'priceModifierType': "discount-percent"
                })
            items.append(item)
        if self.general_note and self.config_id.fp_permit_comment:
            items.append({
                "type": "footer-comment",
                "text": self.general_note
            })
        payments = [{
            'amount': p.amount,
            'paymentType': p.payment_method_id.fp_type,
        } for p in self.payment_ids]
        fpData = {
            'uniqueSaleNumber': self.name,
            'items': items,
            'payments': payments,
            'cui': self.cui or self.partner_id.vat or None,
            'username': self.env.user.name,
            'type': 'bon',
        }
        if self.config_id.fp_userprotect:
            fpData.update({
                'operator': self.config_id.fp_operator,
                'operatorPassword': self.config_id.fp_password
            })
        fpData = {
            'user': self.config_id.fp_server_user,
            'secret': self.config_id.fp_server_secret,
            'bon': fpData
        }
        return fpData

    @api.model
    def _order_fields(self, ui_order):
        ret = super(FiscalPrinter, self)._order_fields(ui_order)
        if ui_order.get('cui', False):
            ret['cui'] = ui_order.get('cui')
        if ui_order.get('fp_task_id', False):
            ret['fp_task_id'] = ui_order.get('fp_task_id')
        if ui_order.get('fp_print_date', False):
            ret['fp_print_date'] = ui_order.get('fp_print_date')
        if ui_order.get('fp_result_date', False):
            ret['fp_result_date'] = ui_order.get('fp_result_date')
        if ui_order.get('fp_number', False):
            ret['fp_number'] = ui_order.get('fp_number')
        if ui_order.get('fp_state', False):
            ret['fp_state'] = ui_order.get('fp_state')
        return ret


#
#     @api.model
#     def updateOrderNr(self, taskId, values):
#         return self.search([('fp_task_id','=', taskId)]).write(values)

class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    price_unit_included = fields.Monetary(compute="_compute_price_unit")
    price_unit_excluded = fields.Monetary(compute="_compute_price_unit")
    tax_group = fields.Char(compute="_compute_tax_group")

    def _compute_tax_group(self):
        models._logger.error(f"self tax {self._fields}")
        for s in self:
            tax_ids = s.order_id.config_id.fp_tax_group_ids
            taxGroup = tax_ids.getTax(s.tax_ids_after_fiscal_position.filtered(lambda x: x.type_tax_use == 'sale'))
            taxQ = s.tax_ids_after_fiscal_position.filtered(lambda x: x.type_tax_use == 'sale')
            taxQamount = taxQ.mapped("amount")
            s.tax_group = taxGroup
            # s.tax_qamount = taxQamount and taxQamount[0] or 0

    @api.onchange('qty', 'discount', 'price_unit', 'tax_ids')
    def _onchange_qty(self):
        if self.product_id:
            price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
            self.price_subtotal = self.price_subtotal_incl = price * self.qty
            if self.tax_ids:
                fpos = self.order_id.fiscal_position_id
                tax_ids_after_fiscal_position = fpos.map_tax(self.tax_ids)
                taxes = tax_ids_after_fiscal_position.compute_all(
                    price, self.order_id.currency_id, self.qty,
                    product=self.product_id, partner=self.order_id.partner_id
                )
                self.price_subtotal = taxes['total_excluded']
                self.price_subtotal_incl = taxes['total_included']

    def _compute_price_unit(self):
        for s in self:
            price_taxes = s.tax_ids_after_fiscal_position.compute_all(s.price_unit)
            s.price_unit_included = price_taxes.get('total_included')
            s.price_unit_excluded = price_taxes.get('total_excluded')


