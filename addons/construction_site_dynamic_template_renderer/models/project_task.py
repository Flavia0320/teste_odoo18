from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class Task(models.Model):
    _inherit = "project.task"

    document_template_ids = fields.Many2many(
        comodel_name='document.template',
        string="Document Templates"
    )
    parameter_ids = fields.One2many(
        comodel_name='document.template.parameter',
        inverse_name='project_task_id',
        string="Parameters"
    )
    opis_parameter_ids = fields.One2many(
        comodel_name='opis.parameter',
        inverse_name='task_id',
        string="Parametri Opis",
    )
    show_opis_page = fields.Boolean(string="Parametrii OPIS", default=True)
    show_parameters_page = fields.Boolean(string="Parametrii sablon", default=True)
    opis_ok = fields.Boolean("OPIS")

    @api.onchange('document_template_ids')
    def _onchange_document_templates(self):
        if self.document_template_ids:
            self.parameter_ids = [(5, 0, 0)]
            self.opis_parameter_ids = [(5, 0, 0)]

            new_opis_parameters = []
            for template in self.document_template_ids:
                for attachment_id in template.attachment_ids:
                    new_opis_parameters.append((0, 0, {
                        'name': attachment_id.name,
                        'prefix_document': template.prefix_document,
                        'document_sablon_id': attachment_id.id,
                    }))

            self.opis_parameter_ids = new_opis_parameters

            processed_keys = set()
            new_parameters = []

            for template in self.document_template_ids:
                for param in template.parameter_ids:
                    if param.key not in processed_keys:
                        processed_keys.add(param.key)
                        new_parameters.append((0, 0, {'key': param.key, 'value': param.value or ''}))
            if self.parameter_ids:
                self.parameter_ids = self.parameter_ids + new_parameters
            else:
                self.parameter_ids = new_parameters

    def copy_parameters_to_project(self):
        if not self.project_id:
            return

        existing_parameters = {param.key: param for param in self.project_id.parameter_ids}
        new_parameters = []

        for param in self.parameter_ids:
            if param.key in existing_parameters:
                if not existing_parameters[param.key].value:
                    existing_parameters[param.key].value = param.value or ''
            else:
                new_parameters.append((0, 0, {'key': param.key, 'value': param.value or ''}))

        if new_parameters:
            self.project_id.write({'parameter_ids': new_parameters})

    def sync_parameters_hierarchy(self):
        missing_keys = {param.key for param in self.parameter_ids if not param.value}
        parameters_dict = {param.key: param for param in self.parameter_ids}
        new_parameters = []

        if self.parent_id:
            for param in self.parent_id.parameter_ids:
                if param.key in missing_keys and param.value:
                    if param.key in parameters_dict:
                        parameters_dict[param.key].value = param.value
                    else:
                        new_parameters.append((0, 0, {'key': param.key, 'value': param.value}))
                    missing_keys.remove(param.key)

        if self.project_id:
            for task in self.project_id.task_ids:
                if task.id != self.id:
                    for param in task.parameter_ids:
                        if param.key in missing_keys and param.value:
                            if param.key in parameters_dict:
                                parameters_dict[param.key].value = param.value
                            else:
                                new_parameters.append((0, 0, {'key': param.key, 'value': param.value}))
                            missing_keys.remove(param.key)

        for param in self.project_id.parameter_ids:
            if param.key in missing_keys and param.value:
                if param.key in parameters_dict:
                    parameters_dict[param.key].value = param.value
                else:
                    new_parameters.append((0, 0, {'key': param.key, 'value': param.value}))
                missing_keys.remove(param.key)

        if new_parameters:
            self.parameter_ids = self.parameter_ids + new_parameters
        self.copy_parameters_to_project()

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