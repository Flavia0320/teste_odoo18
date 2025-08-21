from odoo import api, fields, models, _
from collections import defaultdict
import xlrd
import base64
from odoo.exceptions import ValidationError


class MakeProcurement(models.Model):
    _inherit = "project.site.procurement"

    attachment_id = fields.Binary(string=_("Import XLS File"))
    merge_to_planned = fields.Boolean()

    def __parseExcel(self, s):
        temparray = []
        for row in range(s.nrows):
            values = []
            for col in range(s.ncols):
                values.append(s.cell(row, col).value)
            temparray.append(values)
        return temparray[1:]

    def _agregate(self, line):
        cols = self.env['project.task.product.import']._rowDict()
        if len(line) < 3:
            return {}
        is_product_match = True

        cel_product = line[cols.get('product', 0)]
        product = cel_product

        if not cols.get('product_uom') and '/' in cel_product:
            product = "/".join(cel_product.split('/')[:-1])

        product_uom = line[cols.get('product_uom', 3)]
        if not product_uom:
            product_uom = cel_product[-1]

        product_id = self.env['product.product'].search(['|',('name', '=', product),('default_code', '=',  product)], limit=1)

        if not product_id:
            product_map = self.env['construction.product.mapper'].search([('model', '=', self._name),('name', '=', product)])
            product_id = product_map and product_map.product_id or None

        if not product_id:
            product_id = None
            is_product_match = False

        #De mutat.
        #create product nu are de ce sa fie aici.
        # if not product_id:
        #     product_id = self.env['product.product'].create({
        #         'name': product,
        #         'type': 'product',
        #         'project_id': False,
        #         'service_tracking': 'no',
        #         'seller_ids': [(0, 0, {
        #             'partner_id': self.env.company.partner_id.id,
        #         })]
        #     })
        task = line[cols.get('task', 1)]
        qty = float(line[cols.get('qty', 2)])
        out = {
            "product_id": product_id,
            "product_name": product,
            "product_uom": product_uom,
            "task": task,
            "qty": qty,
            "is_product_match": is_product_match,
        }
        return out

    def parse_xls_data(self):
        try:
            decoded_data = base64.decodebytes(self.attachment_id)
            wb = xlrd.open_workbook(file_contents=decoded_data)
            st = wb.sheet_by_index(0)
            rowx = 1
            vals = []
            for line in self.__parseExcel(st):
                val = self._agregate(line)
                vals.append(val)
                rowx += 1
            return vals
        except xlrd.XLRDError:
            raise ValidationError(
                _("Invalid file style, only .xls or .xlsx file allowed")
            )
        except Exception as e:
            raise e

    def _setItemLineKey(self, d):
        return f"{d.get('task_id').id}-{d.get('product_id') and d.get('product_id').id or d.get('product_name')}"

    def _updateProductItem(self, old, new):
        return {
                'planned_date': fields.Date.today(),
                'qty': old.get('qty', 0) + new.get('qty', 0),
                'task_id': new.get('task_id'),
                'product_id': new.get('product_id'),
                'product_name': new.get('product_name'),
                'product_uom': new.get('product_uom'),
            }

    def _generateProcurementItemValue(self, itemline):
        product_id = itemline.get('product_id')
        product_name = itemline.get('product_name')
        return {
                    'project_id': itemline.get('task_id').project_id.id,
                    'task_id': itemline.get('task_id').id,
                    'product_id': product_id and product_id.id or None,
                    'product_name': product_id and product_id.name or product_name,
                    'product_uom': itemline.get('product_uom'),
                    'to_procure_qty': itemline.get('qty'),
                    'planned_date': itemline.get('planned_date'),
                    'is_product_match': itemline.get('is_product_match'),
                }

    def import_xls(self):
        if not self.attachment_id:
            raise ValidationError(
                _("Please choose a xml file to import!")
            )
        self.task_product_ids.unlink()
        data = self.parse_xls_data()
        products_data = defaultdict(lambda: {})
        for d in data:
            task = d.get('task', False)
            if not task:
                task_id = self.task_id
            else:
                domain = ['|', ('name', '=', task), ('reference', '=',  task), ('project_id', '=',  self.project_id.id), ('parent_id', '=',  self.id)]
                task_id = self.env['project.task'].search(domain, limit=1)
            if not task_id:
                task_id = self.env['project.task'].create({
                    'name': task or _('Products Task'),
                    'project_id': self.project_id.id,
                    'parent_id': self.task_id.id,
                    'partner_id': self.project_id.partner_id.id,
                    'sale_line_id': self.task_id.sale_line_id and self.task_id.sale_line_id.id or False
                })
            d.update({'task_id': task_id})
            key = self._setItemLineKey(d)
            oldPValue = products_data.get(key, {})
            value = self._updateProductItem(oldPValue, d)
            products_data[key].update(value)

        newValueSet = []

        for key, productDict in products_data.items():
            newValueSet.append((0, 0, self._generateProcurementItemValue(productDict)))
        self.task_product_ids = newValueSet
        return data
        # {
        #     'view_mode': 'form',
        #     'view_id': False,
        #     'res_model': self._name,
        #     'context': dict(self._context, active_ids=self.ids),
        #     'type': 'ir.actions.act_window',
        #     'res_id': self.id,
        # }

    def createNonExistingProducts(self):
        for s in self:
            s.task_product_ids.createNonExistingProducts()

class ProcurementLine(models.Model):
    _inherit = "project.site.procurement.product"

    product_id = fields.Many2one('product.product', required=False)
    product_name = fields.Char(string="Product")
    product_uom = fields.Char(string="Unit of Measure")
    is_product_match = fields.Boolean()

    def _SaveForm(self):
        res = super(ProcurementLine, self)._SaveForm()
        for s in self:
            if not s.is_product_match:
                self.env['construction.product.mapper'].create({
                    'name': s.product_name,
                    'product_id': s.product_id.id,
                    'model': s.procurement_id._name,
                    })
        return res

    def createNonExistingProducts(self):
        product = self.env['product.product']
        for s in self.filtered(lambda x: not x.product_id):
            prod_data = product.with_context({'active_id':s.id, 'active_model':s._name}).default_get([
                'name',
                'type',
                ])
            prod_data.update({
                'name': s.product_name,
                'type': 'product',
                'invoice_policy': 'delivery',
                'service_policy': 'delivered_manual',
                'service_tracking': 'no',
                })
            if s.supplier_id:
                prod_data.update({'seller_ids': [(0, 0, self._createSupplierValues(partner_id = s.supplier_id.id))]})
            ctx = self._context.copy()
            models._logger.error(f"marcator {prod_data, ctx, self._context}" )
            if ctx.get('default_project_id'):
                del ctx['default_project_id']
            if ctx.get('default_task_id'):
                del ctx['default_task_id']
            pid = product.with_context(ctx).create(prod_data)
            s.product_id = pid.id

