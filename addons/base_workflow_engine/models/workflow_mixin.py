from odoo import models, fields, api, _
from odoo.exceptions import UserError


class WorkflowMixin(models.AbstractModel):
    _name = 'workflow.mixin'
    _description = 'Mixin for Workflow Engine Integration'

    # Câmpurile care vor fi adăugate modelului țintă
    workflow_id = fields.Many2one('workflow.flow', compute='_compute_workflow', store=True, readonly=False)
    stage_id = fields.Many2one('workflow.stage', string='Stage', ondelete='restrict',
                               tracking=True, domain="[('flow_id', '=', workflow_id)]")

    # Trebuie să fie suprascris în modelul final
    @api.depends('project_id', 'company_id')  # Exemplu pentru project.task
    def _compute_workflow(self):
        """ This method must be implemented on the target model. """
        for rec in self:
            # Logic to find the correct workflow for this record
            # Ex: based on project type, company, etc.
            rec.workflow_id = self.env['workflow.flow'].search([
                ('model_name', '=', self._name)
            ], limit=1)

    def _check_stage_constraints(self, stage):
        """ Verifică toate constrângerile pentru etapa destinație. """
        for constraint in stage.constraint_ids:
            constraint.check_constraint(self)

    def _run_stage_entry_actions(self, stage):
        """ Rulează toate acțiunile de server la intrarea în etapă. """
        for action in stage.action_ids:
            action.run_action(self)

    def write(self, vals):
        """ Suprascriem 'write' pentru a controla tranziția între etape. """
        if 'stage_id' in vals and vals['stage_id']:
            new_stage = self.env['workflow.stage'].browse(vals['stage_id'])
            for record in self:
                # 1. Verifică permisiunile (Cerința #6)
                if not self.env.user.has_group(
                        'base.group_user') and not record.stage_id.allowed_group_ids & self.env.user.groups_id:
                    raise UserError(_("You are not allowed to move the record from stage '%s'.") % record.stage_id.name)

                # 2. Verifică dacă tranziția este validă
                allowed_transitions = record.stage_id.transition_ids.mapped('stage_to_id')
                if new_stage not in allowed_transitions:
                    raise UserError(_("Moving from '%s' to '%s' is not an allowed transition.") % (
                    record.stage_id.name, new_stage.name))

                # 3. Verifică constrângerile (Cerința #2)
                record._check_stage_constraints(new_stage)

        res = super().write(vals)

        # 4. Rulează acțiunile după ce scrierea a avut loc
        if 'stage_id' in vals:
            new_stage = self.env['workflow.stage'].browse(vals['stage_id'])
            for record in self:
                record._run_stage_entry_actions(new_stage)

        # 5. Logica de auto-tranziție (Cerința #7)
        if 'stage_id' in vals:
            self._check_for_auto_transition()

        return res

    def get_next_possible_stages(self):
        """ Funcția pentru "next flow" (Cerința #5). Returnează etapele următoare posibile. """
        self.ensure_one()
        return self.stage_id.transition_ids.mapped('stage_to_id')

    def _check_for_auto_transition(self):
        """ Cerința #7 (Opțional): Trece automat la etapa următoare dacă sunt îndeplinite condițiile. """
        for record in self:
            # Simplificare: Considerăm o singură tranziție posibilă pentru automatizare
            if len(record.stage_id.transition_ids) == 1:
                next_stage = record.stage_id.transition_ids.stage_to_id
                try:
                    # Verificăm constrângerile fără a arunca eroare
                    all_ok = True
                    for constraint in next_stage.constraint_ids:
                        domain = safe_eval(constraint.domain, {'record': record, 'env': self.env})
                        if not record.search_count(domain + [('id', '=', record.id)]):
                            all_ok = False
                            break
                    if all_ok:
                        record.write({'stage_id': next_stage.id})
                except Exception:
                    # Constrângerea nu e îndeplinită, nu facem nimic
                    pass