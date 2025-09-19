from unittest import mock

from django.test import TestCase, override_settings
from parameterized import parameterized

from experimenter.experiments.constants import NimbusConstants
from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tests.factories import (
    NimbusBranchFactory,
    NimbusExperimentFactory,
    NimbusFeatureConfigFactory,
)
from experimenter.klaatu import tasks
from experimenter.klaatu.client import KlaatuError, KlaatuStatus, KlaatuWorkflows
from experimenter.openidc.tests.factories import UserFactory


class TestNimbusKlaatuTasks(TestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        mock_klaatu_client_patcher = mock.patch("experimenter.klaatu.tasks.KlaatuClient")
        self.mock_klaatu_client_creator = mock_klaatu_client_patcher.start()
        self.mock_klaatu_client = mock.Mock()
        self.mock_klaatu_client_creator.return_value = self.mock_klaatu_client

        self.addCleanup(mock.patch.stopall)

    def create_experiment(self, application):
        feature_config1 = NimbusFeatureConfigFactory.create(application=application)
        feature_config2 = NimbusFeatureConfigFactory.create(application=application)
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=application,
            feature_configs=[feature_config1, feature_config2],
            firefox_min_version=NimbusExperiment.Version.FIREFOX_130,
            equal_branch_ratio=False,
            is_localized=False,
            is_rollout=False,
            localizations=None,
            prevent_pref_conflicts=False,
            warn_feature_schema=False,
        )
        experiment.branches.all().delete()
        experiment.changes.all().delete()

        reference_branch = NimbusBranchFactory.create(
            experiment=experiment,
            name="control",
            ratio=1,
            firefox_labs_title="control branch",
        )
        NimbusBranchFactory.create(
            experiment=experiment,
            name="treatment",
            ratio=1,
            firefox_labs_title="treatment branch",
        )
        experiment.reference_branch = reference_branch

        experiment.save()
        self.experiment = NimbusExperiment.objects.get(id=experiment.id)

    @parameterized.expand(
        [
            (NimbusExperiment.Application.FENIX),
            (NimbusExperiment.Application.IOS),
            (NimbusExperiment.Application.DESKTOP),
        ]
    )
    @mock.patch("experimenter.klaatu.client.requests.post")
    @mock.patch.object(tasks, "_create_auth_token", return_value="gh_123abc456xyz")
    def test_klaatu_task_starts_sucessfully(self, application, mock_client, mock_post):
        mock_post.return_value.status_code = 204
        self.create_experiment(application)

        tasks.klaatu_start_job(self.experiment.id)

    @mock.patch.object(tasks, "_create_auth_token", return_value="gh_123abc456xyz")
    def test_klaatu_task_helper_sets_up_branches_correctly(self, mock_client):
        self.create_experiment(NimbusExperiment.Application.DESKTOP)
        self.assertEqual(tasks.get_branches(self.experiment), ["control", "treatment"])

    @mock.patch.object(tasks, "_create_auth_token", return_value="gh_123abc456xyz")
    def test_klaatu_task_helper_creates_targets_with_max_version(self, mock_client):
        self.create_experiment(NimbusExperiment.Application.DESKTOP)
        self.experiment.firefox_max_version = NimbusExperiment.Version.FIREFOX_135
        self.experiment.save()

        self.assertEqual(
            tasks.get_firefox_targets(self.experiment),
            [
                "130.0.1",
                "131.2.0",
                "132.0",
                "133.0.1",
                "134.1.0",
                "135.1.0",
            ],
        )

    @mock.patch.object(tasks, "_create_auth_token", return_value="gh_123abc456xyz")
    def test_klaatu_task_helper_creates_targets_with_no_max_version(self, mock_client):
        self.create_experiment(NimbusExperiment.Application.DESKTOP)

        self.assertIsInstance(tasks.get_firefox_targets(self.experiment), list)
        assert "latest-nightly" and "latest-beta" in tasks.get_firefox_targets(
            self.experiment
        )

    @parameterized.expand(
        [
            (NimbusConstants.Application.FENIX, [KlaatuWorkflows.ANDROID]),
            (NimbusConstants.Application.IOS, [KlaatuWorkflows.IOS]),
            (
                NimbusConstants.Application.DESKTOP,
                [KlaatuWorkflows.WINDOWS, KlaatuWorkflows.LINUX, KlaatuWorkflows.MACOS],
            ),
        ]
    )
    @mock.patch.object(tasks, "_create_auth_token", return_value="gh_123abc456xyz")
    def test_klaatu_task_helper_gets_workflows_correctly(
        self, application, workflow, mock_client
    ):
        self.assertEqual(tasks.get_workflows(application), workflow)

    @mock.patch.object(tasks, "_create_auth_token", return_value="gh_123abc456xyz")
    def test_klaatu_task_helper_raises_on_incorrect_workflows(self, mock_client):
        with self.assertRaises(KlaatuError):
            tasks.get_workflows("ATARI 5200")

    @mock.patch.object(tasks, "_create_auth_token", return_value="gh_123abc456xyz")
    def test_klaatu_task_helper_gets_release_firefox_version(self, mock_client):
        self.assertIsInstance(tasks.get_release_version(), str)

    @mock.patch("experimenter.klaatu.client.requests.get")
    @mock.patch.object(tasks, "_create_auth_token", return_value="gh_123abc456xyz")
    def test_klaatu_task_fetches_run_ids_and_updates_experiment(
        self, mock_client, mock_get
    ):
        run_ids = [123, 456, 789]
        self.create_experiment(NimbusConstants.Application.DESKTOP)

        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "workflow_runs": [
                {"id": f"{run_ids[0]}", "display_title": f"{self.experiment.slug}"},
                {"id": f"{run_ids[1]}", "display_title": f"{self.experiment.slug}"},
                {"id": f"{run_ids[2]}", "display_title": f"{self.experiment.slug}"},
                {"id": "321", "display_title": "Test for other-experiment"},
            ]
        }
        self.mock_klaatu_client.find_run_ids.return_value = run_ids
        tasks.klaatu_get_run_ids(self.experiment, NimbusConstants.Application.DESKTOP)

        for _id in run_ids:
            self.assertIn(_id, self.experiment.klaatu_recent_run_ids)

    @parameterized.expand([(True), (False)])
    @mock.patch("experimenter.klaatu.client.requests.get")
    @mock.patch.object(tasks, "_create_auth_token", return_value="gh_123abc456xyz")
    def test_klaatu_task_fetches_job_complete_status_and_updates_experiment(
        self, value, mock_client, mock_get
    ):
        mock_get.return_value.status_code = 204
        self.create_experiment(NimbusConstants.Application.DESKTOP)
        self.experiment.klaatu_recent_run_ids.append(123)
        self.experiment.save()

        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"status": KlaatuStatus.COMPLETE}
        self.mock_klaatu_client.is_job_complete.return_value = value

        tasks.klaatu_check_jobs_complete(
            self.experiment, NimbusConstants.Application.DESKTOP
        )

        self.assertEqual(self.experiment.klaatu_status, value)

    def test_klaatu_task_auth_token_generation(self):
        with override_settings(
            GH_APP_ID=1,
            GH_INSTALLATION_ID=2,
            GH_APP_PRIVATE_KEY="-----BEGIN KEY-----\\nabc\\n-----END KEY-----",
        ):
            jwt_patcher = mock.patch(
                "experimenter.klaatu.tasks.jwt.encode", return_value="jwt123"
            )
            post_patcher = mock.patch("experimenter.klaatu.tasks.requests.post")

            jwt_patcher.start()
            mock_post = post_patcher.start()
            self.addCleanup(jwt_patcher.stop)
            self.addCleanup(post_patcher.stop)

            mock_response = mock_post.return_value
            mock_response.json.return_value = {"token": "gh_123abc456xyz"}

            token = tasks._create_auth_token()
        self.assertEqual(token, "gh_123abc456xyz")

    @mock.patch("experimenter.klaatu.client.requests.post")
    @mock.patch.object(tasks, "_create_auth_token", return_value="gh_123abc456xyz")
    def test_klaatu_task_stage_job_starts_correctly(self, mock_client, mock_post):
        with override_settings(
            IS_STAGING=True,
        ):
            application = NimbusExperiment.Application.DESKTOP
            mock_post.return_value.status_code = 204
            self.create_experiment(application)

            tasks.klaatu_start_job(self.experiment.id)
