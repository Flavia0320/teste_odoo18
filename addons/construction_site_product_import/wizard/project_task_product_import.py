from odoo import api, fields, models, _
import xlrd
import base64
from odoo.exceptions import ValidationError

class ProjectTaskProductImport(models.TransientModel):
    _name = "project.task.product.import"
    _description = _("Project Task Product Import Wizard")

    attachment_id = fields.Binary(string=_("XLS File"), required=True)
    task_id = fields.Many2one("project.task", _("Parent Task"))

    def _rowDict(self, cols=None):
        if not cols:
            cols = {}
        if not cols.get('product'):
            cols['product'] = 0
        if not cols.get('task'):
            cols['task'] = 1
        if not cols.get('qty'):
            cols['qty'] = 2
        return cols

    def _agregate(self, st, rowx):
        cols = self._rowDict()
        cel_product = st.cell(rowx, cols.get('products',0)).value.split('/')
        if len(cel_product) == 1:
            cel_product += [""]

        product = "/".join(cel_product[:-1])
        product_uom = None
        if cols.get('product_uom'):
            product_uom = st.cell(rowx, cols.get('product_uom')).value
        if not product_uom:
            product_uom = cel_product[-1]

        product_id = self.env['product.product'].search(['|',('name', '=', product),('default_code', '=',  product)], limit=1)
        if not product_id:
            raise ValidationError(
                _("Product '%s' not found in Odoo!" % product)
            )
        task = st.cell(rowx, cols.get('task',1)).value
        qty = st.cell(rowx, cols.get('qty',2)).value
        return {
            "product": product_id.id,
            "task": task,
            "product_uom": product_uom,
            "qty": qty,
        }


    def parse_xls_data(self):
        try:
            decoded_data = base64.decodebytes(self.attachment_id)
            wb = xlrd.open_workbook(file_contents=decoded_data)
            st = wb.sheet_by_index(0)
            rowx = 1
            vals = []
            while rowx < st.nrows:
                vals = self._agregate(st, rowx)
                vals.append(vals)
                rowx += 1
            return vals
        except xlrd.XLRDError:
            raise ValidationError(
                _("Invalid file style, only .xls or .xlsx file allowed")
            )
        except Exception as e:
            raise e

    def execute(self):
        data = self.parse_xls_data()
        products_data = {}
        for index, d in enumerate(data):
            task = d.get('task', False)
            product = d.get('product', False)
            qty = d.get('qty', False)
            if not task:
                task = False
            if not products_data.get(task):
                products_data[task] = {}
            if not products_data[task].get(product):
                products_data[task][product] = 0
            products_data[task][product] += qty
            
            task_id = None
            if not task:
                task_id = self.task_id
            else:
                task_id = self.env['project.task'].search(['|',('name', '=', task),('reference', '=',  task),('parent_id', '=',  self.task_id.id)], limit=1)
            if not task_id:
                task_id = self.env['project.task'].create({
                    'name': task,
                    'project_id': self.task_id.project_id.id,
                    'parent_id': self.task_id.id,
                    'partner_id': self.task_id.partner_id.id,
                    'sale_line_id': self.task_id.sale_line_id.id
                })
            d.update({'task_id': task_id})

            
        for task_id, pd in products_data.items():
            task_id.task_product_ids = [(0, 0, {
                'product_id': product,
                'planned_qty': qty,
            }) for product, qty in pd.items()]
            
            return data
            
            
            
            
