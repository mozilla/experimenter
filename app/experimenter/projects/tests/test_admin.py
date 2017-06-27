import mock

from django.test import TestCase

from experimenter.projects.admin import ProjectAdmin


class ProjectAdminTest(TestCase):

    def test_has_no_delete_permission(self):
        project_admin = ProjectAdmin(mock.Mock(), mock.Mock())
        self.assertFalse(project_admin.has_delete_permission(mock.Mock()))
