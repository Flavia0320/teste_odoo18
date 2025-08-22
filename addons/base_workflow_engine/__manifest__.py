{
    'name': 'Base Workflow Engine',
    'version': '18.0.1.0.0',
    'category': 'Generic Modules/Base',
    'summary': 'Abstract workflow engine to create dynamic stages and transitions for any Odoo model.',
    'author': 'Dakai SOFT SRL',
    'website': 'https://dakai.ro',
    'depends': [
        'base', 'mail',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/workflow_security.xml',
        'views/workflow_stage_mapping_views.xml',
        'views/workflow_constraint_views.xml',
        'views/workflow_transition_views.xml',
        'views/workflow_stage_views.xml',
        'views/workflow_flow_views.xml',

        'views/menu.xml',
    ],
    'demo': [
        'demo/workflow_demo.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'OPL-1',
}