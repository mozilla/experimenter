import mock
from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from experimenter.experiments.admin.nimbus import NimbusExperimentAdminForm
from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tests.factories import (
    NimbusBranchFactory,
    NimbusExperimentFactory,
)
from experimenter.openidc.tests.factories import UserFactory


class TestNimbusExperimentAdminForm(TestCase):
    def test_form_required_fields(self):
        experiment = NimbusExperiment.objects.create(
            owner=UserFactory.create(),
            status=NimbusExperiment.Status.DRAFT,
            name="name",
            slug="slug",
            application=NimbusExperiment.Application.DESKTOP,
        )
        form = NimbusExperimentAdminForm(
            instance=experiment,
            data={
                "owner": experiment.owner,
                "status": experiment.status,
                "publish_status": experiment.publish_status,
                "name": experiment.name,
                "slug": experiment.slug,
                "proposed_duration": experiment.proposed_duration,
                "proposed_enrollment": experiment.proposed_enrollment,
                "population_percent": experiment.population_percent,
                "total_enrolled_clients": experiment.total_enrolled_clients,
                "application": experiment.application,
                "hypothesis": experiment.hypothesis,
            },
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_form_saves_outcomes(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            primary_outcomes=[],
            secondary_outcomes=[],
        )
        form = NimbusExperimentAdminForm(
            instance=experiment,
            data={
                "owner": experiment.owner,
                "status": experiment.status,
                "publish_status": experiment.publish_status,
                "name": experiment.name,
                "slug": experiment.slug,
                "proposed_duration": experiment.proposed_duration,
                "proposed_enrollment": experiment.proposed_enrollment,
                "population_percent": experiment.population_percent,
                "total_enrolled_clients": experiment.total_enrolled_clients,
                "application": experiment.application,
                "hypothesis": experiment.hypothesis,
                "primary_outcomes": "outcome1, outcome2",
                "secondary_outcomes": "outcome3, outcome4",
            },
        )
        self.assertTrue(form.is_valid(), form.errors)
        experiment = form.save()
        self.assertEqual(experiment.primary_outcomes, ["outcome1", "outcome2"])
        self.assertEqual(experiment.secondary_outcomes, ["outcome3", "outcome4"])

    def test_form_rejects_any_branch_if_no_experiment_provided(self):
        branch = NimbusBranchFactory.create()

        form = NimbusExperimentAdminForm(data={"reference_branch": branch.id})
        self.assertFalse(form.is_valid())
        self.assertIn("reference_branch", form.errors)

    def test_form_rejects_reference_branch_from_other_experiment(self):
        experiment = NimbusExperimentFactory.create()
        branch = NimbusBranchFactory.create()

        form = NimbusExperimentAdminForm(
            instance=experiment, data={"reference_branch": branch.id}
        )
        self.assertFalse(form.is_valid())
        self.assertIn("reference_branch", form.errors)

    def test_form_accepts_reference_branch_from_same_experiment(self):
        experiment = NimbusExperimentFactory.create()
        branch = NimbusBranchFactory.create(experiment=experiment)

        form = NimbusExperimentAdminForm(
            instance=experiment,
            data={"reference_branch": branch.id},
        )
        self.assertFalse(form.is_valid())
        self.assertNotIn("reference_branch", form.errors)


class TestNimbusExperimentAdmin(TestCase):
    def test_admin_form_renders(self):
        user = UserFactory.create(is_staff=True, is_superuser=True)
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE
        )
        response = self.client.get(
            reverse(
                "admin:experiments_nimbusexperiment_change",
                args=(experiment.pk,),
            ),
            **{settings.OPENIDC_EMAIL_HEADER: user.email}
        )
        self.assertEqual(response.status_code, 200)

    @mock.patch("experimenter.experiments.admin.nimbus.tasks.fetch_experiment_data")
    def test_admin_force_jetstream_fetch(self, mock_fetch_experiment_data):
        user = UserFactory.create(is_staff=True, is_superuser=True)
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE
        )
        response = self.client.post(
            reverse(
                "admin:experiments_nimbusexperiment_changelist",
            ),
            {"action": "force_fetch_jetstream_data", "_selected_action": [experiment.id]},
            follow=True,
            **{settings.OPENIDC_EMAIL_HEADER: user.email}
        )
        self.assertEqual(response.status_code, 200)
        mock_fetch_experiment_data.delay.assert_called_with(experiment.id)
