from odoo import api, SUPERUSER_ID

def uninstall_hook(env):
    action1 = env.ref('project.open_view_project_all_group_stage')
    action2 = env.ref('project.open_view_project_all_config_group_stage')
    (action1 | action2).write({
        'domain': "[]"
        })

def post_init_hook(env):
    action1 = env.ref('project.open_view_project_all_group_stage')
    action2 = env.ref('project.open_view_project_all_config_group_stage')
    (action1 | action2).write({
        'domain': "[('is_construction_site','=',False)]"
        })
