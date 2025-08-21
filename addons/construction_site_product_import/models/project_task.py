from odoo import models, fields, _
import xlrd
import base64
from odoo.exceptions import ValidationError


class ProjectTask(models.Model):
    _inherit = "project.task"

    reference = fields.Char(_("Internal Reference"))
    upload_materials_excel = fields.Binary(string=_("Import Products XLS File"))


    def _agregate(self, line):
        
        product = line[0]
        product_id = self.env['product.product'].search(['|',('name', '=', product),('default_code', '=',  product)], limit=1)
        if not product_id:
            product_id = self.env['product.product'].create({
                'name': product,
                'type': 'product',
                'project_id': False,
                'service_tracking': 'no',
                #'seller_ids': [(0, 0, {
                #    'partner_id': self.env.company.partner_id.id,
                #})]
            })
        task = line[1]
        qty = float(line[2])
        return {
            "product": product_id.id,
            "task": task,
            "qty": qty,
        }
        
    def __parseExcel(self, s):
        temparray = []
        for row in range(s.nrows):
            values = []
            for col in range(s.ncols):
                values.append(s.cell(row,col).value)
            temparray.append(values)
        return temparray[1:]

    def parse_xls_data(self):
        try:
            decoded_data = base64.decodebytes(self.upload_materials_excel)
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

    def import_xls(self):
        if not self.upload_materials_excel:
            raise ValidationError(
                _("Please choose a xml file to import!")
            )
        data = self.parse_xls_data()
        products_data = {}
        for d in data:
            task = d.get('task', False)
            product = d.get('product', False)
            qty = d.get('qty', False)
            if not products_data.get(task):
                products_data[task] = {}
                
            if not task:
                task_id = self
            else:
                domain = ['|', ('name', '=', task), ('reference', '=',  task), ('project_id', '=',  self.project_id.id), ('parent_id', '=',  self.id)]
                task_id = self.env['project.task'].search(domain, limit=1)
            if not task_id:
                task_id = self.env['project.task'].create({
                    'name': task or _('Products Task'),
                    'project_id': self.project_id.id,
                    'parent_id': self.id,
                    'partner_id': self.project_id.partner_id.id,
                    'sale_line_id': self.sale_line_id and self.sale_line_id.id or False
                })
            d.update({'task_id': task_id})
            if not products_data[task].get(product):
                products_data[task][product] = {
                    'planned_date': fields.Date.today(),
                    'qty': 0,
                    'task': task,
                    'task_id': task_id,
                }
            products_data[task][product]['qty'] += qty
        for task, pd in products_data.items():
            for product, product_data in pd.items():
                task_id = product_data.get('task_id')
                task_id.task_product_ids = [(0, 0, {
                    'product_id': product,
                    'planned_qty': product_data['qty'],
                    'planned_date': product_data['planned_date']
                })]
        self.upload_materials_excel = None
        return data

