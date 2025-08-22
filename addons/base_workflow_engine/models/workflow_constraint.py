from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval


class WorkflowConstraint(models.Model):
    _name = 'workflow.constraint'
    _description = 'Workflow Stage Constraint'

    name = fields.Char(string="Name", required=True,
                       help="Explicit name for this rule, e.g., 'Requires customer email'")

    flow_id = fields.Many2one(
        'workflow.flow',
        string="Workflow",
        required=True,
        ondelete='cascade'
    )

    domain = fields.Char(
        string="Condition",
        default="[]",
        required=True,
        help="Domain expression to be evaluated on the record. Must be true to proceed."
    )

    error_message = fields.Text(
        string="Error Message",
        required=True,
        help="Message shown to the user if the condition is not met.",
        default="The record does not meet the required conditions to move to this stage."
    )

    constraint_type = fields.Selection(
        [('restrict', 'Restrict'), ('warning', 'Warning')],
        string="Constraint Type",
        default='restrict',
        required=True
    )

    def validate(self, record):
        """
        Validates the record against the constraint's domain and user groups.
        Returns:
            (bool, str): A tuple containing a boolean indicating success or failure,
                         and a string with the error message if applicable.
        """
        self.ensure_one()
        record.ensure_one()

        # 1. Validarea domeniului
        try:
            # safe_eval necesită un context, îi oferim 'record' pentru reguli dinamice
            domain_to_eval = safe_eval(self.domain, {'record': record})

            # Folosim filtered_domain, care este mai sigur și mai eficient decât search_count
            if not record.filtered_domain(domain_to_eval):
                # Condiția nu este îndeplinită, returnăm eșec și mesajul de eroare
                return False, self.error_message
        except Exception as e:
            # Eroare de sintaxă în domeniu
            error = _("Error evaluating constraint domain: %s") % str(e)
            raise ValidationError(error)

        # 2. Dacă toate verificările au trecut
        return True, ""