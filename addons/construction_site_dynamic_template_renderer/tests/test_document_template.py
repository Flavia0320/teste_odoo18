# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase
from odoo.exceptions import ValidationError
import base64
from docx import Document
from io import BytesIO

class TestDocumentTemplate(TransactionCase):

    def create_docx_attachment(self, name, variables=None):
        doc = Document()
        if variables:
            for var in variables:
                doc.add_paragraph(f"{{{{ {var} }}}}")
        stream = BytesIO()
        doc.save(stream)
        stream.seek(0)
        return self.env['ir.attachment'].create({
            'name': name,
            'datas': base64.b64encode(stream.read()),
            'mimetype': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        })

    def test_validate_attachments_accepts_only_docx(self):
        docx_att = self.create_docx_attachment('test.docx')
        template = self.env['document.template'].create({
            'name': 'Test Template',
            'attachment_ids': [(6, 0, [docx_att.id])]
        })
        self.assertIn(docx_att, template.attachment_ids)

        # Try with invalid mimetype
        att = self.env['ir.attachment'].create({
            'name': 'test.txt',
            'datas': base64.b64encode(b'hello'),
            'mimetype': 'text/plain',
        })
        with self.assertRaises(ValidationError):
            self.env['document.template'].create({
                'name': 'Invalid Template',
                'attachment_ids': [(6, 0, [att.id])]
            })

    def test_extract_variables_creates_parameters(self):
        docx_att = self.create_docx_attachment('test.docx', variables=['foo', 'bar'])
        template = self.env['document.template'].create({
            'name': 'Test Template',
            'attachment_ids': [(6, 0, [docx_att.id])]
        })
        template.extract_variables()
        keys = template.parameter_ids.mapped('key')
        self.assertIn('foo', keys)
        self.assertIn('bar', keys)