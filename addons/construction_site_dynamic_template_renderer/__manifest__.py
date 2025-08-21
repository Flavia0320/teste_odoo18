# -*- coding: utf-8 -*-
{
    'name': 'Construction site dynamic template renderer',
    'description': "",
    'version': '18.0.2.0',
    'author': 'Dakai SOFT',
    'data': [
        'security/ir.model.access.csv',
        'views/document_template_parameter_view.xml',
        'views/document_template_view.xml',
        'views/project_views.xml',
        'wizard/document_render_wizard_views.xml',
    ],
    'installable': True,
    'depends': ['project', 'construction_site'],
    'external_dependencies': {
        'python' : ['python-docx'],
    },
}
