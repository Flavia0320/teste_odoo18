from odoo import fields, models, _, api

class ProjectProject(models.Model):
    _inherit = "project.project"

    category_id = fields.Many2one(
        comodel_name="project.category",
        string=_("Project Type"),
        copy=False
    )

    @api.model_create_multi
    def create(self, vals_list):
        projects = super().create(vals_list)
        for project in projects:
            if not project.type_ids and project.category_id:
                project.type_ids = [(6, 0, project.category_id.mapped('project_task_type_ids').ids)]
        return projects

    def write(self, vals):
        projects = super().write(vals)
        for project in self:
            if not project.type_ids and project.category_id:
                project.type_ids = [(6, 0, project.category_id.mapped('project_task_type_ids').ids)]
        return projects