import mock

from experimenter.experiments import bugzilla
from experimenter.openidc.tests.factories import UserFactory


class MockNormandyMixin(object):

    def setUp(self):
        super().setUp()

        mock_normandy_requests_get_patcher = mock.patch(
            "experimenter.experiments.normandy.requests.get"
        )
        self.mock_normandy_requests_get = (
            mock_normandy_requests_get_patcher.start()
        )
        self.addCleanup(mock_normandy_requests_get_patcher.stop)
        self.mock_normandy_requests_get.return_value = (
            self.buildMockSuccessEnabledResponse()
        )

    def buildMockSuccessEnabledResponse(self):
        mock_response_data = {
            "approved_revision": {
                "enabled": True,
                "enabled_states": [{"creator": {"email": "dev@example.com"}}],
                "arguments": {"isEnrollmentPaused": True},
            }
        }
        mock_response = mock.Mock()
        mock_response.json = mock.Mock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status = mock.Mock()
        mock_response.raise_for_status.side_effect = None
        mock_response.status_code = 200
        return mock_response

    def buildMockFailedResponse(self):
        mock_response_data = {"message": "id not found"}
        mock_response = mock.Mock()
        mock_response.json = mock.Mock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status = mock.Mock()
        mock_response.raise_for_status.side_effect = None
        mock_response.status_code = 404
        return mock_response

    def buildMockSuccessDisabledResponse(self):
        mock_response_data = {
            "approved_revision": {
                "enabled": False,
                "enabled_states": [{"creator": {"email": "dev@example.com"}}],
            }
        }
        mock_response = mock.Mock()
        mock_response.json = mock.Mock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status = mock.Mock()
        mock_response.raise_for_status.side_effect = None
        mock_response.status_code = 200
        return mock_response

    def buildMockSucessWithNoPauseEnrollment(self):
        mock_response_data = {
            "approved_revision": {
                "enabled": True,
                "enabled_states": [{"creator": None}],
                "arguments": {"isEnrollmentPaused": False},
            }
        }
        mock_response = mock.Mock()
        mock_response.json = mock.Mock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status = mock.Mock()
        mock_response.raise_for_status.side_effect = None
        mock_response.status_code = 200
        return mock_response

    def setUpMockNormandyFailWithSpecifiedID(self, normandy_id):

        def determine_response(url):
            if normandy_id in url:
                return self.buildMockFailedResponse()
            else:
                return self.buildMockSuccessEnabledResponse()

        self.mock_normandy_requests_get.side_effect = determine_response


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
        mock_bugzilla_requests_put_patcher = mock.patch(
            "experimenter.experiments.bugzilla.requests.put"
        )

        self.mock_bugzilla_requests_put = (
            mock_bugzilla_requests_put_patcher.start()
        )
        self.addCleanup(mock_bugzilla_requests_put_patcher.stop)
        self.mock_bugzilla_requests_put.return_value = (
            self.buildMockSuccessResponse()
        )

        mock_bugzilla_requests_get_patcher = mock.patch(
            "experimenter.experiments.bugzilla.requests.get"
        )

        self.mock_bugzilla_requests_get = (
            mock_bugzilla_requests_get_patcher.start()
        )
        self.addCleanup(mock_bugzilla_requests_get_patcher.stop)
        responses = [
            self.buildMockSuccessUserResponse(),
            self.buildMockSuccessBugResponse(),
            self.buildMockSuccessBugResponse(),
        ]
        self.mock_bugzilla_requests_get.side_effect = responses

    def buildMockSuccessUserResponse(self, *args):
        mock_response_data = {"users": [{"email": "dev@example.com"}]}
        mock_response = mock.Mock()
        mock_response.json = mock.Mock()
        mock_response.json.return_value = mock_response_data
        mock_response.status_code = 200
        return mock_response

    def buildMockSuccessBugResponse(self):
        mock_response_data = {"bugs": [{"id": 1234}]}
        mock_response = mock.Mock()
        mock_response.json = mock.Mock()
        mock_response.json.return_value = mock_response_data
        mock_response.status_code = 200
        return mock_response

    def buildMockSuccessResponse(self):
        mock_response_data = {"id": self.bugzilla_id}
        mock_response = mock.Mock()
        mock_response.json = mock.Mock()
        mock_response.json.return_value = mock_response_data
        mock_response.status_code = 200
        return mock_response

    def buildMockFailureResponse(self):
        mock_response_data = {"code": bugzilla.INVALID_USER_ERROR_CODE}
        mock_response = mock.Mock()
        mock_response.json = mock.Mock()
        mock_response.json.return_value = mock_response_data
        mock_response.status_code = 400
        return mock_response

    def setupMockBugzillaCreationFailure(self):
        mock_response_data = {"message": "something went wrong"}
        mock_response = mock.Mock()
        mock_response.json = mock.Mock()
        mock_response.json.return_value = mock_response_data
        mock_response.status_code = 400
        self.mock_bugzilla_requests_post.return_value = mock_response


