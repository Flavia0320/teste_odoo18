from odoo import models, fields, api


class CrmLead(models.Model):
    _name = 'crm.lead'
    _inherit = ['crm.lead', 'workflow.mixin']

    # Suprascriem câmpul stage_id standard din CRM pentru a-l înlocui cu al nostru
    # Notă: Aceasta este partea cea mai complexă și poate necesita ajustări
    # O alternativă este să NU suprascriem stage_id, ci să avem un câmp separat (ex: workflow_stage_id)
    # și să sincronizăm starea. Pentru simplitate, aici îl suprascriem.
    stage_id = fields.Many2one('workflow.stage', string='Stage', ondelete='restrict',
                               tracking=True, domain="[('flow_id', '=', workflow_id)]",
                               copy=False, index=True,
                               group_expand='_read_group_stage_ids')  # Păstrăm funcționalitatea kanban

    # Suprascriem metoda compute pentru a defini cum se alege fluxul
    @api.depends('team_id', 'company_id')
    def _compute_workflow(self):
        # Exemplu: căutăm un workflow specific pentru echipa de vânzări
        for lead in self:
            domain = [('model_name', '=', 'crm.lead')]
            # Aici puteți adăuga logică complexă: ex, un workflow per echipă de vânzări
            # if lead.team_id:
            #     domain.append(('team_id', '=', lead.team_id.id))
            workflow = self.env['workflow.flow'].search(domain, limit=1)
            lead.workflow_id = workflow.id

    # Trebuie să suprascriem read_group pentru a afișa coloanele corecte în Kanban
    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        # Căutăm fluxul implicit sau cel mai comun pentru modelul curent
        # Această logică trebuie adaptată la nevoile specifice
        workflow = self.env['workflow.flow'].search([('model_name', '=', 'crm.lead')], limit=1)
        if workflow:
            return workflow.stage_ids
        return self.env['workflow.stage'].search([])