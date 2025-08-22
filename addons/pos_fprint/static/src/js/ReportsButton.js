/**@odoo-module **/

import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { Navbar } from "@point_of_sale/app/navbar/navbar";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useService } from "@web/core/utils/hooks";
import { Component, useState } from "@odoo/owl";


class AddReportsDialog extends Component {
    static template = "pos_fprint.addReports";
    static components = {Dialog};
    setup() {
        super.setup();
        this.pos = usePos();
    }

    reportX() {
        this.pos.write_reports("x", this, false);
    }

    reportZ() {
        this.pos.write_reports("z", this, false);
    }

    cancel() {
        this.props.close();
    }

    parseReport(reportType) {
        return {
            "user": this.pos.config.fp_server_user,
            "secret": this.pos.config.fp_server_secret,
            "bon": {
                "raport": reportType
            }
        };
    }
}

patch(Navbar.prototype, {
    setup() {
        super.setup();
        this.dialog= useService("dialog");
    },
    async onClick() {
        this.dialog.add(AddReportsDialog, {
            title: _t("Reports"),
            body: _t("Select a report type."),
        });
    }
});
