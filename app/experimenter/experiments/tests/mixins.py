import json
import mock

from experimenter.experiments import bugzilla
from experimenter.openidc.tests.factories import UserFactory


class MockBugzillaMixin(object):

    def setUp(self):
        super().setUp()

        mock_bugzilla_requests_post_patcher = mock.patch(
            "experimenter.experiments.bugzilla.requests.post"
        )
        self.mock_bugzilla_requests_post = (
            mock_bugzilla_requests_post_patcher.start()
        )
        self.addCleanup(mock_bugzilla_requests_post_patcher.stop)

        self.bugzilla_id = "12345"
        self.mock_bugzilla_requests_post.return_value = (
            self.buildMockSuccessResponse()
        )

    def buildMockSuccessResponse(self):
        mock_response_data = {"id": self.bugzilla_id}
        mock_response = mock.Mock()
        mock_response.content = json.dumps(mock_response_data)
        mock_response.status_code = 200
        return mock_response

    def buildMockFailureResponse(self):
        mock_response_data = {"code": bugzilla.INVALID_USER_ERROR_CODE}
        mock_response = mock.Mock()
        mock_response.content = json.dumps(mock_response_data)
        mock_response.status_code = 400
        return mock_response

    def setUpMockBugzillaInvalidUser(self):

        def mock_reject_assignee(url, bug_data):
            if "assigned_to" in bug_data:
                return self.buildMockFailureResponse()
            else:
                return self.buildMockSuccessResponse()

        self.mock_bugzilla_requests_post.side_effect = mock_reject_assignee


class MockMailMixin(object):

    def setUp(self):
        super().setUp()

        mock_send_mail_patcher = mock.patch(
            "experimenter.experiments.email.send_mail"
        )
        self.mock_send_mail = mock_send_mail_patcher.start()
        self.addCleanup(mock_send_mail_patcher.stop)


class MockRequestMixin(object):

    def setUp(self):
        super().setUp()

        self.user = UserFactory()
        self.request = mock.Mock()
        self.request.user = self.user


class MockTasksMixin(object):

    def setUp(self):
        super().setUp()

        mock_tasks_review_email_patcher = mock.patch(
            "experimenter.experiments.tasks.send_review_email_task"
        )
        self.mock_tasks_review_email = mock_tasks_review_email_patcher.start()
        self.addCleanup(mock_tasks_review_email_patcher.stop)

        mock_tasks_create_bug_patcher = mock.patch(
            "experimenter.experiments.tasks.create_experiment_bug_task"
        )
        self.mock_tasks_create_bug = mock_tasks_create_bug_patcher.start()
        self.addCleanup(mock_tasks_create_bug_patcher.stop)

        mock_tasks_add_comment_patcher = mock.patch(
            "experimenter.experiments.tasks.add_experiment_comment_task"
        )
        self.mock_tasks_add_comment = mock_tasks_add_comment_patcher.start()
        self.addCleanup(mock_tasks_add_comment_patcher.stop)
