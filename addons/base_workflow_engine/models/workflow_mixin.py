from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class WorkflowMixin(models.AbstractModel):
    _name = 'workflow.mixin'
    _description = 'Mixin for Non-Invasive Workflow Engine'

    # NU mai definim stage_id aici, pentru a nu-l suprascrie pe cel nativ.

    workflow_id = fields.Many2one(
        'workflow.flow',
        compute='_compute_workflow',
        store=True,
        readonly=False
    )
    # Acesta este câmpul paralel care ține evidența stării în motorul nostru de flux.
    workflow_stage_id = fields.Many2one(
        'workflow.stage',
        string='Workflow Stage',
        ondelete='restrict',
        tracking=True,
        domain="[('flow_id', '=', workflow_id)]",
        copy=False
    )

    # metoda _compute_workflow
    @api.depends('company_id')
    def _compute_workflow(self):
        for rec in self:
            rec.workflow_id = self.env['workflow.flow'].search([
                ('model_name', '=', self._name)
            ], limit=1)

    def _get_mapping(self, reverse=False):
        """ Construiește și returnează dicționarul de mapare pentru fluxul curent. """
        self.ensure_one()
        if not self.workflow_id:
            return {}

        mappings = self.env['workflow.stage.mapping'].search([
            ('flow_id', '=', self.workflow_id.id)
        ])

        if reverse:
            # Mapare: (model.nativ, id) -> workflow.stage()
            return {
                (m.native_stage_id._name, m.native_stage_id.id): m.workflow_stage_id
                for m in mappings if m.native_stage_id
            }

        # Mapare: workflow.stage() -> model.nativ()
        return {
            m.workflow_stage_id: m.native_stage_id
            for m in mappings if m.native_stage_id
        }

    def _execute_transition(self, new_workflow_stage):
        """ Logica centrală care validează și execută o tranziție. """
        self.ensure_one()
        current_workflow_stage = self.workflow_stage_id

        # 1. Validare Tranziție Permisă
        allowed_transitions = current_workflow_stage.transition_ids.filtered(
            lambda t: t.to_stage_id == new_workflow_stage
        )
        if not allowed_transitions:
            raise UserError(_("Transition from '%s' to '%s' is not allowed.") %
                            (current_workflow_stage.name, new_workflow_stage.name))

        # 2. Validare Constrângeri
        transition = allowed_transitions[0]
        for constraint in transition.constraint_ids:
            is_valid, error_msg = constraint.validate(self)
            if not is_valid:
                raise ValidationError(error_msg)

        # 3. Executare Tranziție & Sincronizare
        mapping = self._get_mapping()
        native_stage = mapping.get(new_workflow_stage)

        if not native_stage:
            raise UserError(_("No native stage mapping found for workflow stage '%s'.") % new_workflow_stage.name)

        # Actualizăm ambele câmpuri: cel nativ și cel de workflow
        self.write({
            'stage_id': native_stage.id,  # Presupunem că field-ul nativ se numește 'stage_id'
            'workflow_stage_id': new_workflow_stage.id
        })

    @api.model
    def create(self, vals):
        """ La creare, setează starea inițială a fluxului și o sincronizează cu starea nativă. """
        record = super().create(vals)
        if record.workflow_id:
            entry_stage = record.workflow_id.stage_ids.filtered('is_entry')
            if entry_stage:
                mapping = record._get_mapping()
                native_stage = mapping.get(entry_stage)
                if native_stage:
                    record.write({
                        'stage_id': native_stage.id,
                        'workflow_stage_id': entry_stage.id
                    })
        return record

    def write(self, vals):
        """ Suprascriem 'write' pentru a capta schimbările făcute direct pe etapa nativă (ex: drag-and-drop). """
        if 'stage_id' in vals and self.env.context.get('bypass_workflow') is not True:
            new_native_stage_id = vals['stage_id']
            for record in self:
                reverse_mapping = record._get_mapping(reverse=True)
                native_model_name = self.env['crm.stage'].browse(new_native_stage_id)._name  # Exemplu pentru CRM

                new_workflow_stage = reverse_mapping.get((native_model_name, new_native_stage_id))

                if new_workflow_stage and new_workflow_stage != record.workflow_stage_id:
                    # Am detectat o schimbare nativă, acum validăm prin motorul nostru de flux
                    try:
                        # Folosim _execute_transition pentru a rula toate validările
                        record.with_context(bypass_workflow=True)._execute_transition(new_workflow_stage)
                    except (UserError, ValidationError) as e:
                        # Blocăm tranziția dacă nu respectă regulile fluxului
                        raise UserError(_("The transition is blocked by the workflow engine: %s") % str(e))

        return super().write(vals)