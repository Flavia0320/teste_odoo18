# -*- coding: utf-8 -*-
{
  'name':'Dakai d394',
  'description': "D394",
  'version':'18.0.0.0',
  'author':'Dakai SOFT',
  'website': 'https://dakai.ro',
  'author': 'Dakai SOFT SRL',
  'maintainers': ["adrian-dks"],
  'license': 'OPL-1',
  'installable': True,
  'data': [
    'security/ir.model.access.csv',
    'views/account_move_view.xml',
    'views/account_journal_view.xml',
    'views/d394_view.xml',
    'views/d394_facturi_view.xml',
    'views/d394_lista_view.xml',
    'views/d394_op1_view.xml',
    'views/d394_op2_view.xml',
    'views/d394_rezumat1_view.xml',
    'views/d394_rezumat2_view.xml',
    'views/d394_serie_facturi_view.xml',
    'views/d394_template.xml',
    'views/product_template.xml'
    ],
  'category': 'Accounting',
  'depends': ['account','l10n_ro_config','dakai_declarations_common','l10n_ro_vat_on_payment', 'product'],
}
