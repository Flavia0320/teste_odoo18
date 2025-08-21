# -*- coding: utf-8 -*-
# Copyright 2022 Dakai SoftSRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).
{
'name':'Construction Site Employee',
'description': "Construction Site Employee",
'version': "18.0.1.0.4",
'category': "Construction",
'website': "https://dakai.ro",
'author': "Dakai SOFT SRL",
'maintainers': ["adrian-dks"],
'license': "OPL-1",
'installable': True,
  'data': [
    "security/ir.model.access.csv",
    'reports/project_cost_structure.xml',
    'reports/employee_report.xml',
    'views/project_task_view.xml',
    'wizard/project_task_employee_attendance.xml',
    #'views/project_task_content.xml',
    ],
  'depends': [
      'construction_site',
      'hr',
      ],
}
