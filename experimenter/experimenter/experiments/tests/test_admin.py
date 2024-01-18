from decimal import Decimal
from unittest import mock

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from import_export import fields

from experimenter.experiments.admin import (
    DecimalWidget,
    NimbusBranchForeignKeyWidget,
    NimbusExperimentAdminForm,
    NimbusExperimentResource,
)
from experimenter.experiments.changelog_utils import NimbusBranchChangeLogSerializer
from experimenter.experiments.models import (
    NimbusBranch,
    NimbusChangeLog,
    NimbusExperiment,
    NimbusVersionedSchema,
)
from experimenter.experiments.tests.factories import (
    NimbusBranchFactory,
    NimbusChangeLogFactory,
    NimbusExperimentFactory,
)
from experimenter.openidc.tests.factories import UserFactory
from experimenter.settings import DEV_USER_EMAIL


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
            **{settings.OPENIDC_EMAIL_HEADER: user.email},
        )
        self.assertEqual(response.status_code, 200)

    @mock.patch("experimenter.experiments.admin.tasks.fetch_experiment_data")
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
            **{settings.OPENIDC_EMAIL_HEADER: user.email},
        )
        self.assertEqual(response.status_code, 200)
        mock_fetch_experiment_data.delay.assert_called_with(experiment.id)


class TestNimbusExperimentExport(TestCase):
    def test_decimal_render(self):
        dec_value = DecimalWidget.render(None, Decimal("90.00"))
        self.assertEqual(dec_value, "90.00")
        self.assertNotEqual(dec_value, 90)
        self.assertNotEqual(dec_value, "90.0")

    def test_nimbus_branch_get_queryset(self):
        reference_branch_slug = fields.Field(
            column_name="reference_branch_slug",
            widget=NimbusBranchForeignKeyWidget(NimbusBranch, "slug"),
        )
        experiment = NimbusExperimentFactory.create()
        experiment.id = None
        experiment.reference_branch = None
        test_row = {"slug": experiment.slug, "reference_branch_slug": "control"}

        reference_branch_slug.widget.get_queryset(value=None, row=test_row)

    def test_resource_get_diff_headers(self):
        resource = NimbusExperimentResource()
        headers = resource.get_diff_headers()
        self.assertNotIn("reference_branch_slug", headers)

    def test_resource_dehydrate(self):
        resource = NimbusExperimentResource()
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE
        )

        # test normal dehydrate conditions
        experiment.status_next = "Complete"
        experiment.conclusion_recommendation = "STOP"
        status_next = resource.dehydrate_status_next(experiment)
        conclusion_recommendation = resource.dehydrate_conclusion_recommendation(
            experiment
        )

        num_changes = len(resource.dehydrate_changes(experiment))
        num_branches = len(resource.dehydrate_branches(experiment))
        reference_branch_slug = resource.dehydrate_reference_branch_slug(experiment)

        self.assertGreaterEqual(num_changes, 1)
        self.assertEqual(num_branches, 2)
        self.assertEqual(reference_branch_slug, "control")
        self.assertEqual(status_next, "Complete")
        self.assertEqual(conclusion_recommendation, "STOP")

    def test_resource_dehydrate_none(self):
        resource = NimbusExperimentResource()
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE
        )

        # test None dehydrate conditions
        experiment.reference_branch = None
        experiment.status_next = ""
        experiment.conclusion_recommendation = ""

        none_slug = resource.dehydrate_reference_branch_slug(experiment)
        status_next = resource.dehydrate_status_next(experiment)
        conclusion_recommendation = resource.dehydrate_conclusion_recommendation(
            experiment
        )

        self.assertIsNone(none_slug)
        self.assertIsNone(status_next)
        self.assertIsNone(conclusion_recommendation)

    def test_before_import_row(self):
        resource = NimbusExperimentResource()

        test_row = {"owner": 9999}
        resource.before_import_row(row=test_row)
        owner_id = test_row.get("owner")
        dev_user = User.objects.get(email=DEV_USER_EMAIL)

        # user id=9999 should not exist in test DB
        self.assertNotEqual(owner_id, 9999)
        # should use the default dev user instead
        self.assertEqual(dev_user.id, owner_id)

    def test_after_import_row(self):
        resource = NimbusExperimentResource()
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE
        )
        experiment.reference_branch = None
        branches = [
            dict(NimbusBranchChangeLogSerializer(b).data)
            for b in experiment.branches.all()
        ]
        changes = []
        num_changes = 3
        for _ in range(num_changes):
            cl = NimbusChangeLogFactory.create(
                experiment=experiment, experiment_data={"some_old": "data"}
            )
            changes.append(
                {
                    "changed_on": cl.changed_on,
                    "old_status": cl.old_status,
                    "old_status_next": cl.old_status_next,
                    "old_publish_status": cl.old_publish_status,
                    "new_status": cl.new_status,
                    "new_status_next": cl.new_status_next,
                    "new_publish_status": cl.new_publish_status,
                    "message": cl.message,
                    "experiment_data": cl.experiment_data,
                    "published_dto_changed": cl.published_dto_changed,
                    "experiment": experiment,
                }
            )
        test_row = {
            "slug": experiment.slug,
            "reference_branch_slug": "control",
            "branches": branches,
            "changes": changes,
        }

        pre_changes = NimbusChangeLog.objects.filter(experiment=experiment)
        resource.after_import_row(row=test_row, row_result=None)
        post_branches = NimbusBranch.objects.filter(experiment=experiment)
        post_changes = NimbusChangeLog.objects.filter(experiment=experiment)
        post_experiment = NimbusExperiment.objects.get(slug=experiment.slug)

        self.assertEqual(post_experiment.reference_branch.slug, "control")
        self.assertEqual(len(branches), len(post_branches))
        self.assertEqual(len(post_branches), 2)

        self.assertGreaterEqual(len(post_changes), len(pre_changes))
        self.assertGreaterEqual(len(post_changes), num_changes)


class NimbusVersionedSchemaAdminTests(TestCase):
    def test_filter_application(self):
        user = UserFactory.create(is_staff=True, is_superuser=True)
        url = reverse("admin:experiments_nimbusversionedschema_changelist")

        response = self.client.get(url, **{settings.OPENIDC_EMAIL_HEADER: user.email})
        change_list = response.context["cl"]
        self.assertEqual(
            set(change_list.paginator.object_list),
            set(NimbusVersionedSchema.objects.all()),
        )

        response = self.client.get(
            f"{url}?application={NimbusExperiment.Application.DESKTOP}",
            **{settings.OPENIDC_EMAIL_HEADER: user.email},
        )
        change_list = response.context["cl"]
        self.assertEqual(len(change_list.paginator.object_list), 1)
        self.assertEqual(
            set(change_list.paginator.object_list),
            set(
                NimbusVersionedSchema.objects.filter(
                    feature_config__application=NimbusExperiment.Application.DESKTOP
                )
            ),
        )
