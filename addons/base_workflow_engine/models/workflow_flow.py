from odoo import models, fields, api
from odoo.exceptions import ValidationError

class WorkflowFlow(models.Model):
    _name = 'workflow.flow'
    _description = 'Workflow Flow'

    name = fields.Char(required=True)
    model_name = fields.Selection(
        selection='_get_available_models',
        string='Target Model', 
        help='Technical model name this flow applies to',
        required=True
    )
    
    current_stage_id = fields.Many2one(
        'workflow.stage',
        string='Current Stage',
        domain="[('flow_id', '=', id)]",  # Only stages belonging to this flow
        required=False,
    )

    stage_ids = fields.One2many('workflow.stage', 'flow_id', string='Stages')
    transition_ids = fields.One2many('workflow.transition', 'flow_id', string='Transitions')
    constraint_ids = fields.Many2many('workflow.constraint', string='Flow Constraints', 
                                    compute='_compute_flow_constraints', store=False)
    stage_mapping_ids = fields.One2many('workflow.stage.mapping', 'flow_id', string='Stage Mappings')
    def go_next(self, transition, record, user=None):
        if not self.current_stage_id:
            return False
        if self.current_stage_id.go(transition, record, user=user):
            self.current_stage_id = transition.to_stage_id
            return True
        return False

    @api.model
    def _get_available_models(self):
        """Get all available models from the database."""
        try:
            # Get models that are not transient and not manual
            models = self.env['ir.model'].search([
                ('transient', '=', False),  # Exclude transient models
                ('state', '!=', 'manual'),  # Exclude manual models
            ], order='name')
            
            # Create a list of tuples (model_name, display_name)
            model_list = []
            for model in models:
                # Skip models that don't have a proper name
                if model.name and model.model:
                    model_list.append((model.model, model.name))
            
            return model_list
        except Exception:
            # Fallback in case of any error
            return []

    @api.constrains('stage_ids')
    def _check_single_entry(self):
        for flow in self:
            entry_stages = flow.stage_ids.filtered('is_entry')
            if len(flow.stage_ids) > 0 and len(entry_stages) != 1:
                raise ValidationError("There must be exactly one entry stage per flow.")

    def action_create_constraint(self):
        """Open constraint creation form from flow context."""
        return {
            'name': 'Create Constraint',
            'type': 'ir.actions.act_window',
            'res_model': 'workflow.constraint',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_flow_id': self.id,
            }
        }
