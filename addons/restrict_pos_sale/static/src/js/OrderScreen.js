/** @odoo-module */
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from '@web/core/utils/patch';
import RestrictSalePopup from '@restrict_pos_sale/js/RestrictSalePopup';
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";
import { WarningDialog } from "@web/core/errors/error_dialogs";
import { _t } from "@web/core/l10n/translation";


patch(PosStore.prototype, {
    async pay() {
        console.log(this)
        const dialogService = this.env.services.dialog;

        for (const line of this.selectedOrder.lines) {
            const productId = line.product_id.id;
            const pickingTypeId = this.config.picking_type_id.id;

            const [pickingType] = await rpc("/web/dataset/call_kw", {
                model: "stock.picking.type",
                method: "read",
                args: [[pickingTypeId], ["default_location_src_id"]],
                kwargs: {},
            });
            const locationId = pickingType.default_location_src_id[0];

            const quants = await rpc("/web/dataset/call_kw", {
                model: "stock.quant",
                method: "read_group",
                args: [
                    [
                        ["product_id", "=", productId],
                        ["location_id", "=", locationId]
                    ],
                    ["quantity:sum"],
                    ['product_id']
                ],
                kwargs: {},
            });
            const stockQty = quants.length ? quants[0]["quantity"] : 0;

            if (line.get_quantity() > stockQty || line.get_quantity() === 0) {
                await dialogService.add(WarningDialog, {
                    title: _t("Low stock"),
                    message: `Product ${line.product_id.display_name} has quantity 0 or will be negative!`,
                });
                return;
            }
        }
        return super.pay();
    }
});
