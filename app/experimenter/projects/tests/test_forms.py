from django.test import TestCase

from experimenter.projects.forms import ProjectForm
from experimenter.projects.tests.factories import ProjectFactory


class TestProjectForm(TestCase):

    def test_project_form_creates_project(self):
        project_name = "My Project"

        form_data = {"name": project_name}

        form = ProjectForm(form_data)

        self.assertTrue(form.is_valid())

        project = form.save()

        self.assertEqual(project.name, project_name)
        self.assertEqual(project.slug, "my-project")

    def test_project_form_requires_name(self):
        form = ProjectForm({})
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)

    def test_project_form_checks_for_name_duplicates_for_new_project(self):
        existing_project = ProjectFactory.create()

        form = ProjectForm({"name": existing_project.name})

        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)

    def test_project_form_does_not_check_name_duplicate_when_editing(self):
        project = ProjectFactory.create()

        form = ProjectForm({"name": project.name}, instance=project)

        self.assertTrue(form.is_valid())
        form.save()
