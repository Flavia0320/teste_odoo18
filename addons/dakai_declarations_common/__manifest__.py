# -*- coding: utf-8 -*-
{
  'name':'Dakai Declaration Common',
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
    'data/res.country.state.csv',
    'views/res_company_view.xml',
    'views/account_move_view.xml',
    'views/res_country_state_view.xml',
    'views/res_config_settings_view.xml',
    'views/declaration_view.xml',
    ],
  'category': 'Accounting',
  'depends': ['account','l10n_ro_config'],
}
