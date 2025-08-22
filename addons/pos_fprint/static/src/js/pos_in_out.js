/**@odoo-module **/
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { CashMovePopup } from "@point_of_sale/app/navbar/cash_move_popup/cash_move_popup";
import { FloatField, floatField } from '@web/views/fields/float/float_field';
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { parseFloat } from "@web/views/fields/parsers";

patch(CashMovePopup.prototype, {
    setup() {
        super.setup();
        this.pos = usePos();
    },

    async confirm() {
        const self = this
        const info = {
                amount: parseFloat(this.state.amount),
                reason: this.state.reason,
                type: this.state.type,
            };
        const bon = {
            "user": self.pos.config.fp_server_user,
            "secret": self.pos.config.fp_server_secret,
            "bon": {
                "type": info.type,
                "amount": Math.abs(info.amount),
                "reason": info.reason,
                }
            }
        const amount = parseFloat(this.state.amount);
        const type = this.state.type;
        const formattedAmount = this.env.utils.formatCurrency(amount);
        this.pos.cash_in_out(bon, this, true, true)
        this.props.close();
    }

});
