# -*- coding: utf-8 -*-
{
  'name':'Dakai Account Report Journal',
  'description': "",
  'version':'18.0.0.0',
  'author':'Dakai SOFT',
  'website': 'https://dakai.ro',
  'author': 'Dakai SOFT SRL',
  'maintainers': ["adrian-dks"],
  'license': 'OPL-1',
  'installable': True,
  'data': [
     'security/ir.model.access.csv',
     'views/account_report_journal_view.xml',
     'views/account_report_journal_template.xml'
    ],
  'category': 'Accounting',
  'depends': ['account','l10n_ro_config','l10n_ro_vat_on_payment'],
}
