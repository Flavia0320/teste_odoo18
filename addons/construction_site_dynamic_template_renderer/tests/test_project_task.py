# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase

class TestProjectTaskDynamicTemplate(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.project = cls.env['project.project'].create({'name': 'Test Project'})
        cls.parent_task = cls.env['project.task'].create({
            'name': 'Parent Task',
            'project_id': cls.project.id,
        })
        cls.task = cls.env['project.task'].create({
            'name': 'Child Task',
            'project_id': cls.project.id,
            'parent_id': cls.parent_task.id,
        })
        # Add parameter to parent and project
        cls.parent_param = cls.env['document.template.parameter'].create({
            'key': 'parent_key',
            'value': 'parent_value',
            'project_task_id': cls.parent_task.id,
        })
        cls.project_param = cls.env['document.template.parameter'].create({
            'key': 'project_key',
            'value': 'project_value',
            'project_id': cls.project.id,
        })
        # Add empty parameter to child
        cls.child_param = cls.env['document.template.parameter'].create({
            'key': 'parent_key',
            'value': '',
            'project_task_id': cls.task.id,
        })
        cls.child_param2 = cls.env['document.template.parameter'].create({
            'key': 'project_key',
            'value': '',
            'project_task_id': cls.task.id,
        })

    def test_copy_parameters_to_project(self):
        # Should copy missing values from task to project
        self.task.copy_parameters_to_project()
        project_param = self.project.parameter_ids.filtered(lambda p: p.key == 'parent_key')
        self.assertTrue(project_param)
        self.assertEqual(project_param.value, '')

    def test_sync_parameters_hierarchy(self):
        # Should fill missing values from parent and project
        self.task.sync_parameters_hierarchy()
        child_param = self.task.parameter_ids.filtered(lambda p: p.key == 'parent_key')
        self.assertEqual(child_param.value, 'parent_value')
        child_param2 = self.task.parameter_ids.filtered(lambda p: p.key == 'project_key')
        self.assertEqual(child_param2.value, 'project_value')