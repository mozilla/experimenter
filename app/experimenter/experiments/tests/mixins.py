import mock

from experimenter.openidc.tests.factories import UserFactory


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
