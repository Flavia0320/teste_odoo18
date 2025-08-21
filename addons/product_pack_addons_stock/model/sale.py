from odoo import api, models #, fields, _
from odoo.tools import float_compare #, float_is_zero
from odoo.exceptions import UserError


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    
    def expand_pack_line(self, write=False):
        self.ensure_one()
        if self.product_id.pack_type != 'stock_detailed':
            return super(SaleOrderLine, self).expand_pack_line(write=write)

    
    def _action_launch_stock_rule(self):
        """
        Launch procurement group run method with required/custom fields genrated by a
        sale order line. procurement group will launch '_run_pull', '_run_buy' or '_run_manufacture'
        depending on the sale order line product rule.
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        errors = []
        for line in self:
            if line.state != 'sale' or not line.product_id.type in ('consu','product'):
                continue
            qty = line._get_qty_procurement(False)
            if float_compare(qty, line.product_uom_qty, precision_digits=precision) >= 0:
                continue
 
            group_id = line.order_id.procurement_group_id
            if not group_id:
                group_id = self.env['procurement.group'].create({
                    'name': line.order_id.name, 'move_type': line.order_id.picking_policy,
                    'sale_id': line.order_id.id,
                    'partner_id': line.order_id.partner_shipping_id.id,
                })
                line.order_id.procurement_group_id = group_id
            else:
                # In case the procurement group is already created and the order was
                # cancelled, we need to update certain values of the group.
                updated_vals = {}
                if group_id.partner_id != line.order_id.partner_shipping_id:
                    updated_vals.update({'partner_id': line.order_id.partner_shipping_id.id})
                if group_id.move_type != line.order_id.picking_policy:
                    updated_vals.update({'move_type': line.order_id.picking_policy})
                if updated_vals:
                    group_id.write(updated_vals)
 
            values = line._prepare_procurement_values(group_id=group_id)
            product_qty = line.product_uom_qty - qty
 
            procurement_uom = line.product_uom
            quant_uom = line.product_id.uom_id
            get_param = self.env['ir.config_parameter'].sudo().get_param
            if procurement_uom.id != quant_uom.id and get_param('stock.propagate_uom') != '1':
                product_qty = line.product_uom._compute_quantity(product_qty, quant_uom, rounding_method='HALF-UP')
                procurement_uom = quant_uom
 
            try:
                if line.product_id.pack_ok:
                    procurements = []
                    for lprod in line.product_id.pack_line_ids:
                        if lprod.product_id.type not in ['consu','product'] or not lprod.product_id:
                            continue
                        procurements.append(self.env['procurement.group'].Procurement(
                            lprod.product_id,
                            product_qty * lprod.quantity,
                            procurement_uom,
                            line.order_id.partner_shipping_id.property_stock_customer,
                            lprod.product_id.name, line.order_id.name, line.order_id.company_id, values))
                    self.env['procurement.group'].run(procurements)
                else:
                    procurements = [self.env['procurement.group'].Procurement(
                        line.product_id,
                        product_qty,
                        procurement_uom,
                        line.order_id.partner_shipping_id.property_stock_customer,
                        line.name, line.order_id.name, line.order_id.company_id, values)]
                    self.env['procurement.group'].run(procurements)
            except UserError as error:
                errors.append(error.name)
        if errors:
            raise UserError('\n'.join(errors))
        return True
