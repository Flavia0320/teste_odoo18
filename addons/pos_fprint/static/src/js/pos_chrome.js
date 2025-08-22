/**@odoo-module **/
import { reactive, Component, onMounted, onWillStart } from "@odoo/owl";
import { printBon } from "@pos_fprint/js/fprint";
import { patch } from "@web/core/utils/patch";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { AccountMoveService } from "@account/services/account_move_service";
import { isIosApp, isIOS } from "@web/core/browser/feature_detection";



patch(PaymentScreen.prototype, {
     async _finalizeValidation() {
        console.log("this before",this);

        await this.hook_before_fiscalization();

        if (this.pos.config.fp_active == true){
            const currentOrder = this.pos.get_order();
            const orders = currentOrder ? [currentOrder] : [];
            const self = this.pos;

            if (orders && orders.length > 0) {
                console.log("Calling write_bon with orders:",currentOrder, this);
                if (!currentOrder._isRefundOrder()){
                    const bonPrinted = await this.pos.write_bon(currentOrder, self, true);
                    if (!bonPrinted) {
                        console.warn("Bonul nu a fost printat, se oprește validarea.");
                        return;
                    }
                 }
            }
        }

        await this.hook_after_fiscalization();

        await super._finalizeValidation();
     },

     async hook_before_fiscalization() {
        // Hook method to be overridden if needed
    },

    async hook_after_fiscalization() {
        // Hook method to be overridden if needed
    },

    async afterOrderValidation() {
        console.log("this before",this);
        const currentOrder = this.pos.get_order();
        const orders = currentOrder ? [currentOrder] : [];
        const self = this.pos;

        if (orders && orders.length > 0) {
            console.log("Calling write_bon with orders:",currentOrder, this);
            if (currentOrder.refunded_order_id){
                if (this.pos.config.fp_active == true){
                    await this.pos.cash_in_out_retur(currentOrder, self, this, true);
                }
                const pickingID = currentOrder.raw.picking_ids;
                const report = this.pos.config.fp_report_view;
                if (pickingID) {
                    await this.invoiceService.downloadPdfDelivery(pickingID, report);
                }
                const domain = [['payment_ref', 'ilike', currentOrder.display_name]];
                const cashBase = await this.pos.env.services.orm.call('account.bank.statement.line', "search", [domain]);
                console.log(cashBase);

                const statementID = cashBase;
                if (statementID) {
                    const report_dispo = this.pos.config.fp_report_dispo;
                    await this.invoiceService.downloadPdfDisp(statementID, report_dispo);
                }
            }
         }
        await super.afterOrderValidation();
     }
});

patch(AccountMoveService.prototype, {
    async downloadPdfDisp(statementID, report) {
        const url = `/report/pdf/${report}/${statementID}`

        const link = document.createElement('a');
        link.href = url;
        link.download = `Dispozitie de plata.pdf`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    },
    async downloadPdfDelivery(pickingID, report) {
        const url = `/report/pdf/${report}/${pickingID}`;

        const link = document.createElement('a');
        link.href = url;
        link.download = `Livrare.pdf`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

});