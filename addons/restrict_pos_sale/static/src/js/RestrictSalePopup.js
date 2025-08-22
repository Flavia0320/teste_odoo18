/** @odoo-module **/

import { Dialog } from "@web/core/dialog/dialog";
import { Component } from "@odoo/owl";

export class RestrictSalePopup extends Component {
    setup() {
        super.setup();
    }

    cancel() {
        this.props.close();
    }
}

RestrictSalePopup.template = "RestrictSalePopup";
RestrictSalePopup.props = ["body", "prod_id", "close"];
