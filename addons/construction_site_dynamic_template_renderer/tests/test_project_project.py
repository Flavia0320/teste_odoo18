# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase
from odoo.exceptions import ValidationError

class TestProjectProjectDynamicTemplate(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.template1 = cls.env['document.template'].create({'name': 'Template 1'})
        cls.template2 = cls.env['document.template'].create({'name': 'Template 2'})
        cls.param1 = cls.env['document.template.parameter'].create({
            'key': 'param1',
            'value': 'value1',
            'template_id': cls.template1.id,
        })
        cls.param2 = cls.env['document.template.parameter'].create({
            'key': 'param2',
            'value': 'value2',
            'template_id': cls.template2.id,
        })
        cls.project = cls.env['project.project'].create({'name': 'Test Project'})

    def test_onchange_document_template_ids_sets_parameters(self):
        self.project.document_template_ids = [(6, 0, [self.template1.id, self.template2.id])]
        self.project._onchange_document_templates()
        keys = set(self.project.parameter_ids.mapped('key'))
        self.assertIn('param1', keys)
        self.assertIn('param2', keys)

    def test_onchange_document_template_ids_clears_parameters(self):
        self.project.document_template_ids = [(6, 0, [self.template1.id])]
        self.project._onchange_document_templates()
        self.project.document_template_ids = [(5, 0, 0)]
        self.project._onchange_document_templates()
        self.assertFalse(self.project.parameter_ids, "Parameters should be cleared when no templates are set.")

    def test_render_raises_if_no_templates(self):
        with self.assertRaises(ValidationError):
            self.project.render()