from odoo import http, models
from odoo.http import request
from lxml import etree

COMMON_REMOVE_FIELDS = [
    'id',
    'name',
    '__last_update',
    'display_name',
    'create_uid',
    'create_date',
    'write_uid',
    'write_date',
    'is_l10n_ro_record',
    'activity_ids',
    'activity_state',
    'activity_user_id',
    'activity_type_id',
    'activity_type_icon',
    'activity_date_deadline',
    'my_activity_date_deadline',
    'activity_summary',
    'activity_exception_decoration',
    'activity_exception_icon',
    'message_is_follower',
    'message_follower_ids',
    'message_partner_ids',
    'message_ids',
    'has_message',
    'message_needaction',
    'message_needaction_counter',
    'message_has_error',
    'message_has_error_counter',
    'message_attachment_count',
    'message_main_attachment_id',
    'website_message_ids',
    'message_has_sms_error',
    'state',
]

class Main(http.Controller):


    @http.route(['/d300_data_to_xml'], csrf=False, auth="public", type="json")
    def d300_data_to_xml(self):
        res = request.get_json_data()
        attr_qname = etree.QName("http://www.w3.org/2001/XMLSchema-instance", "schemaLocation")
        nsmap = {None: "mfp:anaf:dgti:d300:declaratie:v10", "xsi": "http://www.w3.org/2001/XMLSchema-instance"}
        d300 = etree.Element("declaratie300",{attr_qname: "mfp:anaf:dgti:d300:declaratie:v10 D300.xsd"}, nsmap=nsmap)

        d300 = self.dict2xml(d300, self.prepare_d300_dict(res))
        return etree.tostring(d300)

    def prepare_d300_dict(self, res):
        removed_fields = COMMON_REMOVE_FIELDS + [
            'version',
            'company_id',
            'succesor_id',
            'cui_succesor',
            'reprezentant_id',
            'bank_account_id',
            'start_date',
            'end_date',
            'move_line_ids',
            'invoice_ids',
        ]
        replace_keys = {
            'depus_reprezentant': 'depusReprezentant',
            'tip_D300': 'tip_decont'
        }
        replaced_values = {
            'solicit_ramb': {
                '0': 'N',
                '1': 'D'
            },
            'bifa_cons': {
                '0': 'N',
                '1': 'D'
            },
            'bifa_disp': {
                '0': 'N',
                '1': 'D'
            },
            'bifa_mob': {
                '0': 'N',
                '1': 'D'
            },
            'bifa_cereale': {
                '0': 'N',
                '1': 'D'
            }
        }
        required_fields = [
            'bifa_interne',
            'depusReprezentant',
            'temei',
            'pro_rata',
            'bifa_cereale',
            'bifa_mob',
            'bifa_disp',
            'bifa_cons',
            'solicit_ramb'
        ]
        return self.clean_dict(res, removed_fields, replace_keys, replaced_values, required_fields)

    @http.route(['/d390_data_to_xml'], csrf=False, auth="public", type="json")
    def d390_data_to_xml(self):
        res = request.get_json_data()
        attr_qname = etree.QName("http://www.w3.org/2001/XMLSchema-instance", "schemaLocation")
        nsmap = {None: "mfp:anaf:dgti:d390:declaratie:v3", "xsi": "http://www.w3.org/2001/XMLSchema-instance"}
        d390 = etree.Element("declaratie390",{attr_qname: "mfp:anaf:dgti:d390:declaratie:v3 D390.xsd"}, nsmap=nsmap)
        d390 = self.dict2xml(d390, self.prepare_d390_dict(res))
        return etree.tostring(d390)

    def prepare_d390_dict(self, res):
        send_res = {}
        for key, val in res.items():
            if 'rezumat_' in key:
                if not send_res.get('rezumat'):
                    send_res['rezumat'] = {}
                send_res['rezumat'][key.replace('rezumat_', '')] = val
            elif key == 'operatie_ids':
                removed_fields = COMMON_REMOVE_FIELDS + [
                    'd390_id',
                    'partner_id',
                    'invoice_line_ids',
                ]
                replace_keys = {}
                replaced_values = {}
                required_fields = [
                    'codO'
                ]
                send_res[key] = []
                for vval in val:
                    send_res[key] += [self.clean_dict(vval, removed_fields, replace_keys, replaced_values, required_fields)]
            elif key == 'cos_ids':
                removed_fields = COMMON_REMOVE_FIELDS + [
                    'd390_id',
                    'picking_id',
                ]
                replace_keys = {}
                replaced_values = {}
                required_fields = [
                    'cod_m1'
                ]
                send_res[key] = []
                for vval in val:
                    send_res[key] += [self.clean_dict(vval, removed_fields, replace_keys, replaced_values, required_fields)]
            else:
                send_res[key] = val
        if send_res.get('rezumat'):
            send_res['rezumat'] = [send_res.get('rezumat')]
        removed_fields = COMMON_REMOVE_FIELDS + [
            'version',
            'company_id',
            'reprezentant_id',
            'start_date',
            'end_date',
            'picking_ids',
            'invoice_ids',
        ]
        replace_keys = {
            'operatie_ids': 'operatie',
            'cos_ids': 'cos'
        }
        replaced_values = {}
        required_fields = [
            'd_rec'
        ]
        d390_dict = self.clean_dict(send_res, removed_fields, replace_keys, replaced_values, required_fields)
        ordered_d390_dict = {
            'rezumat': [],
            'cos': [],
            'operatie': []
        }
        for k, v in d390_dict.items():
            if not isinstance(v, list):
                ordered_d390_dict[k] = v
        for rezumat in d390_dict['rezumat']:
            ordered_d390_dict['rezumat'] += [{
                'nrOPI': rezumat['nrOPI'],
                'bazaL': rezumat['bazaL'],
                'bazaT': rezumat['bazaT'],
                'bazaA': rezumat['bazaA'],
                'bazaP': rezumat['bazaP'],
                'bazaS': rezumat['bazaS'],
                'bazaR': rezumat['bazaR'],
                'total_baza': rezumat['total_baza'],
                'nr_pag': rezumat['nr_pag']
            }]
        for cos in d390_dict['cos']:
            cos_dict = {
                'tara_m1': cos['tara_m1'],
                'cod_m1': cos['cod_m1'],
                'tip': cos['tip']
            }
            if cos.get('tara_m2'):
                cos_dict['motiv'] = cos['motiv']
                cos_dict['tara_m2'] = cos['tara_m2']
                cos_dict['cod_m2'] = cos['cod_m2']
            ordered_d390_dict['cos'] += [cos_dict]
        for op in d390_dict['operatie']:
            ordered_d390_dict['operatie'] += [{
                'tip': op['tip'],
                'tara': op['tara'],
                'codO': op['codO'],
                'denO': op['denO'],
                'baza': op['baza']
            }]
        return ordered_d390_dict

    @http.route(['/d394_data_to_xml'], csrf=False, auth="public", type="json")
    def d394_data_to_xml(self):
        res = request.get_json_data()
        attr_qname = etree.QName("http://www.w3.org/2001/XMLSchema-instance", "schemaLocation")
        nsmap = {None: "mfp:anaf:dgti:d394:declaratie:v4", "xsi": "http://www.w3.org/2001/XMLSchema-instance"}
        d394 = etree.Element("declaratie394",{attr_qname: "mfp:anaf:dgti:d394:declaratie:v4 D394.xsd"}, nsmap=nsmap)
        d394 = self.dict2xml(d394, self.prepare_d394_dict(res))
        return etree.tostring(d394)

    def prepare_d394_dict(self, res):
        send_res = {}
        send_res['informatii'] = {
            'nrCui1': res['i_nrCui1'],
            'nrCui2': res['i_nrCui2'],
            'nrCui3': res['i_nrCui3'],
            'nrCui4': res['i_nrCui4'],
            'nr_BF_i1': res['i_nr_BF_i1'],
            'incasari_i1': res['i_incasari_i1'],
            'incasari_i2': res['i_incasari_i2'],
            'nrFacturi_terti': res['i_nrFacturi_terti'],
            'nrFacturi_benef': res['i_nrFacturi_benef'],
            'nrFacturi': res['i_nrFacturi'],
            'nrFacturiL_PF': res['i_nrFacturiL_PF'],
            'nrFacturiLS_PF': res['i_nrFacturiLS_PF'],
            'val_LS_PF': res['i_val_LS_PF'],
            'tvaDed24': res['i_tvaDed24'],
            'tvaDed20': res['i_tvaDed20'],
            'tvaDed19': res['i_tvaDed19'],
            'tvaDed9': res['i_tvaDed9'],
            'tvaDed5': res['i_tvaDed5'],
            'tvaDedAI24': res['i_tvaDedAI24'],
            'tvaDedAI20': res['i_tvaDedAI20'],
            'tvaDedAI19': res['i_tvaDedAI19'],
            'tvaDedAI9': res['i_tvaDedAI9'],
            'tvaDedAI5': res['i_tvaDedAI5'],
            'tvaCol24': res['i_tvaCol24'],
            'tvaCol20': res['i_tvaCol20'],
            'tvaCol19': res['i_tvaCol19'],
            'tvaCol9': res['i_tvaCol9'],
            'tvaCol5': res['i_tvaCol5'],
            'solicit': res['i_solicit'],
            'achizitiiPE': res['i_achizitiiPE'],
            'achizitiiCR': res['i_achizitiiCR'],
            'achizitiiCB': res['i_achizitiiCB'],
            'achizitiiCI': res['i_achizitiiCI'],
            'achizitiiA': res['i_achizitiiA'],
            'achizitiiB24': res['i_achizitiiB24'],
            'achizitiiB20': res['i_achizitiiB20'],
            'achizitiiB19': res['i_achizitiiB19'],
            'achizitiiB9': res['i_achizitiiB9'],
            'achizitiiB5': res['i_achizitiiB5'],
            'achizitiiS24': res['i_achizitiiS24'],
            'achizitiiS20': res['i_achizitiiS20'],
            'achizitiiS19': res['i_achizitiiS19'],
            'achizitiiS9': res['i_achizitiiS9'],
            'achizitiiS5': res['i_achizitiiS5'],
            'importB': res['i_importB'],
            'acINecorp': res['i_acINecorp'],
            'livrariBI': res['i_livrariBI'],
            'BUN24': res['i_BUN24'],
            'BUN20': res['i_BUN20'],
            'BUN19': res['i_BUN19'],
            'BUN9': res['i_BUN9'],
            'BUN5': res['i_BUN5'],
            'valoareScutit': res['i_valoareScutit'],
            'BunTI': res['i_BunTI'],
            'Prest24': res['i_Prest24'],
            'Prest20': res['i_Prest20'],
            'Prest19': res['i_Prest19'],
            'Prest9': res['i_Prest9'],
            'Prest5': res['i_Prest5'],
            'PrestScutit': res['i_PrestScutit'],
            'LIntra': res['i_LIntra'],
            'PrestIntra': res['i_PrestIntra'],
            'Export': res['i_Export'],
            'livINecorp': res['i_livINecorp']
        }
        for key, val in send_res['informatii'].items():
            del res['i_%s' % key]
        send_res['informatii'] |= {
            'incasari_ag': 0,
            'costuri_ag': 0,
            'marja_ag': 0,
            'tva_ag': 0,
            'pret_vanzare': 0,
            'pret_cumparare': 0,
            'marja_antic': 0,
            'tva_antic': 0,
        }
        for key, val in res.items():
            if 'c1_' in key:
                send_res[key.replace('c1_', '')] = val
            elif key == 'facturi_ids':
                removed_fields = COMMON_REMOVE_FIELDS + [
                    'd394_id',
                    'invoice_id'
                ]
                replace_keys = {}
                replaced_values = {}
                required_fields = [
                    'nr'
                ]
                send_res[key] = []
                for vval in val:
                    send_res[key] += [self.clean_dict(vval, removed_fields, replace_keys, replaced_values, required_fields)]
            elif key == 'lista_ids':
                removed_fields = COMMON_REMOVE_FIELDS + [
                    'd394_id',
                    'invoice_line_ids',
                ]
                replace_keys = {}
                replaced_values = {}
                required_fields = []
                send_res[key] = []
                for vval in val:
                    send_res[key] += [self.clean_dict(vval, removed_fields, replace_keys, replaced_values, required_fields)]
            elif key == 'op1_ids':
                send_res[key] = []
                val_dict = {item.get('denP'): [item.get('taraP'), item.get('judP')] for item in val}
                for vval in val:
                    removed_fields = COMMON_REMOVE_FIELDS + [
                        'd394_id',
                        'partner_id',
                        'invoice_ids',
                        'invoice_line_ids',
                    ]
                    replace_keys = {
                        'l10n_ro_operation_type': 'tip',
                        'l10n_ro_partner_type': 'tip_partener',
                        'l10n_ro_invoice_origin_d394': 'tip_document',
                        'op11_ids':'op11',
                    }
                    replaced_values = {}
                    required_fields = [
                        'cota', 'nrFact', 'baza'
                    ]
                    if vval.get('l10n_ro_partner_type') != '2' or vval.get('cuiP'):
                        removed_fields += ['taraP']
                        removed_fields += ['judP']
                        removed_fields += ['locP']
                        removed_fields += ['strP']
                        removed_fields += ['detP']
                    if vval.get('l10n_ro_partner_type') == '2' and vval.get('l10n_ro_operation_type') == 'N':
                        required_fields += ['l10n_ro_invoice_origin_d394']
                    else:
                        removed_fields += ['l10n_ro_invoice_origin_d394']
                    if vval.get('l10n_ro_operation_type') in ['A', 'L', 'C', 'AI']:
                        required_fields += ['tva']
                    else:
                        removed_fields += ['tva']
                    send_res[key] += [
                        self.clean_dict(vval, removed_fields, replace_keys, replaced_values, required_fields)]
                    for sr in send_res[key]:
                        if sr.get('tip_partener') == '2' and sr.get('cuiP', None) == None:
                            denP = sr.get('denP')
                            if denP in val_dict:
                                sr['taraP'] = val_dict[denP][0]
                                sr['judP'] = val_dict[denP][1]
            elif key == 'op2_ids':
                removed_fields = COMMON_REMOVE_FIELDS + [
                    'd394_id',
                    'invoice_ids',
                ]
                replace_keys = {
                    'tva20': 'TVA20',
                    'tva19': 'TVA19',
                    'tva9': 'TVA9',
                    'tva5': 'TVA5',
                }
                replaced_values = {
                    'tip_op2': {
                        'i1': 'I1',
                        'i2': 'I2',
                    }
                }
                required_fields = [
                    'TVA20',
                    'TVA19',
                    'TVA9',
                    'TVA5',
                    'baza20',
                    'baza19',
                    'baza9',
                    'baza5'
                ]
                send_res[key] = []
                for vval in val:
                    send_res[key] += [self.clean_dict(vval, removed_fields, replace_keys, replaced_values, required_fields)]
            elif key == 'rezumat1_ids':
                send_res[key] = []
                for vval in val:
                    removed_fields = COMMON_REMOVE_FIELDS + [
                        'd394_id',
                        'op1_ids',
                    ]
                    replace_keys = {
                        'l10n_ro_partner_type': 'tip_partener',
                        'l10n_ro_invoice_origin_d394': 'document_N',
                        'rezumat1_detaliu_ids': 'detaliu',
                    }
                    replaced_values = {}
                    required_fields = [
                        'cota'
                    ]
                    if vval.get('cota') != 0:
                        required_fields += ['facturiL']
                        required_fields += ['bazaL']
                        required_fields += ['tvaL']
                        removed_fields += ['facturiLS']
                        removed_fields += ['bazaLS']
                        removed_fields += ['facturiAS']
                        removed_fields += ['bazaAS']
                        removed_fields += ['facturiV']
                        removed_fields += ['bazaV']
                        removed_fields += ['facturiN']
                        removed_fields += ['l10n_ro_invoice_origin_d394']
                        removed_fields += ['bazaN']
                        if vval.get('l10n_ro_partner_type') == '1':
                            required_fields += ['facturiA']
                            required_fields += ['bazaA']
                            required_fields += ['tvaA']
                            required_fields += ['facturiAI']
                            required_fields += ['bazaAI']
                            required_fields += ['tvaAI']
                        else:
                            removed_fields += ['facturiA']
                            removed_fields += ['bazaA']
                            removed_fields += ['tvaA']
                            removed_fields += ['facturiAI']
                            removed_fields += ['bazaAI']
                            removed_fields += ['tvaAI']
                        if vval.get('l10n_ro_partner_type') in ['1', '3', '4']:
                            required_fields += ['facturiC']
                            required_fields += ['bazaC']
                            required_fields += ['tvaC']
                        else:
                            removed_fields += ['facturiC']
                            removed_fields += ['bazaC']
                            removed_fields += ['tvaC']
                    else:
                        removed_fields += ['facturiL']
                        removed_fields += ['bazaL']
                        removed_fields += ['tvaL']
                        removed_fields += ['facturiA']
                        removed_fields += ['bazaA']
                        removed_fields += ['tvaA']
                        removed_fields += ['facturiAI']
                        removed_fields += ['bazaAI']
                        removed_fields += ['tvaAI']
                        removed_fields += ['facturiC']
                        removed_fields += ['bazaC']
                        removed_fields += ['tvaC']
                        if vval.get('l10n_ro_partner_type') == '1':
                            required_fields += ['facturiAS']
                            required_fields += ['bazaAS']
                            required_fields += ['facturiV']
                            required_fields += ['bazaV']
                        else:
                            removed_fields += ['facturiAS']
                            removed_fields += ['bazaAS']
                            removed_fields += ['facturiV']
                            removed_fields += ['bazaV']
                        if vval.get('l10n_ro_partner_type') != '2' or vval.get('l10n_ro_invoice_origin_d394') == '1':
                            required_fields += ['facturiLS']
                            required_fields += ['bazaLS']
                        else:
                            removed_fields += ['facturiLS']
                            removed_fields += ['bazaLS']
                        if vval.get('l10n_ro_partner_type') == '2':
                            required_fields += ['facturiN']
                            required_fields += ['l10n_ro_invoice_origin_d394']
                            required_fields += ['bazaN']
                        else:
                            removed_fields += ['facturiN']
                            removed_fields += ['l10n_ro_invoice_origin_d394']
                            removed_fields += ['bazaN']
                    send_res[key] += [self.clean_dict(vval, removed_fields, replace_keys, replaced_values, required_fields)]
            elif key == 'rezumat2_ids':
                send_res[key] = []
                for vval in val:
                    removed_fields = COMMON_REMOVE_FIELDS + [
                        'd394_id',
                        'op1_ids',
                        'rezumat1_detaliu_ids'
                    ]
                    replace_keys = {}
                    replaced_values = {}
                    required_fields = [
                        'tvaL_PF',
                        'bazaL_PF',
                        'tvaAI',
                        'bazaAI',
                        'nrFacturiAI',
                        'tvaA',
                        'bazaA',
                        'nrFacturiA',
                        'tvaL',
                        'bazaL',
                        'nrFacturiL',
                        'TVABFAI',
                        'bazaBFAI',
                        'TVAFSAI',
                        'bazaFSAI',
                        'TVAFSA',
                        'bazaFSA',
                        'TVAFSL',
                        'bazaFSL',
                        'TVAFSLcod',
                        'bazaFSLcod',
                    ]
                    if res.get('op2_ids'):
                        required_fields += ['baza_incasari_i1']
                    if vval.get('cota') != 24:
                        required_fields += ['baza_incasari_i1']
                        required_fields += ['tva_incasari_i1']
                        required_fields += ['baza_incasari_i2']
                        required_fields += ['tva_incasari_i2']
                    send_res[key] += [self.clean_dict(vval, removed_fields, replace_keys, replaced_values, required_fields)]
            elif key == 'serie_facturi_ids':
                send_res[key] = []
                for vval in val:
                    removed_fields = COMMON_REMOVE_FIELDS + [
                        'd394_id',
                        'journal_id',
                        'invoice_ids'
                    ]
                    replace_keys = {
                        'l10n_ro_sequence_type': 'tip',
                    }
                    replaced_values = {}
                    required_fields = [
                    ]
                    send_res[key] += [self.clean_dict(vval, removed_fields, replace_keys, replaced_values, required_fields)]
            elif not send_res.get(key):
                send_res[key] = val
        if send_res.get('informatii'):
            required_fields = [
                'nrCui1',
                'nrCui2',
                'nrCui3',
                'nrCui4',
                'incasari_i1',
                'incasari_i2',
                'nrFacturi_terti',
                'nrFacturi_benef',
                'tvaDedAI24',
                'tvaDedAI20',
                'tvaDedAI19',
                'tvaDedAI9',
                'tvaDedAI5',
                'solicit',
                'val_LS_PF',
                'nrFacturiLS_PF',
                'nrFacturiL_PF',
                'nrFacturi',
                'nr_BF_i1',
            ]
            send_res['informatii'] = [self.clean_dict(send_res.get('informatii'), required_fields=required_fields)]
        removed_fields = COMMON_REMOVE_FIELDS + [
            'version',
            'company_id',
            'template_id',
            'reprezentant_id',
            'start_date',
            'end_date',
            'invoice_ids',
            'paid_invoice_ids',
            'paid_invoice_ids',
        ]
        replace_keys = {
            'facturi_ids': 'facturi',
            'lista_ids': 'lista',
            'op1_ids': 'op1',
            'op2_ids': 'op2',
            'rezumat1_ids': 'rezumat1',
            'rezumat2_ids': 'rezumat2',
            'serie_facturi_ids': 'serieFacturi',
        }
        replaced_values = {}
        required_fields = [
            'prsAfiliat',
            'sistemTVA',
            'tip_intocmit',
        ]
        d394_dict = self.clean_dict(send_res, removed_fields, replace_keys, replaced_values, required_fields)
        ordered_d394_dict = {}
        for k, v in d394_dict.items():
            if not isinstance(v, list):
                ordered_d394_dict[k] = v
        for informatii in d394_dict['informatii']:
            if not ordered_d394_dict.get('informatii'):
                ordered_d394_dict['informatii'] = []
            ordered_d394_dict['informatii'] += [informatii]
        for rezumat1 in d394_dict['rezumat1']:
            if not ordered_d394_dict.get('rezumat1'):
                ordered_d394_dict['rezumat1'] = []
            ordered_d394_dict['rezumat1'] += [rezumat1]
        for rezumat2 in d394_dict['rezumat2']:
            if not ordered_d394_dict.get('rezumat2'):
                ordered_d394_dict['rezumat2'] = []
            ordered_d394_dict['rezumat2'] += [rezumat2]
        for serieFacturi in d394_dict['serieFacturi']:
            if not ordered_d394_dict.get('serieFacturi'):
                ordered_d394_dict['serieFacturi'] = []
            ordered_d394_dict['serieFacturi'] += [serieFacturi]
        for lista in d394_dict['lista']:
            if not ordered_d394_dict.get('lista'):
                ordered_d394_dict['lista'] = []
            ordered_d394_dict['lista'] += [lista]
        for facturi in d394_dict['facturi']:
            if not ordered_d394_dict.get('facturi'):
                ordered_d394_dict['facturi'] = []
            ordered_d394_dict['facturi'] += [facturi]
        for op1 in d394_dict['op1']:
            if not ordered_d394_dict.get('op1'):
                ordered_d394_dict['op1'] = []
            ordered_d394_dict['op1'] += [op1]
        for op2 in d394_dict['op2']:
            if not ordered_d394_dict.get('op2'):
                ordered_d394_dict['op2'] = []
            ordered_d394_dict['op2'] += [op2]
        return ordered_d394_dict

    def clean_dict(self, res, removed_fields=[], replace_keys={}, replaced_values={}, required_fields=[]):
        new_dict = {}
        for key, val in res.items():
            if key not in removed_fields and (val not in [False, '', '0'] or replace_keys.get(key, key) in required_fields):
                if isinstance(val, int):
                    val = str(val)
                if not isinstance(val, list):
                    new_dict[replace_keys.get(key, key)] = replaced_values.get(key, {val: val})[val]
                else:
                    new_dict[replace_keys.get(key, key)] = val
        return new_dict

    def dict2xml(self, el, dict):
        for k, v in dict.items():
            if isinstance(v, list):
                for vv in v:
                    el2 = etree.SubElement(el, k)
                    self.dict2xml(el2, vv)
            elif isinstance(v, int):
                el.set(k, str(v))
            else:
                el.set(k, v)
        return el
