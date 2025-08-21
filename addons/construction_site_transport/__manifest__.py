# -*- coding: utf-8 -*-
{
  'name':'Construction site transport',
  'description': "",
  'version':'18.0.0.2',
  'author':'Dakai SOFT',
  'website': 'https://dakai.ro',
  'maintainers': ["adrian-dks"],
  'license': 'OPL-1',
  'installable': True,
  'data': [
    'security/ir.model.access.csv',
    'reports/project_cost_structure.xml',
    'reports/report_transport.xml',
    'views/project_task_view.xml',
    'views/transport.xml',
    #'views/project_task_content.xml',
    ],
  'category': '',
  'depends': ['construction_site','fleet'],
}
