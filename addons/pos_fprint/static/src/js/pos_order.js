/**@odoo-module **/
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { patch } from "@web/core/utils/patch";
import { bonProcess } from "@pos_fprint/js/fprint";
import { PosStore } from "@point_of_sale/app/store/pos_store";

patch(PosStore.prototype, {
    export_as_JSON() {
        const pos = usePos();
        const order = pos.get_order();

        const json = super.export_as_JSON();
        json.cui = order.cui;
        return json;
    },

    parseBon(order) {
        const pos = this.pos;
        const currentOrder = order;

        const items = [];
        const payments = [];

        currentOrder.lines.forEach(function(v) {
            const price_unit = v.price_unit.toFixed(2);
            const price_subtotal = v.price_subtotal_incl.toFixed(2);
            const tax_id = v.product_id.taxes_id[0];
            const tax_item = v.tax_ids[0];

            items.push({
                "text": v.product_id.display_name,
                "quantity": v.qty,
                "unitPrice": parseFloat(price_unit),
                "subtotalPrice": parseFloat(price_subtotal),
                "uom": v.product_id.uom_id.name,
                "taxGroup": v.tax_ids[0].sequence,
                "taxPercent": tax_item ? tax_item.amount : 0,
                "discount": v.discount || null,
            });
        });
        currentOrder.payment_ids.forEach(function(v) {
            const payment_method = v.payment_method_id;
            console.log("Paymeent", payment_method);
            payments.push({
                "amount": v.amount,
                "paymentType": payment_method.fp_type || null,
            });
        });
        return {
            "user": this.config.fp_server_user,
            "secret": this.config.fp_server_secret,
            "bon": {
                "uniqueSaleNumber": currentOrder.uid,
                "items": items,
                "payments": payments,
                "cui": currentOrder.cui || 0 ,
                "username": this.user.name,
                "type": "bon",
                "operator": 0,
                "operatorPassword": 0
            }
        };
    },

    parseBonReprint(order, taskId) {
        const pos = this.pos;
        const currentOrder = order;

        const items = [];
        const payments = [];

        currentOrder.lines.forEach(function(v) {
            const price_unit = v.price_unit.toFixed(2);
            const price_subtotal = v.price_subtotal_incl.toFixed(2);
            const tax_id = v.product_id.taxes_id[0];
            const tax_item = v.tax_ids[0];

            items.push({
                "text": v.product_id.display_name,
                "quantity": v.qty,
                "unitPrice": parseFloat(price_unit),
                "subtotalPrice": parseFloat(price_subtotal),
                "uom": v.product_id.uom_id.name,
                "taxGroup": v.tax_ids[0].sequence,
                "taxPercent": tax_item ? tax_item.amount : 0,
                "discount": v.discount || null,
            });
        });
        currentOrder.payment_ids.forEach(function(v) {
            const payment_method = v.payment_method_id;
            console.log("Paymeent", payment_method);
            payments.push({
                "amount": v.amount,
                "paymentType": payment_method.fp_type || null,
            });
        });
        return {
            "user": this.config.fp_server_user,
            "secret": this.config.fp_server_secret,
            "taskid": taskId,
            "bon": {
                "uniqueSaleNumber": currentOrder.uid,
                "items": items,
                "payments": payments,
                "cui": currentOrder.cui || 0 ,
                "username": this.user.name,
                "type": "bon",
                "operator": 0,
                "operatorPassword": 0
            }
        };

    },

    parseBonOutIn(order){
        var payment_total = 0;
        order.payment_ids.forEach(function(v) {
            if (v.amount < 0) {
                v.amount = v.amount*(-1);
            }
            payment_total += v.amount;
        });
        return {
                "user": this.config.fp_server_user,
                "secret": this.config.fp_server_secret,
                "bon": {
                    "type": "out",
                    "amount": payment_total,
                    "reason": `Retur ${order.display_name}`,
                    }
                }
    },

    async _save_to_server(orders, options) {
        var self = this
        const pos = usePos();
        console.log("Save to server:", orders);
        if (orders.length && (this.config.fp_access == 'network' || this.config.fp_access == 'local')) {
            await this.orders[0].pos.write_bon(orders, this, false);
        }
        try {
            return super._save_to_server(orders, self, options);
        } catch (error) {
            if (orders.length && self.config.fp_access == 'internet' && error.code != 200) {
                this.orders[0].pos.write_bon(orders, self, true);
            }
        }
    }
});