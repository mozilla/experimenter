from django import forms
from django.test import TestCase

from experimenter.projects.models import Project
from experimenter.projects.forms import (
    ProjectForm,
    NameSlugFormMixin,
    UniqueNameSlugFormMixin,
)
from experimenter.projects.tests.factories import ProjectFactory


class TestNameSlugFormMixin(TestCase):

    def setUp(self):

        class TestForm(NameSlugFormMixin, forms.ModelForm):
            name = forms.CharField()
            slug = forms.CharField(required=False)

            class Meta:
                model = Project
                fields = ("name", "slug")

        self.Form = TestForm

    def test_sets_slug_for_new_instance(self):
        form = self.Form({"name": "New Name"})
        self.assertTrue(form.is_valid())
        project = form.save()
        self.assertEqual(project.slug, "new-name")

    def test_doesnt_set_slug_for_existing_instance(self):
        project = ProjectFactory.create(name="Old Name", slug="old-slug")
        form = self.Form({"name": "New Name"}, instance=project)
        self.assertTrue(form.is_valid())
        project = form.save()
        self.assertEqual(project.name, "New Name")
        self.assertEqual(project.slug, "old-slug")


class TestUniqueNameSlugFormMixin(TestCase):

    def setUp(self):

        class TestForm(UniqueNameSlugFormMixin, forms.ModelForm):
            name = forms.CharField()
            slug = forms.CharField(required=False)

            class Meta:
                model = Project
                fields = ("name", "slug")

        self.Form = TestForm

    def test_valid_for_no_slug_match(self):
        form = self.Form({"name": "New Name"})
        self.assertTrue(form.is_valid())

    def test_invalid_for_existing_slug_match(self):
        ProjectFactory(name="Unique Existing Name", slug="existing-slug")
        form = self.Form({"name": "Existing Slug"})
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)


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
