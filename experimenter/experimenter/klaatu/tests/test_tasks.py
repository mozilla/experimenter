from unittest import mock

from django.test import TestCase
from parameterized import parameterized

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
        mock_klaatu_client_patcher = mock.patch("experimenter.klaatu.client.KlaatuClient")
        self.mock_klaatu_client_creator = mock_klaatu_client_patcher.start()
        self.mock_klaatu_client = mock.Mock()
        self.mock_klaatu_client_creator.return_value = self.mock_klaatu_client
        self.addCleanup(mock_klaatu_client_patcher.stop)

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
            (NimbusExperiment.Application.FENIX, "fenix"),
            (NimbusExperiment.Application.IOS, "ios"),
            (NimbusExperiment.Application.DESKTOP, "windows"),
            (NimbusExperiment.Application.DESKTOP, "linux"),
            (NimbusExperiment.Application.DESKTOP, "macos"),
        ]
    )
    @mock.patch("experimenter.klaatu.client.requests.post")
    def test_klaatu_task_starts_sucessfully(self, application, os, mock_post):
        mock_post.return_value.status_code = 204
        self.create_experiment(application)

        tasks.klaatu_start_job(self.experiment, os)

    def test_klaatu_task_helper_sets_up_branches_correctly(self):
        self.create_experiment(NimbusExperiment.Application.DESKTOP)
        self.assertEqual(tasks.get_branches(self.experiment), ["control", "treatment"])

    def test_klaatu_task_helper_creates_targets_with_max_version(self):
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

    def test_klaatu_task_helper_creates_targets_with_no_max_version(self):
        self.create_experiment(NimbusExperiment.Application.DESKTOP)

        self.assertIsInstance(tasks.get_firefox_targets(self.experiment), list)
        assert "latest-nightly" and "latest-beta" in tasks.get_firefox_targets(
            self.experiment
        )

    @parameterized.expand(
        [
            ("fenix", KlaatuWorkflows.ANDROID),
            ("ios", KlaatuWorkflows.IOS),
            ("windows", KlaatuWorkflows.WINDOWS),
            ("linux", KlaatuWorkflows.LINUX),
            ("macos", KlaatuWorkflows.MACOS),
        ]
    )
    def test_klaatu_task_helper_gets_workflows_correctly(self, application, workflow):
        self.assertEqual(tasks.get_workflow(application), workflow)

    def test_klaatu_task_helper_raises_on_incorrect_workflows(self):
        with self.assertRaises(KlaatuError):
            tasks.get_workflow("ATARI 5200")

    def test_klaatu_task_helper_gets_release_firefox_version(self):
        self.assertIsInstance(tasks.get_release_version(), str)

    @mock.patch("experimenter.klaatu.client.requests.get")
    def test_klaatu_task_fetches_run_ids_and_updates_experiment(self, mock_get):
        self.create_experiment(NimbusExperiment.Application.DESKTOP)

        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "workflow_runs": [
                {"id": "123", "display_title": f"{self.experiment.slug}"},
                {"id": "456", "display_title": "Test for other-experiment"},
            ]
        }
        tasks.klaatu_get_run_id(self.experiment, "windows")

        self.assertEqual(self.experiment.klaatu_recent_run_id, 123)

    @mock.patch("experimenter.klaatu.client.requests.get")
    def test_klaatu_task_fetches_job_complete_status_and_updates_experiment(
        self, mock_get
    ):
        mock_get.return_value.status_code = 204
        self.create_experiment(NimbusExperiment.Application.DESKTOP)
        self.experiment.klaatu_recent_run_id = 123
        self.experiment.save()

        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"status": KlaatuStatus.COMPLETE}
        tasks.klaatu_check_job_complete(self.experiment, "windows")
        self.assertTrue(self.experiment.klaatu_status)
