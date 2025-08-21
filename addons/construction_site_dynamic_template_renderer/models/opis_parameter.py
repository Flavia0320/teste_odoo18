from odoo import models, fields, api

class OPISParameter(models.Model):
    _name = 'opis.parameter'
    _description = 'Parameter Opis'

    name = fields.Char(string="Nume document")
    denumire_document_opis = fields.Char(string="Denumire document Opis")
    prefix_document = fields.Char(string="Prefix document")
    cod_document = fields.Char(string="Cod document")
    data_document = fields.Date(string="Data document")
    document_sablon_id = fields.Many2one('ir.attachment', string="Doc Sablon")
    task_id = fields.Many2one(
        comodel_name='project.task',
        string="Task",
        ondelete='cascade'
    )