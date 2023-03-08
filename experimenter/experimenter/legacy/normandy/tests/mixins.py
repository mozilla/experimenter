import mock


class MockNormandyMixin(object):
    def setUp(self):
        super().setUp()

        mock_normandy_requests_get_patcher = mock.patch(
            "experimenter.legacy.normandy.client.requests.get"
        )
        self.mock_normandy_requests_get = mock_normandy_requests_get_patcher.start()
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
        def determine_response(url, verify=None, params={}):
            if normandy_id in url:
                return self.buildMockFailedResponse()
            else:
                return self.buildMockSuccessEnabledResponse()

        self.mock_normandy_requests_get.side_effect = determine_response


class MockNormandyTasksMixin(object):
    def setUp(self):
        super().setUp()

        mock_tasks_set_is_paused_value_patcher = mock.patch(
            "experimenter.legacy.normandy.tasks.set_is_paused_value_task"
        )
        self.mock_tasks_set_is_paused_value = (
            mock_tasks_set_is_paused_value_patcher.start()
        )
        self.addCleanup(mock_tasks_set_is_paused_value_patcher.stop)

        mock_tasks_add_start_date_comment_patcher = mock.patch(
            "experimenter.legacy.normandy.tasks.add_start_date_comment_task"
        )
        self.mock_tasks_add_start_date_comment = (
            mock_tasks_add_start_date_comment_patcher.start()
        )

        self.addCleanup(mock_tasks_add_start_date_comment_patcher.stop)

        mock_tasks_comp_experiment_update_res_patcher = mock.patch(
            "experimenter.legacy.normandy.tasks.comp_experiment_update_res_task"
        )
        self.mock_tasks_comp_experiment_update_res = (
            mock_tasks_comp_experiment_update_res_patcher.start()
        )

        self.addCleanup(mock_tasks_comp_experiment_update_res_patcher.stop)
