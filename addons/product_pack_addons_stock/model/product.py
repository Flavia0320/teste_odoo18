from odoo import fields, models, _, api


class ProductTemplate(models.Model):
    _inherit = "product.template"
    
    pack_type = fields.Selection(selection_add=[
        ('stock_detailed', _('Stock Detailed')),
    ],
        string=_('Pack Type'),
        help=_("On sale orders or purchase orders:\n"
             "* Detailed: Display components individually in the sale order.\n"
             "* Stock Detailed: Display components individually in the Stock Picking.\n"
             "* Non Detailed: Do not display components individually in the"
             " sale order."
             )
    )
    
    
class ProductProduct(models.Model):
    _inherit = "product.product"
    
    def split_pack_products(self):
        """Split products and the pack in 2 separate recordsets.

        :return: [packs, no_packs]
        """
        packs = self.filtered(
            lambda p: p.pack_ok and (
                (p.pack_type in ['detailed','stock_detailed']
                 and p.pack_component_price == 'totalized')
                or p.pack_type == 'non_detailed'))
        # TODO: Check why this is needed
        # for compatibility with website_sale
        if self._context.get('website_id', False) and \
                not self._context.get('from_cart', False):
            packs |= self.filtered(
                lambda p: p.pack_ok and p.pack_type in ['detailed','stock_detailed']
                and p.pack_component_price == 'detailed')

        no_packs = (self | self.sudo().get_pack_lines().mapped('product_id')) - packs
        return packs, no_packs

