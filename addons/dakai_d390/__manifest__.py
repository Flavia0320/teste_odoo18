# -*- coding: utf-8 -*-
{
  'name':'Dakai D390',
  'description': "",
  'version':'18.0.0.1',
  'author':'Dakai SOFT',
  'website': 'https://dakai.ro',
  'author': 'Dakai SOFT SRL',
  'maintainers': ["adrian-dks"],
  'license': 'OPL-1',
  'installable': True,
  'data': [
     'security/ir.model.access.csv',
     'views/d390_view.xml',
     'views/d390_template.xml',
    ],
  'category': 'Accounting',
  'depends': ['account','stock','l10n_ro_config','dakai_declarations_common','l10n_ro_vat_on_payment'],
}
