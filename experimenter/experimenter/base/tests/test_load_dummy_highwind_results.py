from django.core.management import call_command
from django.test import TestCase

from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tests.factories import NimbusExperimentFactory


class TestLoadDummyHighwindResults(TestCase):
    def test_loads_results_onto_live_and_complete_experiments(self):
        live = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE
        )
        complete = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE
        )
        draft = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED
        )

        call_command("load_dummy_highwind_results")

        for experiment in (live, complete):
            experiment.refresh_from_db()
            self.assertTrue(experiment.analysis_data)
            self.assertIsNotNone(experiment.analysis_last_updated)

        draft.refresh_from_db()
        self.assertIsNone(draft.analysis_data)

    def test_covers_every_cell_state(self):
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE
        )

        call_command("load_dummy_highwind_results")

        experiment = NimbusExperiment.objects.exclude(analysis_data=None).first()
        states = {
            comparison["state"]
            for metric in experiment.analysis_data["metrics"]
            for segment in metric["segments"]
            for window in segment["windows"]
            for comparison in window["comparisons"]
        }
        self.assertEqual(
            states,
            {"forming", "confident", "insufficient_data", "error", "not_started"},
        )

    def test_writes_both_cumulative_and_disjoint_windows(self):
        NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE
        )

        call_command("load_dummy_highwind_results")

        experiment = NimbusExperiment.objects.exclude(analysis_data=None).first()
        kinds = {
            window["window"]["kind"]
            for metric in experiment.analysis_data["metrics"]
            for segment in metric["segments"]
            for window in segment["windows"]
        }
        self.assertEqual(kinds, {"cumulative", "disjoint"})

    def test_skips_an_experiment_with_no_treatment_branch(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE
        )
        experiment.branches.exclude(id=experiment.reference_branch.id).delete()

        call_command("load_dummy_highwind_results")

        experiment.refresh_from_db()
        self.assertIsNone(experiment.analysis_data)

    def test_skips_an_experiment_with_no_reference_branch(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE_APPROVE
        )
        experiment.reference_branch = None
        experiment.save()

        call_command("load_dummy_highwind_results")

        experiment.refresh_from_db()
        self.assertIsNone(experiment.analysis_data)
