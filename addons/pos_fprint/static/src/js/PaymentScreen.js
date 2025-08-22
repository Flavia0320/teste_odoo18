/**@odoo-module**/
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { TextInputPopup } from "@point_of_sale/app/utils/input_popups/text_input_popup";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";

patch(PaymentScreen.prototype, {
    setup() {
        super.setup();
        this.dialogService = useService("dialog");
    },

    getCif() {
        return this.currentOrder.cui;
    },

    async setCif() {
        const { confirmed, payload: cui } = await this.dialogService.add(TextInputPopup, {
            title: _t("Adaugă CUI"),
            getPayload: (inputValue) => inputValue,
            close: () => {},
        });

        if (confirmed) {
            this.currentOrder.cui = cui;
        }
    },
});
