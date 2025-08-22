from odoo import models, fields, api

class WorkflowStageMapping(models.Model):
    _name = 'workflow.stage.mapping'
    _description = 'Workflow Stage to Native Stage Mapping'
    _rec_name = 'workflow_stage_id'

    flow_id = fields.Many2one(
        'workflow.flow',
        string='Workflow',
        required=True,
        ondelete='cascade'
    )
    workflow_stage_id = fields.Many2one(
        'workflow.stage',
        string='Workflow Stage',
        domain="[('flow_id', '=', flow_id)]",
        required=True
    )
    # Folosim un câmp Reference pentru a putea lega la orice model de etape (crm.stage, project.task.type, etc.)
    native_stage_id = fields.Reference(
        selection='_get_native_stage_models',
        string='Native Model Stage',
        required=True
    )

    @api.model
    def _get_native_stage_models(self):
        # Această metodă ar putea fi extinsă pentru a oferi o listă de modele de etape comune
        return [
            # De implementat in CRM Workflow
            ('crm.stage', 'CRM Stage'),
            ('project.task.type', 'Project Task Type'),
            # Adăugați aici alte modele de etape pe măsură ce integrați cu noi aplicații
        ]

    _sql_constraints = [
        ('uniq_workflow_stage_mapping', 'unique(flow_id, workflow_stage_id)',
         'This workflow stage is already mapped.'),
        ('uniq_native_stage_mapping', 'unique(flow_id, native_stage_id)',
         'This native stage is already mapped.'),
    ]