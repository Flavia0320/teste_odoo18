# -*- coding: utf-8 -*-
{
  'name':'Sale Construction site',
  'description': "*Create project construction from sale order",
  'version':'18.0.0.1',
  'website': 'https://dakai.ro',
  'author': 'Dakai SOFT SRL',
  'maintainers': ["adrian-dks"],
  'license': 'OPL-1',
  'installable': True,
  'auto_install': True,
  'data': [
    'security/ir.model.access.csv',
    # 'view/sale.xml',
    "view/product_views.xml",
    "wizard/sale_order_construction.xml",
    ],
  'category': "Construction",
  'depends': ['construction_site', 'sale_project'],
}
