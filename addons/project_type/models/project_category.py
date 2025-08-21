from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

class ProjectCategory(models.Model):
    _name = "project.category"
    _description = "Project Category"
    _rec_name = "complete_name"

    parent_id = fields.Many2one(comodel_name="project.category", string="Parent Category")
    child_ids = fields.One2many(
        comodel_name="project.category", inverse_name="parent_id", string="Subtypes"
    )
    name = fields.Char(string="Name", required=True, translate=True)
    complete_name = fields.Char(
        string="Complete Name", compute="_compute_complete_name", store=True
    )
    sequence_code = fields.Char()
    description = fields.Text(translate=True)
    project_sequence_id = fields.Many2one("ir.sequence", _("Code Project"))
    project_task_type_ids = fields.Many2many("project.task.type", domain="[('user_id', '=', False)]")
    company_id = fields.Many2one("res.company", default=lambda x: x.env.user.company_id.id)

    @api.constrains("parent_id")
    def check_parent_id(self):
        if not self._check_recursion():
            raise ValidationError(_("You cannot create recursive project categories."))

    @api.depends("name", "parent_id.complete_name")
    def _compute_complete_name(self):
        for project_category in self:
            if project_category.parent_id:
                project_category.complete_name = "{} / {}".format(
                    project_category.parent_id.complete_name, project_category.name
                )
            else:
                project_category.complete_name = project_category.name
    
    @api.model_create_multi
    def create(self, value_list):
        res = super(ProjectCategory, self).create(value_list)
        for item in res:
            if item.sequence_code:
                item.project_sequence_id = item.generate_code()
        return res
    
    def write(self, value):
        if value.get('sequence_code'):
            value['project_sequence_id'] = self.generate_code(code=value.get('sequence_code'))
        return super(ProjectCategory, self).write(value)

    def generate_code(self, code=None):
        return self.env['ir.sequence'].sudo().create({
                    'name': self.name + ' ' + ' Tasks Sequence ',
                    'prefix': (code or self.sequence_code or '') + "/",
                    'padding': 5,
                    'company_id': self.company_id.id,
                    'implementation': 'no_gap',
                })