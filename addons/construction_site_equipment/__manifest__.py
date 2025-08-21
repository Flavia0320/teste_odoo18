# -*- coding: utf-8 -*-
{
    'name': 'Construction Site Equipment',
    'description': "Construction Site Equipment",
    'version': "18.0.1.0.2",
    'category': "Construction",
    'website': "https://dakai.ro",
    'author': "Dakai SOFT SRL",
    'maintainers': ["adrian-dks"],
    'license': "OPL-1",
    'installable': True,
    'data': [
        "security/ir.model.access.csv",
        'reports/project_cost_structure.xml',
        'reports/report_equipment.xml',
        'views/project_task_view.xml',
        'views/equipment.xml',
        # 'views/project_task_content.xml',
    ],
    'depends': [
        'construction_site',
        'maintenance',
    ],
}
