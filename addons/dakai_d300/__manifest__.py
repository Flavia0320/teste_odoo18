# -*- coding: utf-8 -*-
{
  'name':'Dakai D300',
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
     'views/d300_view.xml',
     'views/d300_template.xml',
     'views/product_category_view.xml',
    ],
  'category': 'Accounting',
  'depends': ['account','l10n_ro_config','dakai_declarations_common','l10n_ro_vat_on_payment'],
}
