from odoo import models, fields, api

class WorkflowStage(models.Model):
    _name = 'workflow.stage'
    _description = 'Workflow Stage'

    name = fields.Char(required=True)
    description = fields.Text(string="Description")
    flow_id = fields.Many2one('workflow.flow', required=True, ondelete='cascade')
    is_entry = fields.Boolean(default=False)
    transition_ids = fields.One2many('workflow.transition', 'from_stage_id', string='Transitions')

    is_stop = fields.Boolean(compute='_compute_is_stop', store=True)

    @api.depends('transition_ids')
    def _compute_is_stop(self):
        for stage in self:
            stage.is_stop = not bool(stage.transition_ids)

    def go(self, transition, record, user=None):
        if transition not in self.transition_ids:
            return False
        return transition.do(record, user=user)
