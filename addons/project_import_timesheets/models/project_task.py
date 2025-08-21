from odoo import fields, models, _
import xlrd
import base64
from odoo.exceptions import ValidationError
import dateutil.parser

class ProjectProject(models.Model):
    _inherit = "project.task"

    timesheets_attachment_id = fields.Binary(string=_("Import Timesheets"))

    def parse_xls_data(self):
        try:
            decoded_data = base64.decodebytes(self.timesheets_attachment_id)
            wb = xlrd.open_workbook(file_contents=decoded_data)
            st = wb.sheet_by_index(0)
            rowx = 1
            vals = []
            while rowx < st.nrows:
                employee = st.cell(rowx, 1).value
                employee_id = self.env['hr.employee'].search(['|',('name', '=', employee),('barcode', '=',  employee)], limit=1)
                if not employee_id:
                    raise ValidationError(_("Employee '%s' not found!" % employee))
                name = st.cell(rowx, 2).value
                unit_amount = st.cell(rowx, 3).value
                date = st.cell(rowx, 0).value and dateutil.parser.parse(st.cell(rowx, 0).value) or fields.Date.today()
                vals.append({
                    "employee_id": employee_id.id,
                    "name": name,
                    "unit_amount": unit_amount,
                    "date": date,
                    'project_id': self.project_id.id
                })
                rowx += 1
            return vals
        except xlrd.XLRDError:
            raise ValidationError(
                _("Invalid file style, only .xls or .xlsx file allowed")
            )
        except Exception as e:
            raise e

    def import_timesheets_xls(self):
        if not self.timesheets_attachment_id:
            raise ValidationError(
                _("Please choose a xml file to import!")
            )
        data = self.parse_xls_data()
        self.timesheet_ids = [(0, 0,  d) for d in data]