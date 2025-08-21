# -*- coding: utf-8 -*-
# Copyright 2023 Dakai SoftSRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).
{
'name':'Construction Site Task Product Import',
'description': "Construction Site Task Product Import",
'version': "18.0.1.0.1",
'category': "Construction",
'website': "https://dakai.ro",
'author': "Dakai SOFT SRL",
'maintainers': ["adrian-dks"],
'license': "OPL-1",
'installable': True,
  'data': [
    "security/ir.model.access.csv",
    'views/procurement.xml',
    'wizard/project_task_product_import.xml',
    'views/project_task_view.xml',
    'views/project_project_view.xml',
    ],
  'depends': [
      'construction_site',
      ],
}
