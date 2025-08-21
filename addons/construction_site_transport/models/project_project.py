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
            transport_ids = self.task_ids.mapped('task_transport_ids')
            if transport_ids:
                panel_data['buttons'] += [{
                    'action': 'action_open_transport',
                    'action_type': 'object',
                    'icon': 'wrench',
                    'number': len(transport_ids),
                    'sequence': 3,
                    'show': True,
                    'text': _("Used Transports")
                }]
                panel_data['profitability_labels']['construction_picking'] = _("Delivery from Supply WH")
                args = ['construction_transport', [('id', 'in', transport_ids.ids)]]
                if len(transport_ids) == 1:
                    args.append(transport_ids[0].id)
                panel_data['profitability_items']['costs']['data'] += [{
                    'id': 'construction_transport',
                    'action': {'name': 'action_profitability_items', 'type': 'object', 'args': json.dumps(args)},
                    'billed': sum(transport_ids.mapped("effective_cost")),
                    'sequence':20,
                    'to_bill': sum(transport_ids.mapped("planned_cost"))
                }]
                panel_data['profitability_items']['costs']['total']['billed'] += sum(transport_ids.mapped("effective_cost"))
                panel_data['profitability_items']['costs']['total']['to_bill'] += sum(transport_ids.mapped("planned_cost"))
        return panel_data

    def action_profitability_items(self, section_name, domain=None, res_id=False):
        if section_name == 'construction_transport':
            action = {
                'name': _('Transport Items'),
                'type': 'ir.actions.act_window',
                'res_model': 'project.task.transport',
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


    def action_open_transport(self):
        transport_ids = self.task_ids.mapped('task_transport_ids')
        action_window = {
            'name': _('Transport Items'),
            'type': 'ir.actions.act_window',
            'res_model': 'project.task.transport',
            'views': [[False, 'list'], [False, 'form']],
            'domain': [('id', 'in', transport_ids.ids)],
            'context': {
                'project_id': self.id,
            }
        }
        if len(transport_ids) == 1:
            action_window['views'] = [[False, 'form']]
            action_window['res_id'] = transport_ids[0].id
        return action_window