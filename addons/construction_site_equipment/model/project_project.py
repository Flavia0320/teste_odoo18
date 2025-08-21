from odoo import api, fields, models, _
import json

class Project(models.Model):
    _inherit = "project.project"

    def get_panel_data(self):
        panel_data = super(Project, self).get_panel_data()
        if not self.env.user.has_groups('project.group_project_user'):
            return panel_data
        if self.is_construction_site:
            panel_data['is_construction_site'] = self.is_construction_site
            equipment_ids = self.task_ids.mapped('task_equipment_ids')
            if equipment_ids:
                panel_data['buttons'] += [{
                    'action': 'action_open_equipment',
                    'action_type': 'object',
                    'icon': 'wrench',
                    'number': len(equipment_ids),
                    'sequence': 4,
                    'show': True,
                    'text': _("Used Equipments")
                }]
                panel_data['profitability_labels']['construction_picking'] = _("Delivery from Supply WH")
                args = ['construction_equipment', [('id', 'in', equipment_ids.ids)]]
                if len(equipment_ids) == 1:
                    args.append(equipment_ids[0].id)
                panel_data['profitability_items']['costs']['data'] += [{
                    'id': 'construction_equipment',
                    'action': {'name': 'action_profitability_items', 'type': 'object', 'args': json.dumps(args)},
                    'billed': sum(equipment_ids.mapped("effective_cost")),
                    'sequence':20,
                    'to_bill': sum(equipment_ids.mapped("planned_cost"))
                }]
                panel_data['profitability_items']['costs']['total']['billed'] += sum(equipment_ids.mapped("effective_cost"))
                panel_data['profitability_items']['costs']['total']['to_bill'] += sum(equipment_ids.mapped("planned_cost"))
        return panel_data

    def action_profitability_items(self, section_name, domain=None, res_id=False):
        if section_name == 'construction_equipment':
            action = {
                'name': _('Equipment Items'),
                'type': 'ir.actions.act_window',
                'res_model': 'project.task.equipment',
                'views': [[False, 'list'], [False, 'form']],
                'domain': domain,
                'context': {
                    'create': False,
                    'edit': False,
                },
            }
            if res_id:
                action['res_id'] = res_id
                if 'views' in action:
                    action['views'] = [
                        (view_id, view_type)
                        for view_id, view_type in action['views']
                        if view_type == 'form'
                    ] or [False, 'form']
                action['view_mode'] = 'form'
            return action

        return super().action_profitability_items(section_name, domain, res_id)


    def action_open_equipment(self):
        equipment_ids = self.task_ids.mapped('task_equipment_ids')
        action_window = {
            'name': _('Equipment Items'),
            'type': 'ir.actions.act_window',
            'res_model': 'project.task.equipment',
            'views': [[False, 'list'], [False, 'form']],
            'domain': [('id', 'in', equipment_ids.ids)],
            'context': {
                'project_id': self.id,
            }
        }
        if len(equipment_ids) == 1:
            action_window['views'] = [[False, 'form']]
            action_window['res_id'] = equipment_ids[0].id
        return action_window