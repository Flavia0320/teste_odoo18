/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen";
import { useService } from "@web/core/utils/hooks";
import { TextInputPopup } from "@point_of_sale/app/utils/input_popups/text_input_popup";

patch(TicketScreen.prototype, {
    setup() {
        super.setup(...arguments);
        this.orm = useService("orm");
        if (this.pos.config.fp_active){
            this.doPrint = this.doFiscalPrint.bind(this);
        }
    },

    async doFiscalPrint() {
        console.log("this", this)
            const order = this.getSelectedOrder()
            console.log(order);
            const procSource = this.pos;
            var self = this;
            this.pos.exec_bon(
                'printbon',
                procSource.parseBonReprint(order, order.fp_task_id),
                { async: false }
            ).then(function (date){
                console.log("reprintare order", date)
                if (date.error == true) {
                        const dialogService = self.env.services.dialog;
                        dialogService.add(WarningDialog, {
                            title: _t("Invalid licence"),
                            message: date.message || _t("Please check the app configuration."),
                        });
                        resolve();
                    } else if (date === undefined){
                        const dialogService = self.env.services.dialog;
                        dialogService.add(WarningDialog, {
                            title: _t("Unexpected error"),
                            message: _t("The applications seems not to be running, please operate the cash register manually and then add the bon number in Odoo."),
                        });
                        order.fp_task_id = "manually operated";
                        order.fp_state = 'to_print'
                        resolve();
                    } else {
                        console.log("date", date)
                    }
            })
    },

    async click() {
        await this.doPrint();
    }

});
