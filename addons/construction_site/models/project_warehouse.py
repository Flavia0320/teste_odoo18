from odoo import fields, models, api, _
from odoo.exceptions import UserError

class Project(models.Model):
    _inherit = "project.project"

    warehouse_id = fields.Many2one("stock.warehouse", _("Stock Warehouse"))
    supply_warehouse_id = fields.Many2one("stock.warehouse", _("Supply Warehouse"))
    consume_loc_id = fields.Many2one("stock.location", string=_("Consume Location"))
    consume_type_id = fields.Many2one("stock.picking.type", string=_("Consume Type"))

    def createLogistic(self):
        if not self.category_id:
            raise UserError(_("Project Category is required!"))
        if not self.category_id.project_sequence_id:
            raise UserError(_("Project Category Sequence is required!"))
        if not self.supply_warehouse_id:
            raise UserError(_("Project Category Supply Warehouse is required!"))
        values = {
            'name':self.name,
            'project_id': self.id,
            'code': self.sudo().category_id.project_sequence_id.next_by_id(),
            'is_construction_site': True,
            'buy_to_resupply': False,
            'resupply_wh_ids': [(6, 0, self.supply_warehouse_id.ids)],
            'partner_id': (self.sale_order_id.partner_shipping_id or self.partner_id).id
            }
        wh = self.env['stock.warehouse'].create(values)
        self.warehouse_id = wh.id
        self.name = "[%s] %s" % (wh.code, self.name)

class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    is_construction_site = fields.Boolean(_("Is Construction Site"))
    project_id = fields.Many2one("project.project", _("Construction Site"))
    code = fields.Char(size=None)

    def unlink(self):
        if any(self.mapped("is_construction_site")) and any(self.mapped('project_id')):
            raise UserError(_("Cannot delete construction warehouse\n Project linked %s") % self.mapped('project_id.name'))
        return super(StockWarehouse, self).unlink()

    @api.model_create_multi
    def create(self, values):
        whs = super(StockWarehouse, self).create(values)
        for wh in whs:
            if wh.is_construction_site:
                wh.create_rules()
        return whs

    #Create Route/Rule
    def _get_consume_route_values(self):
        return {
            'name': "%s: Consume" % self.name,
            'product_categ_selectable': True,
            'product_selectable': False,
            'warehouse_selectable': True,
            'warehouse_ids': [(6, 0, self.ids)],
            'rule_ids':[(0, 0, {
                'name': "%s -> %s" % (self.lot_stock_id.name, self.project_id.consume_loc_id.name),
                'action':'pull',
                'picking_type_id': self.project_id.consume_type_id.id,
                'location_src_id': self.lot_stock_id.id,
                'location_dest_id': self.project_id.consume_loc_id.id,
                'procure_method':'make_to_stock',
                'warehouse_id': self.id,
                'group_propagation_option': 'propagate',
            })]
        }

    def create_rules(self):
        consume_route_values = self._get_consume_route_values()
        self.env['stock.route'].create(consume_route_values)
        if self.project_id:
            transit = self.env['stock.location'].search([('usage','=','transit')], limit=1)
            spl_wh = self.project_id.supply_warehouse_id
            if not transit:
                raise UserError(_("No inter-transit location"))
            self.env['stock.route'].create({
                'name': "%s: Retur la %s" % (self.name, spl_wh.name),
                'product_categ_selectable': True,
                'product_selectable': False,
                'warehouse_selectable': True,
                'warehouse_ids': [(6, 0, self.ids)],
                'rule_ids':[
                    (0, 0, {
                    'name': "%s -> %s" % (self.lot_stock_id.display_name, "Transit"),
                    'action':'pull',
                    'picking_type_id': self.int_type_id.id,
                    'location_src_id': self.lot_stock_id.id,
                    'location_dest_id': spl_wh.lot_stock_id.id,
                    'procure_method':'make_to_stock',
                    'warehouse_id': spl_wh.id,
                    'auto': 'manual',
                    })]
                })
            # self.env['stock.route'].create({
            #     'name': "%s: Retur la %s" % (self.name, spl_wh.name),
            #     'product_categ_selectable': True,
            #     'product_selectable': True,
            #     'warehouse_selectable': True,
            #     'warehouse_ids': [(6, 0, [self.id, spl_wh.id])],
            #     'rule_ids':[
            #         (0, 0, {
            #         'name': "%s -> %s" % (self.lot_stock_id.display_name, "Transit"),
            #         'action':'pull',
            #         'picking_type_id': self.int_type_id.id,
            #         'location_src_id': self.lot_stock_id.id,
            #         'location_dest_id': transit.id,
            #         'procure_method':'make_to_stock',
            #         'warehouse_id': self.id,
            #         'auto': 'manual',
            #         }),
            #         (0, 0, {
            #         'name': "%s -> %s" % ('Transit', spl_wh.lot_stock_id.display_name),
            #         'action':'pull',
            #         'picking_type_id': spl_wh.int_type_id.id,
            #         'location_src_id': transit.id,
            #         'location_dest_id': spl_wh.lot_stock_id.id,
            #         'procure_method':'make_to_stock',
            #         'warehouse_id': spl_wh.id,
            #         'auto': 'manual',
            #         })]
            #     })

