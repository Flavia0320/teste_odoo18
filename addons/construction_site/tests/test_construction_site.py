from odoo.addons.project.tests.test_project_base import TestProjectCommon
from odoo.exceptions import UserError
from odoo.tests import tagged


from odoo.addons.project.tests.test_project_base import TestProjectCommon
from odoo.exceptions import UserError
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TaskProductPurchaseTests(TestProjectCommon):
    def test_creating_task_product_purchase_with_valid_data_succeeds(self):
        product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'product',
            'uom_id': self.env.ref('uom.product_uom_unit').id,
            'uom_po_id': self.env.ref('uom.product_uom_unit').id,
        })
        task = self.env['project.task'].create({
            'name': 'Test Task',
            'project_id': self.env['project.project'].create({'name': 'Test Project'}).id,
        })
        task_product = self.env['project.task.product'].create({
            'product_id': product.id,
            'task_id': task.id,
        })
        partner = self.env['res.partner'].create({'name': 'Test Partner'})
        purchase_order = self.env['purchase.order'].create({'partner_id': partner.id})
        purchase_order_line = self.env['purchase.order.line'].create({
            'order_id': purchase_order.id,
            'product_id':product.id,
            'product_uom_qty': 10,
            'price_unit': 100,
        })
        purchase = self.env['project.task.product.purchase'].create({
            'task_product_id': task_product.id,
            'purchase_order_line_id': purchase_order_line.id,
            'planned_qty': 5,
        })
        self.assertEqual(purchase.planned_qty, 5)
        self.assertEqual(purchase.purchase_order_line_id, purchase_order_line)

    def test_writing_state_to_cancel_resets_quantities(self):
        product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'product',
            'uom_id': self.env.ref('uom.product_uom_unit').id,
            'uom_po_id': self.env.ref('uom.product_uom_unit').id,
        })
        task = self.env['project.task'].create({
            'name': 'Test Task',
            'project_id': self.env['project.project'].create({'name': 'Test Project'}).id,
        })
        task_product = self.env['project.task.product'].create({
            'product_id': product.id,
            'task_id': task.id,
        })
        purchase_order = self.env['purchase.order'].create({'partner_id': self.env.ref('base.res_partner_1').id})
        purchase_order_line = self.env['purchase.order.line'].create({
            'order_id': purchase_order.id,
            'product_id': product.id,
            'product_uom_qty': 10,
            'price_unit': 100,
        })
        purchase = self.env['project.task.product.purchase'].create({
            'task_product_id': task_product.id,
            'purchase_order_line_id': purchase_order_line.id,
            'planned_qty': 5,
        })
        purchase.write({'state': 'cancel'})
        self.assertEqual(purchase.planned_qty, 0)
        self.assertEqual(purchase.purchase_qty, 0)
        self.assertEqual(purchase.received_qty, 0)
        self.assertEqual(purchase.billed_qty, 0)

    def writing_state_from_cancel_to_draft_raises_user_error(self):
        product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'product',
            'uom_id': self.env.ref('uom.product_uom_unit').id,
            'uom_po_id': self.env.ref('uom.product_uom_unit').id,
        })
        task = self.env['project.task'].create({
            'name': 'Test Task',
            'project_id': self.env['project.project'].create({'name': 'Test Project'}).id,
        })
        task_product = self.env['project.task.product'].create({
            'product_id': product.id,
            'task_id': task.id,
        })
        purchase_order = self.env['purchase.order'].create({'partner_id': self.env.ref('base.res_partner_1').id})
        purchase_order_line = self.env['purchase.order.line'].create({
            'order_id': purchase_order.id,
            'product_id': product.id,
            'product_uom_qty': 10,
            'price_unit': 100,
        })
        purchase = self.env['project.task.product.purchase'].create({
            'task_product_id': task_product.id,
            'purchase_order_line_id': purchase_order_line.id,
            'planned_qty': 5,
        })
        purchase.write({'state': 'cancel'})
        with self.assertRaises(UserError):
            purchase.write({'state': 'draft'})

    def writing_state_to_purchase_with_purchase_qty_sets_planned_qty(self):
        product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'product',
            'uom_id': self.env.ref('uom.product_uom_unit').id,
            'uom_po_id': self.env.ref('uom.product_uom_unit').id,
        })
        task = self.env['project.task'].create({
            'name': 'Test Task',
            'project_id': self.env['project.project'].create({'name': 'Test Project'}).id,
        })
        task_product = self.env['project.task.product'].create({
            'product_id': product.id,
            'task_id': task.id,
        })
        purchase_order = self.env['purchase.order'].create({'partner_id': self.env.ref('base.res_partner_1').id})
        purchase_order_line = self.env['purchase.order.line'].create({
            'order_id': purchase_order.id,
            'product_id': product.id,
            'product_uom_qty': 10,
            'price_unit': 100,
        })
        purchase = self.env['project.task.product.purchase'].create({
            'task_product_id': task_product.id,
            'purchase_order_line_id': purchase_order_line.id,
            'planned_qty': 5,
        })
        purchase.write({'state': 'purchase', 'purchase_qty': 7})
        self.assertEqual(purchase.planned_qty, 7)