class MockRequestMixin(object):

    def setUp(self):
        super().setUp()

        self.user = UserFactory()
        self.request = mock.Mock()
        self.request.user = self.user


class MockTasksMixin(object):

    def setUp(self):
        super().setUp()

        mock_tasks_create_bug_patcher = mock.patch(
            "experimenter.experiments.tasks.create_experiment_bug_task"
        )
        self.mock_tasks_create_bug = mock_tasks_create_bug_patcher.start()
        self.addCleanup(mock_tasks_create_bug_patcher.stop)

        mock_tasks_update_experiment_bug_patcher = mock.patch(
            "experimenter.experiments.tasks.update_experiment_bug_task"
        )
        self.mock_tasks_update_experiment_bug = (
            mock_tasks_update_experiment_bug_patcher.start()
        )
        self.addCleanup(mock_tasks_update_experiment_bug_patcher.stop)

        mock_tasks_update_bug_resolution_patcher = mock.patch(
            "experimenter.experiments.tasks.update_bug_resolution_task"
        )
        self.mock_tasks_update_bug_resolution = (
            mock_tasks_update_bug_resolution_patcher.start()
        )
        self.addCleanup(mock_tasks_update_bug_resolution_patcher.stop)

        mock_tasks_add_start_date_comment_patcher = mock.patch(
            "experimenter.experiments.tasks.add_start_date_comment_task"
        )
        self.mock_tasks_add_start_date_comment = (
            mock_tasks_add_start_date_comment_patcher.start()
        )

        self.addCleanup(mock_tasks_add_start_date_comment_patcher.stop)

        mock_tasks_comp_experiment_update_res_patcher = mock.patch(
            "experimenter.experiments.tasks.comp_experiment_update_res_task"
        )
        self.mock_tasks_comp_experiment_update_res = (
            mock_tasks_comp_experiment_update_res_patcher.start()
        )

        self.addCleanup(mock_tasks_comp_experiment_update_res_patcher.stop)

        mock_tasks_set_is_paused_value_patcher = mock.patch(
            "experimenter.experiments.tasks.set_is_paused_value_task"
        )
        self.mock_tasks_set_is_paused_value = (
            mock_tasks_set_is_paused_value_patcher.start()
        )
        self.addCleanup(mock_tasks_set_is_paused_value_patcher.stop)

        mock_tasks_update_ds_bug_patcher = mock.patch(
            "experimenter.experiments.tasks.update_ds_bug_task"
        )

        self.mock_tasks_update_bug_ds = (
            mock_tasks_update_ds_bug_patcher.start()
        )
        self.addCleanup(mock_tasks_update_ds_bug_patcher.stop)

        mock_tasks_update_exp_id_to_ds_bug_patcher = mock.patch(
            "experimenter.experiments.tasks.update_exp_id_to_ds_bug_task"
        )

        self.mock_tasks_update_exp_id_to_ds_bug = (
            mock_tasks_update_exp_id_to_ds_bug_patcher.start()
        )
        self.addCleanup(mock_tasks_update_exp_id_to_ds_bug_patcher.stop)
