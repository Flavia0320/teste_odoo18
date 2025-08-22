import { OpeningControlPopup } from "@point_of_sale/app/store/opening_control_popup/opening_control_popup";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { parseFloat } from "@web/views/fields/parsers";

patch(OpeningControlPopup.prototype, {
    setup() {
        super.setup();
        this.pos = usePos();
    },

    confirm() {
        const bon = {
            "user": this.pos.config.fp_server_user,
            "secret": this.pos.config.fp_server_secret,
            "bon": {
                "type": 'in',
                "amount": parseFloat(this.state.openingCash),
                "reason": this.state.notes,
                }
            }
        this.pos.cash_in_out(bon, this, true, false)

        super.confirm();
    }
});

