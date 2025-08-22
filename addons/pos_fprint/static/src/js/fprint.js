/**@odoo-module **/
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
const { DateTime } = luxon;
import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { Deferred } from "@web/core/utils/concurrency";
import { rpc } from "@web/core/network/rpc";
import { WarningDialog } from "@web/core/errors/error_dialogs";
import { TextInputPopup } from "@point_of_sale/app/utils/input_popups/text_input_popup";


patch(PosStore.prototype, {

    init(options){
        this.accessType = options.accessType;
        this.networkUrl = options.networkUrl;
        this.localhostUrl = options.localhostUrl;
        this.jobs = {};
        this.env = options.env;
        this.pos = options.env.pos;

    },

    setOrderBon(taskName, date, obj, ProcSource){
        console.log("setOrderBon",obj, ProcSource)
        if (obj && ProcSource.checker_done == false){
            if(date.state == 'close'){
                    obj.fp_number = date.nr
                    obj.fp_result_date = new Date().toISOString().slice(0, 10);
                    obj.fp_state = 'printed'
                    obj.fp_task_id = taskName
                    console.log("setorderbon", ProcSource, obj)
                    ProcSource.checker_done = true;
            } else {
                obj.fp_task_id = "manually operated";
                obj.fp_result_date = new Date().toISOString().slice(0, 10);
                obj.fp_state = 'to_print'
                ProcSource.jobs_checker = 60
                ProcSource.checker_done = true;
                const dialogService = ProcSource.env.services.dialog;
                dialogService.add(WarningDialog, {
                    title: _t("Unexpected error"),
                    message: _t("The applications seems not to be running, please operate the cash register manually."),
                });
            }
        }
    },

    checkStatusBon(taskName, settings, obj, func, self){
        console.log(taskName, settings, obj, func, self)
        var url = this.env.services.pos.config.fp_access=='local'?this.env.services.pos.config.fp_localhost_server_url:this.env.services.pos.config.fp_network_server_url;
        return self.customJsonRpc(url + '/getbon/' + taskName, 'call', {}, Object.assign({}, settings, {
            type: 'GET',
            dataType: 'json',
            crossDomain: true,
            contentType: 'application/json',
        })).then(function(date){
            if(date.state=='open'){
                if(self.jobs_checker > 15){
                    const dialogService = self.env.services.dialog;
                    dialogService.add(WarningDialog, {
                        title: _t("Unexpected error"),
                        message: _t("The applications seems not to be running, please operate the cash register manually."),
                    });
                    obj.fp_task_id = "manually operated";
                    obj.fp_result_date = new Date().toISOString().slice(0, 10);
                    obj.fp_state = 'to_print'
                    self.jobs_checker = 70
                }
            } else {
                func(taskName, date, obj, self)
                self.checker_done = true;
            }
        })
    },

    parseBon(bon){
        return bon
    },

    genericJsonRpc(fct_name, params, settings, fct) {
        const shadow = settings.shadow || false;
        delete settings.shadow;

        if (!shadow) {
            console.log('rpc_request triggered');
        }

        const deferred = new Deferred();

        const data = {
            jsonrpc: "2.0",
            method: fct_name,
            params: params,
            id: Math.floor(Math.random() * 1000 * 1000 * 1000)
        };

        const xhr = fct(data);
        console.log("xhr", xhr)
        const result = xhr
            .then((result) => {
                console.log('rpc:result', data, result);
                return result;
            })
            .catch((...args) => {
                const def = new Deferred();
                // def.reject("communication", ...args);
                return def.promise;
            });

        deferred.abort = function () {
            deferred.reject({ message: "XmlHttpRequestError abort" }, new CustomEvent('abort'));
            if (xhr.abort) {
                xhr.abort();
            }
        };

        result.then(
            (result) => {
                if (!shadow) {
                    console.log('rpc_response triggered');
                }
                deferred.resolve(result);
            },
            (type, error, textStatus, errorThrown) => {
                if (type === "server") {
                    if (!shadow) {
                        console.log('rpc_response triggered');
                    }
                    if (error.code === 100) {
                        console.log('Session invalidated');
                    }
                    deferred.reject(error, new CustomEvent());
                } else {
                    if (!shadow) {
                        console.log('rpc_response_failed triggered');
                    }
                    const nerror = {
                        code: -32098,
                        message: "XmlHttpRequestError " + errorThrown,
                        data: {
                            type: "xhr" + textStatus,
                            debug: error.responseText,
                            objects: [error, errorThrown]
                        }
                    };
                    deferred.reject(nerror, new CustomEvent());
                }
            }
        );

        return deferred;
    },

    customJsonRpc(url, fct_name, params, settings) {
        settings = settings || {};
        let localDate = new Date();
        let utcDate = new Date(localDate.getTime() + localDate.getTimezoneOffset() * 60000);
        return this.genericJsonRpc(fct_name, params, settings, function(data) {
            return fetch(url, {
                method: settings.type || 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                ...(settings.type !== 'GET' && settings.type !== 'HEAD' ? { body: JSON.stringify(data.params, utcDate) } : {}),
            })
                .then(response => {
                    if (!response.ok) {
                        throw new Error(response);
                    }
                    return response.json();
                })
                .then(data => {
                    console.log(data);
                    return data;
                })
                .catch(error => {
                    console.log("--", error, settings)
                    settings.shadow = true;
                    const dialogService = self.env.services.dialog;
                    dialogService.add(WarningDialog, {
                        title: _t("Unexpected error"),
                        message: _t("The application seems not to be running. Restart the application or contact the provider."),
                    });
                    console.error('Fetch Error :-S', error);
                    return error;
                });
        });
    },

    exec_bon(url, bon, params){
        var base_url = this.env.services.pos.config.fp_access=='local'?this.env.services.pos.config.fp_localhost_server_url:this.env.services.pos.config.fp_network_server_url;;
        return this.customJsonRpc(base_url + '/' + url, 'call', bon, Object.assign({}, params, {
            type: 'POST',
            dataType: 'json',
            crossDomain: true,
            contentType: 'application/json'
        }));
    },

    async write_reports(report_type, procSource, async_type){
        var self = this
        return new Promise(function (resolve, reject) {
            self.exec_bon(
                'raport',
                procSource.parseReport(report_type), // {'user':' nume_user', 'password':'nume_password', 'bon':{'tip':'in', 'amount': abs(valoare)}}
                {async:async_type}
            ).then(function(date){
                if (date === undefined){
                    const dialogService = self.env.services.dialog;
                    dialogService.add(WarningDialog, {
                        title: _t("Unexpected error"),
                        message: _t("The application seems not to be running. Restart the application or contact the provider."),
                    });
                    resolve()
                } else if (date.error == true) {
                        const dialogService = self.env.services.dialog;
                        dialogService.add(WarningDialog, {
                            title: _t("Invalid licence"),
                            message: date.message,
                        });
                        resolve();
                    }
                    else{
                        resolve();
                    }
            })
        });
    },

    async write_bon(order, procSource, async_type){
        if(this.env.services.pos) {
            this.jobs_checker = 0
            this.checker_done = false
            this.checker_error = false
            var self = this
            console.log("write_bon", self)
            return new Promise(function (resolve, reject) {
                self.exec_bon(
                    'printbon',
                    procSource.parseBon(order),
                    {async: false}
                ).then(function (date) {
                    if (date === undefined){
                        const dialogService = self.env.services.dialog;
                        dialogService.add(WarningDialog, {
                            title: _t("Unexpected error"),
                            message: _t("The applications seems not to be running, please operate the cash register manually."),
                        });
                        order.fp_task_id = "manually operated";
                        order.fp_result_date = new Date().toISOString().slice(0, 10);
                        order.fp_state = 'to_print'
                        return resolve(false);
                    } else if (date.error == true) {
                            const dialogService = self.env.services.dialog;
                            dialogService.add(WarningDialog, {
                                title: _t("Invalid licence"),
                                message: date.message,
                            });
                            resolve();
                        } else{
                            order.fp_task_id = date.taskid;
                            order.fp_result_date = new Date().toISOString().slice(0, 10);
                            console.log("write bon", date, self.checker_done, self.jobs_checker)
                            order.fp_state = 'to_print';
                            const interval = setInterval(() => {
                                if (self.checker_done || self.jobs_checker >= 15) {
                                    clearInterval(interval);
                                    return resolve(!!order.fp_number);
                                }
                                console.log("check interval:", self.checker_done, self.jobs_checker, order);
                                if (date.taskid && self.checker_done == false) {
                                    self.checkStatusBon(date.taskid, {
                                        type: 'GET',
                                        dataType: 'json',
                                        crossDomain: true,
                                        async: async_type,
                                        contentType: 'application/json',
                                    }, order, self.setOrderBon, self);
                                    self.jobs_checker += 1;
                                }
                            }, 1000);
                            console.log(self)
                            if (date.taskid === undefined){
                                const dialogService = self.env.services.dialog;
                                dialogService.add(WarningDialog, {
                                    title: _t("Unexpected error"),
                                    message: _t("The applications seems not to be running, please operate the cash register manually."),
                                });
                                order.fp_task_id = "manually operated";
                                order.fp_result_date = new Date().toISOString().slice(0, 10);
                                order.fp_state = 'to_print'
                                return resolve();
                            }
                        }
                })
            });
        }
    },
    _prepare_try_cash_in_out_payload(type, amount, reason, extras) {
        console.log(this)
        return [[this.session.id], type, amount, reason, extras];
    },

    async cash_in_out(bon_in_out, procSource, async_type, record){
        /**
         * bon_in_out
         * {'user': str, 'password':str, 'bon': {'tip': 'in', 'amount':abs(value)}}
         **/
        console.log("cash in out order", bon_in_out)
        var self = this
        var bon = {}
        if (procSource.parseBonOutIn){
            bon = procSource.parseBonOutIn(bon_in_out);
        }
        else { bon = bon_in_out}

        const translatedType = _t(bon.bon.type);
        const formattedAmount = this.env.utils.formatCurrency(bon.bon.amount);
        const extras = { formattedAmount, translatedType };

        if (record){
            await this.data.call(
                "pos.session",
                "try_cash_in_out",
                this._prepare_try_cash_in_out_payload(bon.bon.type, bon.bon.amount, bon.bon.reason, extras),
                {},
                true
            );
            await this.logEmployeeMessage(
                `${_t("Cash")} ${translatedType} - ${_t("Amount")}: ${formattedAmount}`,
                "CASH_DRAWER_ACTION"
            );
            await this.notification.add(
                _t("Successfully made a cash %s of %s.", translatedType, formattedAmount),
                3000
            );
        }
        return new Promise(function (resolve, reject) {
            self.exec_bon(
                'cashinout',
                bon,
                {async:async_type}
            ).then(function(date){
                if (date === undefined){
                    const dialogService = self.env.services.dialog;
                    dialogService.add(WarningDialog, {
                        title: _t("Unexpected error"),
                        message: _t("The application seems not to be running. Please make the manual operation on the cash register."),
                    });
                    resolve()
                } else if (date.error == true) {
                        const dialogService = self.env.services.dialog;
                        dialogService.add(WarningDialog, {
                            title: _t("Invalid licence"),
                            message: date.message || _t("Please check the app configuration."),
                        });
                        resolve();
                    } else{
                        resolve();
                    }
            })
        });
    },
    async cash_in_out_retur(bon_in_out, procSource, async_type, record){
        console.log("cash in out order", bon_in_out)
        var self = this
        var bon = {}
        if (procSource.parseBonOutIn){
            bon = procSource.parseBonOutIn(bon_in_out);
        }
        else { bon = bon_in_out}
        console.log("bon de out", bon)

        return new Promise(function (resolve, reject) {
            self.exec_bon(
                'cashinout',
                bon,
                {async:async_type}
            ).then(function(date){
                if (date === undefined){
                    const dialogService = self.env.services.dialog;
                    dialogService.add(WarningDialog, {
                        title: _t("Unexpected error"),
                        message: _t("The application seems not to be running. Please make the manual operationon the cash register."),
                    });
                    resolve()
                } else if (date.error == true) {
                    const dialogService = self.env.services.dialog;
                    dialogService.add(WarningDialog, {
                        title: _t("Invalid licence"),
                        message: date.message || _t("Please check the app configuration."),
                    });
                    resolve();
                } else{
                    resolve();
                }
            })
        });
    },

});