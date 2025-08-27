from odoo import fields, models, api, _

class Project(models.Model):
    _inherit = "project.project"

    consume_loc_id = fields.Many2one("stock.location", string=_("Consume Location"), related="warehouse_id.l10n_ro_wh_consume_loc_id")
    consume_type_id = fields.Many2one("stock.picking.type", string=_("Consume Type"), related="warehouse_id.l10n_ro_consume_type_id")

    def createLogistic(self):
        super(Project, self).createLogistic()
        # migrare v17
        # self.warehouse_id.lot_stock_id.l10n_ro_accounting_location_id = self.category_id.l10n_ro_accounting_location_id.id

class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"
    #TODO : fix eroare picking_type_id
    def _get_consume_route_values(self):
        return {
            'name': "%s: Consume" % self.name,
            'product_categ_selectable': True,
            'product_selectable': True,
            'warehouse_selectable': True,
            'warehouse_ids': [(6, 0, self.ids)],
            'rule_ids':[(0, 0, {
                'name': "%s -> %s" % (self.lot_stock_id.name, self.l10n_ro_wh_consume_loc_id.name),
                'action':'pull',
                'picking_type_id': self.l10n_ro_consume_type_id.id,
                'location_src_id': self.lot_stock_id.id,
                'location_dest_id': self.l10n_ro_wh_consume_loc_id.id,
                'procure_method':'make_to_stock',
                'warehouse_id': self.id,
                'group_propagation_option': 'propagate',
            })]
        }
