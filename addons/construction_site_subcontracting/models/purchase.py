# Copyright 2023 Dakai SOFT SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    task_subcontracting_ids = fields.One2many("project.task.subcontracting", "purchase_order_line_id", string=_("Task Subcontracting"))