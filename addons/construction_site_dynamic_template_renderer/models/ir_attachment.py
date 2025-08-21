# -*- coding: utf-8 -*-
from odoo import api, models, fields


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    attachment_source = fields.Selection(
        selection=[
            ('uploaded', 'Uploaded'),
            ('processed', 'Processed')
        ],
        string="Attachment Source",
        default='uploaded',
    )

    document_template_id = fields.Many2one(
        'document.template',
        string='Document Template',
    )
