from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from experimenter.projects.tests.factories import ProjectFactory
from experimenter.projects.models import Project


class TestProjectListView(TestCase):

    def test_list_view_returns_projects(self):
        headers = {
            settings.OPENIDC_EMAIL_HEADER: 'user@example.com',
        }
        response = self.client.get(reverse('projects-list'), **headers)
        self.assertEqual(response.status_code, 200)


class TestProjectCreateView(TestCase):

    def test_project_create_view_creates_project_and_redirects(self):
        headers = {
            settings.OPENIDC_EMAIL_HEADER: 'user@example.com',
        }

        project_data = {
            'name': 'My Project',
        }

        response = self.client.post(
            reverse('projects-create'), project_data, **headers)

        project = Project.objects.get()

        self.assertEqual(project.name, project_data['name'])
        self.assertEqual(project.slug, 'my-project')
        self.assertRedirects(
            response,
            reverse('projects-detail', kwargs={'slug': project.slug}),
            fetch_redirect_response=False,
        )


class TestProjectUpdateView(TestCase):

    def test_project_update_view_updates_project(self):
        project = ProjectFactory.create()

        headers = {
            settings.OPENIDC_EMAIL_HEADER: 'user@example.com',
        }

        project_data = {
            'name': 'New Name',
        }

        response = self.client.post(
            reverse('projects-update', kwargs={'slug': project.slug}),
            project_data,
            **headers
        )

        updated_project = Project.objects.get(id=project.id)

        self.assertEqual(updated_project.name, project_data['name'])
        self.assertEqual(updated_project.slug, 'new-name')
        self.assertRedirects(
            response,
            reverse('projects-detail', kwargs={'slug': updated_project.slug}),
            fetch_redirect_response=False,
        )
