from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ProjectProject(models.Model):
    _inherit = 'project.project'

    document_template_ids = fields.Many2many(
        comodel_name='document.template',
        string="Document Templates"
    )
    parameter_ids = fields.One2many(
        comodel_name='document.template.parameter',
        inverse_name='project_project_id',
        string="Parameters"
    )

    @api.onchange('document_template_ids')
    def _onchange_document_templates(self):
        if self.document_template_ids:
            self.parameter_ids = [(5, 0, 0)]
            processed_keys = set()
            new_parameters = []

            for template in self.document_template_ids:
                for param in template.parameter_ids:
                    if param.key not in processed_keys:
                        processed_keys.add(param.key)
                        new_parameters.append((0, 0, {'key': param.key, 'value': param.value or ''}))

            self.parameter_ids = new_parameters
        else:
            self.parameter_ids = [(5, 0, 0)]

    def render(self):
        if not self.document_template_ids:
            raise ValidationError("Nu există șabloane de documente asociate cu acest proiect.")

        # for template in self.document_template_ids:
        self.env['document.template'].render(self.id, self._name)

    def render_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'document.render.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'active_id': self.id},
        }
