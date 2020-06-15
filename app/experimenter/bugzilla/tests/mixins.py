import mock

from experimenter import bugzilla


class MockBugzillaMixin(object):
    def setUp(self):
        super().setUp()

        mock_bugzilla_requests_post_patcher = mock.patch(
            "experimenter.bugzilla.client.requests.post"
        )
        self.mock_bugzilla_requests_post = mock_bugzilla_requests_post_patcher.start()
        self.addCleanup(mock_bugzilla_requests_post_patcher.stop)
        self.bugzilla_id = "12345"
        self.mock_bugzilla_requests_post.return_value = self.buildMockSuccessResponse()
        mock_bugzilla_requests_put_patcher = mock.patch(
            "experimenter.bugzilla.client.requests.put"
        )

        self.mock_bugzilla_requests_put = mock_bugzilla_requests_put_patcher.start()
        self.addCleanup(mock_bugzilla_requests_put_patcher.stop)
        self.mock_bugzilla_requests_put.return_value = self.buildMockSuccessResponse()

        mock_bugzilla_requests_get_patcher = mock.patch(
            "experimenter.bugzilla.client.requests.get"
        )

        self.mock_bugzilla_requests_get = mock_bugzilla_requests_get_patcher.start()
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


class MockBugzillaTasksMixin(object):
    def setUp(self):
        super().setUp()

        mock_tasks_create_bug_patcher = mock.patch(
            "experimenter.bugzilla.tasks.create_experiment_bug_task"
        )
        self.mock_tasks_create_bug = mock_tasks_create_bug_patcher.start()
        self.addCleanup(mock_tasks_create_bug_patcher.stop)

        mock_tasks_update_experiment_bug_patcher = mock.patch(
            "experimenter.bugzilla.tasks.update_experiment_bug_task"
        )
        self.mock_tasks_update_experiment_bug = (
            mock_tasks_update_experiment_bug_patcher.start()
        )
        self.addCleanup(mock_tasks_update_experiment_bug_patcher.stop)

        mock_tasks_update_bug_resolution_patcher = mock.patch(
            "experimenter.bugzilla.tasks.update_bug_resolution_task"
        )
        self.mock_tasks_update_bug_resolution = (
            mock_tasks_update_bug_resolution_patcher.start()
        )
        self.addCleanup(mock_tasks_update_bug_resolution_patcher.stop)

        mock_tasks_add_start_date_comment_patcher = mock.patch(
            "experimenter.bugzilla.tasks.add_start_date_comment_task"
        )
        self.mock_tasks_add_start_date_comment = (
            mock_tasks_add_start_date_comment_patcher.start()
        )

        self.addCleanup(mock_tasks_add_start_date_comment_patcher.stop)

        mock_tasks_comp_experiment_update_res_patcher = mock.patch(
            "experimenter.bugzilla.tasks.comp_experiment_update_res_task"
        )
        self.mock_tasks_comp_experiment_update_res = (
            mock_tasks_comp_experiment_update_res_patcher.start()
        )

        self.addCleanup(mock_tasks_comp_experiment_update_res_patcher.stop)
