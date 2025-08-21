from odoo import api, fields, models, _


class TaskConsumeProducts(models.TransientModel):
    _name = "project.task.product.consume.wizard"

    task_id = fields.Many2one("project.task")
    product_ids = fields.One2many("project.task.product.consume.wizard.line", "wiz_id")

    def default_get(self, fieldlist):
        res = super(TaskConsumeProducts, self).default_get(fieldlist)
        if res.get('task_id'):
            task = self.env['project.task'].browse(res.get('task_id'))
            #qty =
            res['product_ids'] = [(0, 0, {
                'product_line_id': line.id,
                'max_limit': line.received_qty-line.consumed_qty,
                'quantity':line.received_qty-line.consumed_qty,
                }) for line in task.task_product_ids]
        return res

    def execute(self):
        for line in self.product_ids:
            line.product_line_id.tmp_consume = line.quantity
        self.task_id.consumeProducts()

class TaskConsumeProductsLine(models.TransientModel):
    _name = "project.task.product.consume.wizard.line"

    product_line_id = fields.Many2one("project.task.product")
    product_id = fields.Many2one("product.product", related="product_line_id.product_id")
    uom_id = fields.Many2one("uom.uom", related="product_line_id.uom_id")
    wiz_id = fields.Many2one('project.task.product.consume.wizard')
    max_limit = fields.Float()
    quantity = fields.Float()

    @api.onchange('quantity')
    def onChangequantity(self):
        res = {}
        if self.quantity > self.max_limit:
            res['warning'] = {'title': _("Quantity not allowed"), 'message':_("Desired consume quantity is above max quantity allowed  %s>%s" % (self.quantity, self.max_limit))}
            res['value'] = {'quantity': self.max_limit}
        return res
