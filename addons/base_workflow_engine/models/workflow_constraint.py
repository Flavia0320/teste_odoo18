from odoo import models, fields

class WorkflowConstraint(models.Model):
    _name = 'workflow.constraint'
    _description = 'Workflow Constraint'

    name = fields.Char(string="Name", help="Name for this constraint")
    domain = fields.Char(string="Domain", help="Domain expression to be evaluated", default="[]")
    group_ids = fields.Many2many('res.groups', string="Allowed Groups")
    flow_id = fields.Many2one('workflow.flow', string="Workflow Flow", 
                             help="Optional: Associate this constraint with a specific workflow")

    def validate(self, record, user=None):
        user = user or self.env.user

        # Access rights check
        if self.group_ids and not user.groups_id & self.group_ids:
            return False

        # Domain check
        try:
            result = record.browse(record.id).filtered_domain(eval(self.domain))
            return bool(result)
        except Exception:
            return False
