from odoo import models, fields, api

class WorkflowTransition(models.Model):
    _name = 'workflow.transition'
    _description = 'Workflow Transition'

    name = fields.Char(compute='_compute_name', store=True)
    from_stage_id = fields.Many2one('workflow.stage', required=True, ondelete='cascade', 
                                   domain="[('flow_id', '=', flow_id)]")
    to_stage_id = fields.Many2one('workflow.stage', required=True, ondelete='cascade', 
                                 domain="[('flow_id', '=', flow_id)]")
    constraint_ids = fields.Many2many('workflow.constraint', string="Constraints")
    flow_id = fields.Many2one('workflow.flow', required=False, ondelete='cascade', default=lambda self: self.env.context.get('default_flow_id'))

    # Add SQL constraint for unique pair
    _sql_constraints = [
        ('unique_transition_pair', 'unique(from_stage_id, to_stage_id)', 
         'A transition between these two stages already exists!')
    ]


    def do(self, record, user=None):
        for constraint in self.constraint_ids:
            if not constraint.validate(record, user=user):
                return False
        return True
    
    @api.depends('from_stage_id.name', 'to_stage_id.name')
    def _compute_name(self):
        for transition in self:
            if transition.from_stage_id and transition.to_stage_id:
                transition.name = f"{transition.from_stage_id.name} → {transition.to_stage_id.name}"
            else:
                transition.name = ""

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if self.env.context.get('default_from_stage_id'):
            res['from_stage_id'] = self.env.context['default_from_stage_id']
        return res