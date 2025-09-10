import datetime
import io
import json
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, TestCase
from django.urls import reverse
from parameterized import parameterized
from PIL import Image

from experimenter.base.tests.factories import (
    CountryFactory,
    LanguageFactory,
    LocaleFactory,
)
from experimenter.experiments.api.v6.serializers import NimbusExperimentSerializer
from experimenter.experiments.models import (
    NimbusBranchFeatureValue,
    NimbusExperiment,
    NimbusExperimentBranchThroughExcluded,
    NimbusExperimentBranchThroughRequired,
)
from experimenter.experiments.tests.factories import (
    NimbusBranchFactory,
    NimbusDocumentationLinkFactory,
    NimbusExperimentFactory,
    NimbusFeatureConfigFactory,
    NimbusVersionedSchemaFactory,
)
from experimenter.kinto.tasks import (
    nimbus_check_kinto_push_queue_by_collection,
    nimbus_synchronize_preview_experiments_in_kinto,
)
from experimenter.klaatu.tasks import klaatu_start_job
from experimenter.nimbus_ui.constants import NimbusUIConstants
from experimenter.nimbus_ui.forms import (
    ApproveEndEnrollmentForm,
    ApproveEndExperimentForm,
    ApproveUpdateRolloutForm,
    AudienceForm,
    BranchScreenshotCreateForm,
    BranchScreenshotDeleteForm,
    CancelEndEnrollmentForm,
    CancelEndExperimentForm,
    CancelUpdateRolloutForm,
    DocumentationLinkCreateForm,
    DocumentationLinkDeleteForm,
    DraftToPreviewForm,
    DraftToReviewForm,
    FeaturesForm,
    LiveToCompleteForm,
    LiveToEndEnrollmentForm,
    LiveToUpdateRolloutForm,
    MetricsForm,
    NimbusBranchCreateForm,
    NimbusBranchDeleteForm,
    NimbusBranchesForm,
    NimbusBranchFeatureValueForm,
    NimbusExperimentCreateForm,
    NimbusExperimentPromoteToRolloutForm,
    NimbusExperimentSidebarCloneForm,
    OverviewForm,
    PreviewToDraftForm,
    PreviewToReviewForm,
    QAStatusForm,
    ReviewToApproveForm,
    ReviewToDraftForm,
    SignoffForm,
    SubscribeForm,
    TakeawaysForm,
    ToggleArchiveForm,
    UnsubscribeForm,
)
from experimenter.openidc.tests.factories import UserFactory
from experimenter.outcomes import Outcomes
from experimenter.outcomes.tests import mock_valid_outcomes
from experimenter.projects.tests.factories import ProjectFactory
from experimenter.segments import Segments
from experimenter.segments.tests.mock_segments import mock_get_segments
from experimenter.targeting.constants import NimbusTargetingConfig


class RequestFormTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory.create(email="dev@example.com")
        request_factory = RequestFactory()
        self.request = request_factory.get(reverse("nimbus-ui-create"))
        self.request.user = self.user


class TestNimbusExperimentCreateForm(RequestFormTestCase):
    def test_valid_form_creates_experiment_with_changelog(self):
        data = {
            "owner": self.user,
            "name": "Test Experiment",
            "hypothesis": "test hypothesis",
            "application": NimbusExperiment.Application.DESKTOP,
        }
        form = NimbusExperimentCreateForm(data, request=self.request)
        self.assertTrue(form.is_valid(), form.errors)

        experiment = form.save()
        self.assertEqual(experiment.owner, self.user)
        self.assertEqual(experiment.name, "Test Experiment")
        self.assertEqual(experiment.slug, "test-experiment")
        self.assertEqual(experiment.hypothesis, "test hypothesis")
        self.assertEqual(experiment.application, NimbusExperiment.Application.DESKTOP)

        changelog = experiment.changes.get()
        self.assertEqual(changelog.changed_by, self.user)
        self.assertEqual(changelog.message, "dev@example.com created Test Experiment")

    def test_invalid_unsluggable_name(self):
        data = {
            "owner": self.user,
            "name": "$.",
            "hypothesis": "test hypothesis",
            "application": NimbusExperiment.Application.DESKTOP,
        }
        form = NimbusExperimentCreateForm(data, request=self.request)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["name"], [NimbusUIConstants.ERROR_NAME_INVALID])

    def test_invalid_duplicate_slug(self):
        NimbusExperimentFactory.create(slug="test-experiment")
        data = {
            "owner": self.user,
            "name": "Test Experiment",
            "hypothesis": "test hypothesis",
            "application": NimbusExperiment.Application.DESKTOP,
        }
        form = NimbusExperimentCreateForm(data, request=self.request)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["name"], [NimbusUIConstants.ERROR_SLUG_DUPLICATE])

    def test_invalid_with_placeholder_hypothesis(self):
        data = {
            "owner": self.user,
            "name": "$.",
            "hypothesis": NimbusUIConstants.HYPOTHESIS_PLACEHOLDER,
            "application": NimbusExperiment.Application.DESKTOP,
        }
        form = NimbusExperimentCreateForm(data, request=self.request)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["hypothesis"], [NimbusUIConstants.ERROR_HYPOTHESIS_PLACEHOLDER]
        )

    def test_form_creates_default_branches(self):
        data = {
            "owner": self.user,
            "name": "Branched Experiment",
            "hypothesis": "test hypothesis",
            "application": NimbusExperiment.Application.DESKTOP,
        }
        form = NimbusExperimentCreateForm(data, request=self.request)
        self.assertTrue(form.is_valid(), form.errors)

        experiment = form.save()

        self.assertEqual(experiment.branches.count(), 2)
        self.assertIsNotNone(experiment.reference_branch)
        self.assertEqual(experiment.reference_branch.name, "Control")

        branch_names = set(experiment.branches.values_list("name", flat=True))
        self.assertIn("Control", branch_names)
        self.assertIn("Treatment A", branch_names)


class TestNimbusExperimentSidebarCloneForm(RequestFormTestCase):
    def test_valid_clone_form_creates_experiment(self):
        parent_experiment = NimbusExperiment.objects.create(
            owner=self.user,
            name="Original Experiment",
            slug="original-experiment",
            application=NimbusExperiment.Application.DESKTOP,
        )

        data = {
            "owner": self.user,
            "name": "Cloned Experiment",
            "slug": "cloned-experiment",
        }
        form = NimbusExperimentSidebarCloneForm(
            data, instance=parent_experiment, request=self.request
        )
        changelog_message = form.get_changelog_message()
        self.assertEqual(
            changelog_message,
            f"{self.user} cloned this experiment from Original Experiment",
        )

        self.assertTrue(form.is_valid())

        cloned_experiment = form.save()

        self.assertEqual(cloned_experiment.owner, self.user)
        self.assertEqual(cloned_experiment.name, "Cloned Experiment")
        self.assertEqual(cloned_experiment.slug, "cloned-experiment")
        self.assertEqual(
            cloned_experiment.application, NimbusExperiment.Application.DESKTOP
        )

    def test_invalid_unsluggable_name(self):
        parent_experiment = NimbusExperiment.objects.create(
            owner=self.user,
            name="Original Experiment",
            slug="original-experiment",
            application=NimbusExperiment.Application.DESKTOP,
        )

        data = {
            "owner": self.user,
            "name": "$.",
            "slug": "",
        }
        form = NimbusExperimentSidebarCloneForm(
            data, instance=parent_experiment, request=self.request
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["name"], [NimbusUIConstants.ERROR_NAME_INVALID])

    def test_invalid_duplicate_slug(self):
        NimbusExperiment.objects.create(
            owner=self.user,
            name="Cloned Experiment",
            slug="cloned-experiment",
            application=NimbusExperiment.Application.DESKTOP,
        )

        parent_experiment = NimbusExperiment.objects.create(
            owner=self.user,
            name="Original Experiment",
            slug="original-experiment",
            application=NimbusExperiment.Application.DESKTOP,
        )

        data = {
            "owner": self.user,
            "name": "Cloned Experiment.",
            "slug": "cloned-experiment",
        }
        form = NimbusExperimentSidebarCloneForm(
            data, instance=parent_experiment, request=self.request
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["name"], [NimbusUIConstants.ERROR_NAME_MAPS_TO_EXISTING_SLUG]
        )


class TestNimbusExperimentPromoteToRolloutForm(RequestFormTestCase):
    def test_valid_clone_form_creates_experiment(self):
        parent_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            name="Original Experiment",
            slug="original-experiment",
        )

        data = {
            "owner": self.user,
            "name": "Cloned Experiment",
            "slug": "cloned-experiment",
            "branch_slug": "control",
        }
        form = NimbusExperimentPromoteToRolloutForm(
            data,
            instance=parent_experiment,
            request=self.request,
        )
        changelog_message = form.get_changelog_message()
        self.assertEqual(
            changelog_message,
            f"{self.user} cloned this experiment from Original Experiment",
        )

        self.assertTrue(form.is_valid())

        cloned_experiment = form.save()

        self.assertEqual(cloned_experiment.owner, self.user)
        self.assertEqual(cloned_experiment.name, "Cloned Experiment")
        self.assertEqual(cloned_experiment.slug, "cloned-experiment")
        self.assertTrue(cloned_experiment.is_rollout)
        self.assertEqual(
            cloned_experiment.application, NimbusExperiment.Application.DESKTOP
        )

    def test_invalid_unsluggable_name(self):
        parent_experiment = NimbusExperiment.objects.create(
            owner=self.user,
            name="Original Experiment",
            slug="original-experiment",
            application=NimbusExperiment.Application.DESKTOP,
        )

        data = {
            "owner": self.user,
            "name": "$.",
            "slug": "",
            "branch_slug": "control",
        }
        form = NimbusExperimentPromoteToRolloutForm(
            data,
            instance=parent_experiment,
            request=self.request,
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["name"], [NimbusUIConstants.ERROR_NAME_INVALID])

    def test_invalid_duplicate_slug(self):
        NimbusExperiment.objects.create(
            owner=self.user,
            name="Cloned Experiment",
            slug="cloned-experiment",
            application=NimbusExperiment.Application.DESKTOP,
        )

        parent_experiment = NimbusExperiment.objects.create(
            owner=self.user,
            name="Original Experiment",
            slug="original-experiment",
            application=NimbusExperiment.Application.DESKTOP,
        )

        data = {
            "owner": self.user,
            "name": "Cloned Experiment.",
            "slug": "cloned-experiment",
            "branch_slug": "control",
        }
        form = NimbusExperimentPromoteToRolloutForm(
            data,
            instance=parent_experiment,
            request=self.request,
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["name"], [NimbusUIConstants.ERROR_NAME_MAPS_TO_EXISTING_SLUG]
        )


class TestToggleArchiveForm(RequestFormTestCase):
    def test_toggle_archive(self):
        experiment = NimbusExperiment.objects.create(
            owner=self.user,
            name="Test Experiment",
            slug="test-experiment",
            is_archived=False,
        )

        data = {
            "owner": self.user,
        }

        form = ToggleArchiveForm(data, instance=experiment, request=self.request)
        self.assertTrue(form.is_valid())

        updated_experiment = form.save()

        self.assertTrue(updated_experiment.is_archived)

        changelog_message = form.get_changelog_message()

        self.assertEqual(
            changelog_message, f"{self.user} set the Is Archived Flag to True"
        )

    def test_toggle_unarchive(self):
        experiment = NimbusExperiment.objects.create(
            owner=self.user,
            name="Test Experiment",
            slug="test-experiment",
            is_archived=True,
        )

        data = {
            "owner": self.user,
        }

        form = ToggleArchiveForm(data, instance=experiment, request=self.request)
        self.assertTrue(form.is_valid())

        updated_experiment = form.save()

        self.assertFalse(updated_experiment.is_archived)

        changelog_message = form.get_changelog_message()

        self.assertEqual(
            changelog_message, f"{self.user} set the Is Archived Flag to False"
        )


class TestQAStatusForm(RequestFormTestCase):
    def test_form_updates_qa_fields_and_creates_changelog(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            qa_status=NimbusExperiment.QAStatus.NOT_SET,
            qa_comment="",
        )
        existing_changes = list(experiment.changes.values_list("id", flat=True))
        data = {
            "qa_status": NimbusExperiment.QAStatus.GREEN,
            "qa_comment": "tests passed",
        }
        form = QAStatusForm(data, request=self.request, instance=experiment)
        self.assertTrue(form.is_valid(), form.errors)

        experiment = form.save()
        self.assertEqual(experiment.qa_status, NimbusExperiment.QAStatus.GREEN)
        self.assertEqual(experiment.qa_comment, "tests passed")

        self.assertEqual(experiment.changes.count(), 2)
        changelog = experiment.changes.exclude(id__in=existing_changes).get()
        self.assertEqual(changelog.changed_by, self.user)
        self.assertEqual(
            changelog.message,
            "dev@example.com updated QA",
        )


class TestTakeawaysForm(RequestFormTestCase):
    def test_form_updates_takeaways_fields_and_creates_changelog(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            takeaways_qbr_learning=False,
            takeaways_metric_gain=False,
            takeaways_summary="",
            takeaways_gain_amount="",
            conclusion_recommendations={},
        )
        existing_changes = list(experiment.changes.values_list("id", flat=True))
        data = {
            "takeaways_qbr_learning": True,
            "takeaways_metric_gain": True,
            "takeaways_summary": "Updated summary.",
            "takeaways_gain_amount": "1%% gain in retention",
            "conclusion_recommendations": [
                NimbusExperiment.ConclusionRecommendation.CHANGE_COURSE,
                NimbusExperiment.ConclusionRecommendation.FOLLOWUP,
            ],
        }
        form = TakeawaysForm(data, request=self.request, instance=experiment)
        self.assertTrue(form.is_valid(), form.errors)

        experiment = form.save()
        self.assertEqual(experiment.takeaways_qbr_learning, True)
        self.assertEqual(experiment.takeaways_metric_gain, True)
        self.assertEqual(experiment.takeaways_summary, "Updated summary.")
        self.assertEqual(experiment.takeaways_gain_amount, "1%% gain in retention")
        self.assertEqual(
            experiment.conclusion_recommendations,
            [
                NimbusExperiment.ConclusionRecommendation.CHANGE_COURSE,
                NimbusExperiment.ConclusionRecommendation.FOLLOWUP,
            ],
        )

        self.assertEqual(experiment.changes.count(), 2)
        changelog = experiment.changes.exclude(id__in=existing_changes).get()
        self.assertEqual(changelog.changed_by, self.user)
        self.assertEqual(
            changelog.message,
            "dev@example.com updated takeaways",
        )


class TestSignoffForm(RequestFormTestCase):
    def test_signoff_form_valid(self):
        experiment = NimbusExperimentFactory.create(
            name="Test Experiment",
            owner=self.user,
            qa_signoff=False,
            vp_signoff=False,
            legal_signoff=False,
        )
        data = {
            "qa_signoff": True,
            "vp_signoff": True,
            "legal_signoff": False,
        }
        form = SignoffForm(data=data, instance=experiment, request=self.request)
        self.assertTrue(form.is_valid(), form.errors)

        experiment = form.save()
        self.assertTrue(experiment.qa_signoff)
        self.assertTrue(experiment.vp_signoff)
        self.assertFalse(experiment.legal_signoff)

    def test_signoff_form_saves_to_changelog(self):
        """Test that saving the form also creates an entry in the changelog."""
        experiment = NimbusExperimentFactory.create(
            name="Test Experiment",
            owner=self.user,
            qa_signoff=False,
            vp_signoff=False,
            legal_signoff=False,
        )
        data = {
            "qa_signoff": True,
            "vp_signoff": True,
            "legal_signoff": True,
        }
        form = SignoffForm(data=data, instance=experiment, request=self.request)
        self.assertTrue(form.is_valid())
        experiment = form.save()

        changelog = experiment.changes.get()
        self.assertEqual(changelog.changed_by, self.user)
        self.assertIn("dev@example.com updated sign off", changelog.message)


@mock_valid_outcomes
class TestMetricsForm(RequestFormTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Outcomes.clear_cache()
        Segments.clear_cache()

    def test_valid_form_saves_and_creates_chanelog(self):
        application = NimbusExperiment.Application.DESKTOP
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=application,
            primary_outcomes=[],
            secondary_outcomes=[],
            segments=[],
        )
        existing_changes = list(experiment.changes.values_list("id", flat=True))

        outcomes = Outcomes.by_application(application)
        segments = Segments.by_application(application, mock_get_segments())

        outcome1 = outcomes[0]
        outcome2 = outcomes[1]
        segment = segments[0]

        data = {
            "primary_outcomes": [outcome1.slug],
            "secondary_outcomes": [outcome2.slug],
            "segments": [segment.slug],
        }
        form = MetricsForm(data=data, instance=experiment, request=self.request)
        self.assertTrue(form.is_valid(), form.errors)

        experiment = form.save()
        self.assertEqual(experiment.primary_outcomes, [outcome1.slug])
        self.assertEqual(experiment.secondary_outcomes, [outcome2.slug])
        self.assertEqual(experiment.segments, [segment.slug])

        changelog = experiment.changes.exclude(id__in=existing_changes).get()
        self.assertEqual(changelog.changed_by, self.user)
        self.assertEqual(
            changelog.message,
            "dev@example.com updated metrics",
        )

    def test_invalid_form_with_wrong_application_outcomes_and_segments(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            primary_outcomes=[],
            secondary_outcomes=[],
            segments=[],
        )

        outcomes = Outcomes.by_application(NimbusExperiment.Application.FENIX)
        segments = Segments.by_application(
            NimbusExperiment.Application.FENIX, mock_get_segments()
        )

        outcome1 = outcomes[0]
        outcome2 = outcomes[1]
        segment = segments[0]

        data = {
            "primary_outcomes": [outcome1],
            "secondary_outcomes": [outcome2],
            "segments": [segment.slug],
        }
        form = MetricsForm(data=data, instance=experiment, request=self.request)
        self.assertFalse(form.is_valid(), form.errors)
        self.assertIn("primary_outcomes", form.errors)
        self.assertIn("secondary_outcomes", form.errors)
        self.assertIn("segments", form.errors)


class SubscriptionFormTests(RequestFormTestCase):
    def test_subscribe_form_adds_subscriber(self):
        experiment = NimbusExperimentFactory.create(
            name="Test Experiment",
            owner=self.user,
            qa_signoff=False,
            vp_signoff=False,
            legal_signoff=False,
        )
        form = SubscribeForm(instance=experiment, data={}, request=self.request)
        self.assertTrue(form.is_valid())
        form.save()
        self.assertIn(self.request.user, experiment.subscribers.all())
        changelog = experiment.changes.latest("changed_on")
        self.assertEqual(changelog.changed_by, self.user)
        self.assertIn("dev@example.com added subscriber", changelog.message)

    def test_unsubscribe_form_removes_subscriber(self):
        experiment = NimbusExperimentFactory.create(
            name="Test Experiment",
            owner=self.user,
            qa_signoff=False,
            vp_signoff=False,
            legal_signoff=False,
        )
        experiment.subscribers.add(self.request.user)
        form = UnsubscribeForm(instance=experiment, data={}, request=self.request)
        self.assertTrue(form.is_valid())
        form.save()
        self.assertNotIn(self.request.user, experiment.subscribers.all())
        changelog = experiment.changes.latest("changed_on")
        self.assertEqual(changelog.changed_by, self.user)
        self.assertIn("dev@example.com removed subscriber", changelog.message)


class TestLaunchForms(RequestFormTestCase):
    def setUp(self):
        super().setUp()

        self.mock_preview_task = patch.object(
            nimbus_synchronize_preview_experiments_in_kinto, "apply_async"
        ).start()
        self.mock_push_task = patch.object(
            nimbus_check_kinto_push_queue_by_collection, "apply_async"
        ).start()
        self.mock_allocate_bucket_range = patch.object(
            NimbusExperiment, "allocate_bucket_range"
        ).start()
        self.mock_klaatu_task = patch.object(klaatu_start_job, "delay").start()

        self.addCleanup(patch.stopall)

    def test_draft_to_preview_form(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
            status_next=None,
            publish_status=NimbusExperiment.PublishStatus.IDLE,
        )
        form = DraftToPreviewForm(data={}, instance=experiment, request=self.request)
        self.assertTrue(form.is_valid(), form.errors)

        experiment = form.save()
        self.assertEqual(experiment.status, NimbusExperiment.Status.PREVIEW)
        self.assertEqual(experiment.status_next, NimbusExperiment.Status.PREVIEW)
        self.assertEqual(experiment.publish_status, NimbusExperiment.PublishStatus.IDLE)
        self.mock_klaatu_task.assert_called_once_with(
            experiment=experiment, application=experiment.application
        )

        changelog = experiment.changes.latest("changed_on")
        self.assertEqual(changelog.changed_by, self.user)
        self.assertIn("launched experiment to Preview", changelog.message)
        self.mock_preview_task.assert_called_once_with(countdown=5)
        self.mock_allocate_bucket_range.assert_called_once()

    def test_draft_to_review_form(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
            status_next=None,
            publish_status=NimbusExperiment.PublishStatus.IDLE,
        )
        form = DraftToReviewForm(data={}, instance=experiment, request=self.request)
        self.assertTrue(form.is_valid(), form.errors)

        experiment = form.save()
        self.assertEqual(experiment.status, NimbusExperiment.Status.DRAFT)
        self.assertEqual(experiment.status_next, NimbusExperiment.Status.LIVE)
        self.assertEqual(experiment.publish_status, NimbusExperiment.PublishStatus.REVIEW)

        changelog = experiment.changes.latest("changed_on")
        self.assertEqual(changelog.changed_by, self.user)
        self.assertIn("requested launch without Preview", changelog.message)

    def test_preview_to_review_form(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.PREVIEW,
            status_next=NimbusExperiment.Status.PREVIEW,
            publish_status=NimbusExperiment.PublishStatus.IDLE,
        )
        experiment.published_dto = NimbusExperimentSerializer(experiment).data
        experiment.save()

        form = PreviewToReviewForm(data={}, instance=experiment, request=self.request)
        self.assertTrue(form.is_valid(), form.errors)

        experiment = form.save()
        self.assertEqual(experiment.status, NimbusExperiment.Status.DRAFT)
        self.assertEqual(experiment.status_next, NimbusExperiment.Status.LIVE)
        self.assertEqual(experiment.publish_status, NimbusExperiment.PublishStatus.REVIEW)
        self.assertEqual(experiment.published_dto, None)

        changelog = experiment.changes.latest("changed_on")
        self.assertEqual(changelog.changed_by, self.user)
        self.assertIn("requested launch from Preview", changelog.message)

    def test_preview_to_draft_form(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.PREVIEW,
            status_next=NimbusExperiment.Status.PREVIEW,
            publish_status=NimbusExperiment.PublishStatus.IDLE,
        )
        experiment.published_dto = NimbusExperimentSerializer(experiment).data
        experiment.save()

        form = PreviewToDraftForm(data={}, instance=experiment, request=self.request)
        self.assertTrue(form.is_valid(), form.errors)

        experiment = form.save()
        self.assertEqual(experiment.status, NimbusExperiment.Status.DRAFT)
        self.assertEqual(experiment.status_next, NimbusExperiment.Status.DRAFT)
        self.assertEqual(experiment.publish_status, NimbusExperiment.PublishStatus.IDLE)
        self.assertEqual(experiment.published_dto, None)

        changelog = experiment.changes.latest("changed_on")
        self.assertEqual(changelog.changed_by, self.user)
        self.assertIn("moved the experiment back to Draft", changelog.message)
        self.mock_preview_task.assert_called_once_with(countdown=5)

    def test_preview_to_draft_form_resets_published_dto_and_targeting(self):
        experiment = NimbusExperimentFactory.create(
            application=NimbusExperiment.Application.DESKTOP,
            status=NimbusExperiment.Status.PREVIEW,
            status_next=NimbusExperiment.Status.PREVIEW,
            publish_status=NimbusExperiment.PublishStatus.IDLE,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_116,
            channels=[NimbusExperiment.Channel.NIGHTLY],
        )

        # Publishing to the preview collection would set the published_dto field
        # to the value in Remote Settings. However, since we're not actually
        # publishing to Remote Settings, we need to fake it.
        experiment.published_dto = NimbusExperimentSerializer(experiment).data
        experiment.save()

        self.assertEqual(
            experiment.targeting,
            """(browserSettings.update.channel in ["nightly"]) && """
            """(version|versionCompare('116.!') >= 0)""",
        )

        form = PreviewToDraftForm(data={}, instance=experiment, request=self.request)
        self.assertTrue(form.is_valid(), form.errors)

        experiment = form.save()
        self.assertEqual(experiment.published_dto, None)

        experiment.firefox_min_version = NimbusExperiment.Version.FIREFOX_117
        experiment.channels = [NimbusExperiment.Channel.BETA]
        experiment.save()

        self.assertEqual(
            experiment.targeting,
            """(browserSettings.update.channel in ["beta"]) && """
            """(version|versionCompare('117.!') >= 0)""",
        )

    def test_review_to_draft_form_with_changelog_message(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
            status_next=NimbusExperiment.Status.LIVE,
            publish_status=NimbusExperiment.PublishStatus.REVIEW,
        )
        experiment.published_dto = NimbusExperimentSerializer(experiment).data
        experiment.save()

        form = ReviewToDraftForm(
            data={"changelog_message": "Needs further updates."},
            instance=experiment,
            request=self.request,
        )
        self.assertTrue(form.is_valid(), form.errors)

        experiment = form.save()
        self.assertEqual(experiment.status, NimbusExperiment.Status.DRAFT)
        self.assertEqual(experiment.status_next, NimbusExperiment.Status.DRAFT)
        self.assertEqual(experiment.publish_status, NimbusExperiment.PublishStatus.IDLE)
        self.assertEqual(experiment.published_dto, None)

        changelog = experiment.changes.latest("changed_on")
        self.assertEqual(changelog.changed_by, self.user)
        self.assertIn(
            "rejected the review with reason: Needs further updates.", changelog.message
        )

    def test_review_to_draft_form_with_cancel_message(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
            status_next=NimbusExperiment.Status.LIVE,
            publish_status=NimbusExperiment.PublishStatus.REVIEW,
        )
        experiment.published_dto = NimbusExperimentSerializer(experiment).data
        experiment.save()

        form = ReviewToDraftForm(
            data={"cancel_message": "Review was withdrawn by the user."},
            instance=experiment,
            request=self.request,
        )
        self.assertTrue(form.is_valid(), form.errors)

        experiment = form.save()
        self.assertEqual(experiment.status, NimbusExperiment.Status.DRAFT)
        self.assertEqual(experiment.status_next, NimbusExperiment.Status.DRAFT)
        self.assertEqual(experiment.publish_status, NimbusExperiment.PublishStatus.IDLE)
        self.assertEqual(experiment.published_dto, None)

        changelog = experiment.changes.latest("changed_on")
        self.assertEqual(changelog.changed_by, self.user)
        self.assertIn(f"{self.user} Review was withdrawn by the user.", changelog.message)

    def test_review_to_approve_form(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.DRAFT,
            status_next=NimbusExperiment.Status.LIVE,
            publish_status=NimbusExperiment.PublishStatus.REVIEW,
        )

        form = ReviewToApproveForm(data={}, instance=experiment, request=self.request)
        self.assertTrue(form.is_valid(), form.errors)

        experiment = form.save()
        self.assertEqual(experiment.status, NimbusExperiment.Status.DRAFT)
        self.assertEqual(experiment.status_next, NimbusExperiment.Status.LIVE)
        self.assertEqual(
            experiment.publish_status, NimbusExperiment.PublishStatus.APPROVED
        )

        changelog = experiment.changes.latest("changed_on")
        self.assertEqual(changelog.changed_by, self.user)
        self.assertIn(f"{self.user} approved the review.", changelog.message)
        self.mock_push_task.assert_called_once_with(
            countdown=5, args=[experiment.kinto_collection]
        )
        self.mock_allocate_bucket_range.assert_called_once()

    def test_live_to_end_enrollment_form(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE,
            status_next=None,
            publish_status=NimbusExperiment.PublishStatus.IDLE,
            is_paused=False,
        )

        form = LiveToEndEnrollmentForm(data={}, instance=experiment, request=self.request)
        self.assertTrue(form.is_valid(), form.errors)

        experiment = form.save()
        self.assertEqual(experiment.status, NimbusExperiment.Status.LIVE)
        self.assertEqual(experiment.status_next, NimbusExperiment.Status.LIVE)
        self.assertEqual(experiment.publish_status, NimbusExperiment.PublishStatus.REVIEW)
        self.assertTrue(experiment.is_paused)

        changelog = experiment.changes.latest("changed_on")
        self.assertEqual(changelog.changed_by, self.user)
        self.assertIn("requested review to end enrollment", changelog.message)

    def test_approve_end_enrollment_form(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE,
            status_next=NimbusExperiment.Status.LIVE,
            publish_status=NimbusExperiment.PublishStatus.REVIEW,
            is_paused=True,
        )

        form = ApproveEndEnrollmentForm(
            data={}, instance=experiment, request=self.request
        )
        self.assertTrue(form.is_valid(), form.errors)

        experiment = form.save()
        self.assertEqual(experiment.status, NimbusExperiment.Status.LIVE)
        self.assertEqual(experiment.status_next, NimbusExperiment.Status.LIVE)
        self.assertEqual(
            experiment.publish_status, NimbusExperiment.PublishStatus.APPROVED
        )
        self.assertTrue(experiment.is_paused)

        changelog = experiment.changes.latest("changed_on")
        self.assertEqual(changelog.changed_by, self.user)
        self.assertIn("approved the end enrollment request", changelog.message)
        self.mock_push_task.assert_called_once_with(
            countdown=5, args=[experiment.kinto_collection]
        )

    def test_live_to_complete_form(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE,
            status_next=None,
            publish_status=NimbusExperiment.PublishStatus.IDLE,
            is_paused=False,
        )

        form = LiveToCompleteForm(data={}, instance=experiment, request=self.request)
        self.assertTrue(form.is_valid(), form.errors)

        experiment = form.save()
        self.assertEqual(experiment.status, NimbusExperiment.Status.LIVE)
        self.assertEqual(experiment.status_next, NimbusExperiment.Status.COMPLETE)
        self.assertEqual(experiment.publish_status, NimbusExperiment.PublishStatus.REVIEW)

        changelog = experiment.changes.latest("changed_on")
        self.assertEqual(changelog.changed_by, self.user)
        self.assertIn("requested review to end experiment", changelog.message)

    def test_approve_end_experiment_form(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE,
            status_next=NimbusExperiment.Status.COMPLETE,
            publish_status=NimbusExperiment.PublishStatus.REVIEW,
            is_paused=True,
        )

        form = ApproveEndExperimentForm(
            data={}, instance=experiment, request=self.request
        )
        self.assertTrue(form.is_valid(), form.errors)

        experiment = form.save()
        self.assertEqual(experiment.status, NimbusExperiment.Status.LIVE)
        self.assertEqual(experiment.status_next, NimbusExperiment.Status.COMPLETE)
        self.assertEqual(
            experiment.publish_status, NimbusExperiment.PublishStatus.APPROVED
        )
        self.assertTrue(experiment.is_paused)

        changelog = experiment.changes.latest("changed_on")
        self.assertEqual(changelog.changed_by, self.user)
        self.assertIn("approved the end experiment request", changelog.message)
        self.mock_push_task.assert_called_once_with(
            countdown=5, args=[experiment.kinto_collection]
        )

    def test_reject_end_enrollment_request(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE,
            status_next=NimbusExperiment.Status.LIVE,
            publish_status=NimbusExperiment.PublishStatus.REVIEW,
            is_paused=True,
        )

        form = CancelEndEnrollmentForm(
            data={
                "changelog_message": "Enrollment should continue.",
            },
            instance=experiment,
            request=self.request,
        )
        self.assertTrue(form.is_valid(), form.errors)

        experiment = form.save()
        self.assertEqual(experiment.status, NimbusExperiment.Status.LIVE)
        self.assertEqual(experiment.status_next, None)
        self.assertEqual(experiment.publish_status, NimbusExperiment.PublishStatus.IDLE)
        self.assertFalse(experiment.is_paused)

        changelog = experiment.changes.latest("changed_on")
        self.assertEqual(changelog.changed_by, self.user)
        self.assertIn(
            "rejected the review with reason: Enrollment should continue.",
            changelog.message,
        )

    def test_cancel_end_enrollment_request(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE,
            status_next=NimbusExperiment.Status.LIVE,
            publish_status=NimbusExperiment.PublishStatus.REVIEW,
            is_paused=True,
        )

        form = CancelEndEnrollmentForm(
            data={
                "cancel_message": "Cancelled end enrollment request.",
            },
            instance=experiment,
            request=self.request,
        )
        self.assertTrue(form.is_valid(), form.errors)

        experiment = form.save()
        self.assertEqual(experiment.status, NimbusExperiment.Status.LIVE)
        self.assertEqual(experiment.status_next, None)
        self.assertEqual(experiment.publish_status, NimbusExperiment.PublishStatus.IDLE)
        self.assertFalse(experiment.is_paused)

        changelog = experiment.changes.latest("changed_on")
        self.assertEqual(changelog.changed_by, self.user)
        self.assertIn("Cancelled end enrollment request.", changelog.message)

    def test_reject_end_experiment_request(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE,
            status_next=NimbusExperiment.Status.COMPLETE,
            publish_status=NimbusExperiment.PublishStatus.REVIEW,
            is_paused=True,
        )

        form = CancelEndExperimentForm(
            data={
                "changelog_message": "Experiment should continue.",
            },
            instance=experiment,
            request=self.request,
        )
        self.assertTrue(form.is_valid(), form.errors)

        experiment = form.save()
        self.assertEqual(experiment.status, NimbusExperiment.Status.LIVE)
        self.assertEqual(experiment.status_next, None)
        self.assertEqual(experiment.publish_status, NimbusExperiment.PublishStatus.IDLE)
        self.assertTrue(experiment.is_paused)

        changelog = experiment.changes.latest("changed_on")
        self.assertEqual(changelog.changed_by, self.user)
        self.assertIn(
            "rejected the review with reason: Experiment should continue.",
            changelog.message,
        )

    def test_cancel_end_experiment_request(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE,
            status_next=NimbusExperiment.Status.COMPLETE,
            publish_status=NimbusExperiment.PublishStatus.REVIEW,
            is_paused=True,
        )

        form = CancelEndExperimentForm(
            data={
                "cancel_message": "Cancelled end experiment request.",
            },
            instance=experiment,
            request=self.request,
        )
        self.assertTrue(form.is_valid(), form.errors)

        experiment = form.save()
        self.assertEqual(experiment.status, NimbusExperiment.Status.LIVE)
        self.assertEqual(experiment.status_next, None)
        self.assertEqual(experiment.publish_status, NimbusExperiment.PublishStatus.IDLE)
        self.assertTrue(experiment.is_paused)

        changelog = experiment.changes.latest("changed_on")
        self.assertEqual(changelog.changed_by, self.user)
        self.assertIn("Cancelled end experiment request.", changelog.message)

    def test_live_to_update_rollout_form(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE,
            status_next=None,
            publish_status=NimbusExperiment.PublishStatus.IDLE,
            is_paused=False,
            is_rollout=True,
        )

        form = LiveToUpdateRolloutForm(data={}, instance=experiment, request=self.request)
        self.assertTrue(form.is_valid(), form.errors)

        experiment = form.save()
        self.assertEqual(experiment.status_next, NimbusExperiment.Status.LIVE)
        self.assertEqual(experiment.publish_status, NimbusExperiment.PublishStatus.REVIEW)

        changelog = experiment.changes.latest("changed_on")
        self.assertIn("requested review to update Audience", changelog.message)

    def test_cancel_update_rollout_form_with_rejection_reason(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE,
            status_next=NimbusExperiment.Status.LIVE,
            publish_status=NimbusExperiment.PublishStatus.REVIEW,
            is_rollout=True,
        )

        form = CancelUpdateRolloutForm(
            data={"changelog_message": "Audience update not valid."},
            instance=experiment,
            request=self.request,
        )
        self.assertTrue(form.is_valid(), form.errors)

        experiment = form.save()
        self.assertEqual(experiment.status_next, None)
        self.assertEqual(experiment.publish_status, NimbusExperiment.PublishStatus.IDLE)

        changelog = experiment.changes.latest("changed_on")
        self.assertIn(
            "rejected the update review with reason: Audience update not valid.",
            changelog.message,
        )

    def test_cancel_update_rollout_form_with_cancel_message(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE,
            status_next=NimbusExperiment.Status.LIVE,
            publish_status=NimbusExperiment.PublishStatus.REVIEW,
            is_rollout=True,
        )

        form = CancelUpdateRolloutForm(
            data={"cancel_message": "Cancelled update rollout."},
            instance=experiment,
            request=self.request,
        )
        self.assertTrue(form.is_valid(), form.errors)

        experiment = form.save()
        self.assertEqual(experiment.status_next, None)
        self.assertEqual(experiment.publish_status, NimbusExperiment.PublishStatus.IDLE)

        changelog = experiment.changes.latest("changed_on")
        self.assertIn("Cancelled update rollout.", changelog.message)

    def test_approve_update_rollout_form(self):
        experiment = NimbusExperimentFactory.create(
            status=NimbusExperiment.Status.LIVE,
            status_next=NimbusExperiment.Status.LIVE,
            publish_status=NimbusExperiment.PublishStatus.REVIEW,
            is_rollout=True,
        )

        form = ApproveUpdateRolloutForm(
            data={}, instance=experiment, request=self.request
        )
        self.assertTrue(form.is_valid(), form.errors)

        experiment = form.save()
        self.assertEqual(experiment.status_next, NimbusExperiment.Status.LIVE)
        self.assertEqual(
            experiment.publish_status, NimbusExperiment.PublishStatus.APPROVED
        )

        changelog = experiment.changes.latest("changed_on")
        self.assertIn("approved the update review request", changelog.message)
        self.mock_push_task.assert_called_once_with(
            countdown=5, args=[experiment.kinto_collection]
        )
        self.mock_preview_task.assert_called_once_with(countdown=5)
        self.mock_allocate_bucket_range.assert_called_once()


class TestOverviewForm(RequestFormTestCase):
    def test_valid_form_saves(self):
        project = ProjectFactory.create()
        documentation_link = NimbusDocumentationLinkFactory.create()
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            documentation_links=[documentation_link],
        )

        form = OverviewForm(
            instance=experiment,
            data={
                "name": "new name",
                "hypothesis": "new hypothesis",
                "risk_brand": True,
                "risk_message": True,
                "projects": [project.id],
                "public_description": "new description",
                "risk_revenue": True,
                "risk_partner_related": True,
                # Management form data for the inline formset
                "documentation_links-TOTAL_FORMS": "1",
                "documentation_links-INITIAL_FORMS": "1",
                "documentation_links-0-id": documentation_link.id,
                "documentation_links-0-title": (
                    NimbusExperiment.DocumentationLink.DESIGN_DOC.value
                ),
                "documentation_links-0-link": "https://www.example.com",
            },
            request=self.request,
        )

        self.assertTrue(form.is_valid(), form.errors)

        experiment = form.save()

        self.assertEqual(experiment.name, "new name")
        self.assertEqual(experiment.hypothesis, "new hypothesis")
        self.assertTrue(experiment.risk_brand)
        self.assertTrue(experiment.risk_message)
        self.assertEqual(list(experiment.projects.all()), [project])
        self.assertEqual(experiment.public_description, "new description")
        self.assertTrue(experiment.risk_revenue)
        self.assertTrue(experiment.risk_partner_related)

        documentation_link = experiment.documentation_links.all().get()
        self.assertEqual(
            documentation_link.title, NimbusExperiment.DocumentationLink.DESIGN_DOC
        )
        self.assertEqual(documentation_link.link, "https://www.example.com")

    def test_name_field_is_required(self):
        project = ProjectFactory.create()
        documentation_link = NimbusDocumentationLinkFactory.create()

        form_data = {
            "name": "",
            "hypothesis": "new hypothesis",
            "risk_brand": True,
            "risk_message": True,
            "projects": [project.id],
            "public_description": "new description",
            "risk_revenue": True,
            "risk_partner_related": True,
            "documentation_links-TOTAL_FORMS": "1",
            "documentation_links-INITIAL_FORMS": "1",
            "documentation_links-0-id": documentation_link.id,
            "documentation_links-0-title": (
                NimbusExperiment.DocumentationLink.DESIGN_DOC.value
            ),
            "documentation_links-0-link": "https://www.example.com",
        }

        form = OverviewForm(data=form_data)

        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)


class TestDocumentationLinkCreateForm(RequestFormTestCase):
    def test_valid_form_adds_documentation_link(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            documentation_links=[],
        )

        form = DocumentationLinkCreateForm(
            instance=experiment,
            data={
                "name": "new name",
                "hypothesis": "new hypothesis",
                "risk_brand": True,
                "risk_message": True,
                "projects": [],
                "public_description": "new description",
                "risk_revenue": True,
                "risk_partner_related": True,
                # Management form data for the inline formset
                "documentation_links-TOTAL_FORMS": "0",
                "documentation_links-INITIAL_FORMS": "0",
            },
            request=self.request,
        )

        self.assertTrue(form.is_valid())

        experiment = form.save()

        self.assertEqual(experiment.documentation_links.all().count(), 1)


class TestDocumentationLinkDeleteForm(RequestFormTestCase):
    def test_valid_form_deletes_documentation_link(self):
        documentation_link = NimbusDocumentationLinkFactory.create()
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            documentation_links=[documentation_link],
        )

        form = DocumentationLinkDeleteForm(
            instance=experiment,
            data={
                "name": "new name",
                "hypothesis": "new hypothesis",
                "risk_brand": True,
                "risk_message": True,
                "projects": [],
                "public_description": "new description",
                "risk_revenue": True,
                "risk_partner_related": True,
                # Management form data for the inline formset
                "documentation_links-TOTAL_FORMS": "1",
                "documentation_links-INITIAL_FORMS": "1",
                "documentation_links-0-id": documentation_link.id,
                "documentation_links-0-title": (
                    NimbusExperiment.DocumentationLink.DESIGN_DOC.value
                ),
                "documentation_links-0-link": "https://www.example.com",
                "link_id": documentation_link.id,
            },
            request=self.request,
        )

        self.assertTrue(form.is_valid())

        experiment = form.save()

        self.assertEqual(experiment.documentation_links.all().count(), 0)


class TestAudienceForm(RequestFormTestCase):
    def test_valid_form_saves_desktop(self):
        country = CountryFactory.create()
        locale = LocaleFactory.create()
        language = LanguageFactory.create()
        excluded = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
        )
        required = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
        )
        experiment = NimbusExperimentFactory.create(
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            application=NimbusExperiment.Application.DESKTOP,
            firefox_min_version=NimbusExperiment.Version.NO_VERSION,
            population_percent=0.0,
            proposed_duration=0,
            proposed_enrollment=0,
            proposed_release_date=None,
            total_enrolled_clients=0,
            is_sticky=False,
            countries=[],
            locales=[],
            languages=[],
        )

        form = AudienceForm(
            instance=experiment,
            data={
                "changelog_message": "test changelog message",
                "channels": [
                    NimbusExperiment.Channel.NIGHTLY,
                    NimbusExperiment.Channel.BETA,
                ],
                "countries": [country.id],
                "excluded_experiments_branches": [f"{excluded.slug}:None"],
                "firefox_max_version": NimbusExperiment.Version.FIREFOX_84,
                "firefox_min_version": NimbusExperiment.Version.FIREFOX_83,
                "is_sticky": True,
                "languages": [language.id],
                "locales": [locale.id],
                "population_percent": 10,
                "proposed_duration": 120,
                "proposed_enrollment": 42,
                "required_experiments_branches": [f"{required.slug}:None"],
                "targeting_config_slug": (NimbusExperiment.TargetingConfig.FIRST_RUN),
                "total_enrolled_clients": 100,
            },
            request=self.request,
        )

        self.assertEqual(experiment.changes.count(), 0)
        self.assertTrue(form.is_valid(), form.errors)
        experiment = form.save()

        self.assertEqual(experiment.changes.count(), 1)
        self.assertEqual(
            set(experiment.channels),
            {NimbusExperiment.Channel.NIGHTLY, NimbusExperiment.Channel.BETA},
        )
        self.assertEqual(
            experiment.firefox_min_version, NimbusExperiment.Version.FIREFOX_83
        )
        self.assertEqual(
            experiment.firefox_max_version, NimbusExperiment.Version.FIREFOX_84
        )
        self.assertEqual(experiment.population_percent, 10)
        self.assertEqual(experiment.proposed_duration, 120)
        self.assertEqual(experiment.proposed_enrollment, 42)
        self.assertEqual(
            experiment.targeting_config_slug,
            NimbusExperiment.TargetingConfig.FIRST_RUN,
        )
        self.assertEqual(experiment.total_enrolled_clients, 100)
        self.assertEqual(list(experiment.countries.all()), [country])
        self.assertEqual(list(experiment.locales.all()), [locale])
        self.assertEqual(list(experiment.languages.all()), [language])
        self.assertTrue(experiment.is_sticky)
        self.assertEqual(experiment.excluded_experiments.get(), excluded)
        self.assertTrue(
            NimbusExperimentBranchThroughExcluded.objects.filter(
                parent_experiment=experiment, child_experiment=excluded, branch_slug=None
            ).exists()
        )
        self.assertEqual(experiment.required_experiments.get(), required)
        self.assertTrue(
            NimbusExperimentBranchThroughRequired.objects.filter(
                parent_experiment=experiment, child_experiment=required, branch_slug=None
            ).exists()
        )

    @parameterized.expand(
        [
            (application,)
            for application in NimbusExperiment.Application
            if application != NimbusExperiment.Application.DESKTOP
        ]
    )
    def test_valid_form_saves_non_desktop(self, application):
        country = CountryFactory.create()
        locale = LocaleFactory.create()
        language = LanguageFactory.create()
        excluded = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=application,
        )
        required = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=application,
        )
        experiment = NimbusExperimentFactory.create(
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            application=application,
            firefox_min_version=NimbusExperiment.Version.NO_VERSION,
            targeting_config_slug=NimbusExperiment.TargetingConfig.NO_TARGETING,
            population_percent=0.0,
            proposed_duration=0,
            proposed_enrollment=0,
            proposed_release_date=None,
            total_enrolled_clients=0,
            is_sticky=False,
            countries=[],
            locales=[],
            languages=[],
        )

        targeting_config_slugs = [
            targeting.slug
            for targeting in NimbusTargetingConfig.targeting_configs
            if application.name in targeting.application_choice_names
        ]

        new_targeting_config_slug = NimbusExperiment.TargetingConfig.NO_TARGETING
        if targeting_config_slugs:
            new_targeting_config_slug = targeting_config_slugs[0]

        new_channel = next(iter(experiment.application_config.channel_app_id.keys()))

        form = AudienceForm(
            instance=experiment,
            data={
                "changelog_message": "test changelog message",
                "channel": new_channel,
                "countries": [country.id],
                "excluded_experiments_branches": [f"{excluded.slug}:None"],
                "firefox_max_version": NimbusExperiment.Version.FIREFOX_84,
                "firefox_min_version": NimbusExperiment.Version.FIREFOX_83,
                "is_sticky": True,
                "languages": [language.id],
                "locales": [locale.id],
                "population_percent": 10,
                "proposed_duration": 120,
                "proposed_enrollment": 42,
                "required_experiments_branches": [f"{required.slug}:None"],
                "targeting_config_slug": new_targeting_config_slug,
                "total_enrolled_clients": 100,
            },
            request=self.request,
        )

        self.assertEqual(experiment.changes.count(), 0)
        self.assertTrue(form.is_valid(), form.errors)
        experiment = form.save()

        self.assertEqual(experiment.changes.count(), 1)
        self.assertEqual(experiment.channel, new_channel)
        self.assertEqual(
            experiment.firefox_min_version, NimbusExperiment.Version.FIREFOX_83
        )
        self.assertEqual(
            experiment.firefox_max_version, NimbusExperiment.Version.FIREFOX_84
        )
        self.assertEqual(experiment.population_percent, 10)
        self.assertEqual(experiment.proposed_duration, 120)
        self.assertEqual(experiment.proposed_enrollment, 42)
        self.assertEqual(
            experiment.targeting_config_slug,
            new_targeting_config_slug,
        )
        self.assertEqual(experiment.total_enrolled_clients, 100)
        self.assertEqual(list(experiment.countries.all()), [country])
        self.assertEqual(list(experiment.locales.all()), [locale])
        self.assertEqual(list(experiment.languages.all()), [language])
        self.assertTrue(experiment.is_sticky)
        self.assertEqual(experiment.excluded_experiments.get(), excluded)
        self.assertTrue(
            NimbusExperimentBranchThroughExcluded.objects.filter(
                parent_experiment=experiment, child_experiment=excluded, branch_slug=None
            ).exists()
        )
        self.assertEqual(experiment.required_experiments.get(), required)
        self.assertTrue(
            NimbusExperimentBranchThroughRequired.objects.filter(
                parent_experiment=experiment, child_experiment=required, branch_slug=None
            ).exists()
        )

    def test_mobile_first_run_saves(self):
        experiment = NimbusExperimentFactory.create(
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            application=NimbusExperiment.Application.DESKTOP,
            firefox_min_version=NimbusExperiment.Version.NO_VERSION,
            population_percent=0.0,
            proposed_duration=0,
            proposed_enrollment=0,
            proposed_release_date=None,
            total_enrolled_clients=0,
            is_sticky=False,
            is_first_run=False,
            countries=[],
            locales=[],
            languages=[],
        )

        form = AudienceForm(
            instance=experiment,
            data={
                "changelog_message": "test changelog message",
                "channel": NimbusExperiment.Channel.BETA,
                "countries": [],
                "excluded_experiments_branches": [],
                "firefox_max_version": NimbusExperiment.Version.FIREFOX_84,
                "firefox_min_version": NimbusExperiment.Version.FIREFOX_83,
                "is_sticky": True,
                "is_first_run": True,
                "languages": [],
                "locales": [],
                "population_percent": 10,
                "proposed_duration": 120,
                "proposed_enrollment": 42,
                "proposed_release_date": "2023-01-01",
                "required_experiments_branches": [],
                "targeting_config_slug": (NimbusExperiment.TargetingConfig.FIRST_RUN),
                "total_enrolled_clients": 100,
            },
            request=self.request,
        )

        self.assertTrue(form.is_valid(), form.errors)
        experiment = form.save()

        self.assertTrue(experiment.is_first_run)
        self.assertEqual(experiment.proposed_release_date, datetime.date(2023, 1, 1))

    def test_archived_required_or_excluded_is_invalid(self):
        country = CountryFactory.create()
        locale = LocaleFactory.create()
        language = LanguageFactory.create()
        excluded = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            name="archived-excluded",
            application=NimbusExperiment.Application.DESKTOP,
            is_archived=True,
        )
        required = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            name="archived-required",
            application=NimbusExperiment.Application.DESKTOP,
            is_archived=True,
        )
        experiment = NimbusExperimentFactory.create(
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            application=NimbusExperiment.Application.DESKTOP,
            firefox_min_version=NimbusExperiment.Version.NO_VERSION,
            population_percent=0.0,
            proposed_duration=0,
            proposed_enrollment=0,
            proposed_release_date=None,
            total_enrolled_clients=0,
            is_sticky=False,
            countries=[],
            locales=[],
            languages=[],
        )

        form = AudienceForm(
            instance=experiment,
            data={
                "changelog_message": "test changelog message",
                "channel": NimbusExperiment.Channel.BETA,
                "countries": [country.id],
                "excluded_experiments_branches": [f"{excluded.slug}:None"],
                "firefox_max_version": NimbusExperiment.Version.FIREFOX_84,
                "firefox_min_version": NimbusExperiment.Version.FIREFOX_83,
                "is_sticky": True,
                "languages": [language.id],
                "locales": [locale.id],
                "population_percent": 10,
                "proposed_duration": 120,
                "proposed_enrollment": 42,
                "required_experiments_branches": [f"{required.slug}:None"],
                "targeting_config_slug": (NimbusExperiment.TargetingConfig.FIRST_RUN),
                "total_enrolled_clients": 100,
            },
            request=self.request,
        )

        self.assertFalse(form.is_valid(), form.errors)
        self.assertIn("excluded_experiments_branches", form.errors)
        self.assertIn("required_experiments_branches", form.errors)

    def test_check_rollout_dirty_sets_flag(self):
        experiment = NimbusExperimentFactory.create(
            is_rollout=True,
            status=NimbusExperiment.Status.LIVE,
            status_next=None,
            is_paused=False,
            publish_status=NimbusExperiment.PublishStatus.IDLE,
            population_percent=5,
            application=NimbusExperiment.Application.DESKTOP,
            channels=[NimbusExperiment.Channel.BETA],
        )

        form = AudienceForm(
            instance=experiment,
            data={
                "changelog_message": "updating population",
                "channel": NimbusExperiment.Channel.BETA,
                "countries": [],
                "excluded_experiments_branches": [],
                "firefox_max_version": NimbusExperiment.Version.FIREFOX_84,
                "firefox_min_version": NimbusExperiment.Version.FIREFOX_83,
                "is_sticky": False,
                "languages": [],
                "locales": [],
                "population_percent": 10,
                "proposed_duration": 0,
                "proposed_enrollment": 0,
                "required_experiments_branches": [],
                "targeting_config_slug": NimbusExperiment.TargetingConfig.NO_TARGETING,
                "total_enrolled_clients": 0,
            },
            request=self.request,
        )

        self.assertTrue(form.is_valid(), form.errors)
        updated_experiment = form.save()
        updated_experiment.refresh_from_db()

        self.assertTrue(updated_experiment.is_rollout_dirty)

    def test_fields_are_disabled_in_live_rollout(self):
        experiment = NimbusExperimentFactory.create(
            is_rollout=True,
            status=NimbusExperiment.Status.LIVE,
            status_next=None,
            is_paused=False,
            publish_status=NimbusExperiment.PublishStatus.IDLE,
            population_percent=5,
            application=NimbusExperiment.Application.DESKTOP,
            channels=[NimbusExperiment.Channel.BETA],
        )

        form = AudienceForm(instance=experiment, request=self.request)

        for field_name, field in form.fields.items():
            if field_name == "population_percent":
                self.assertFalse(field.disabled, f"{field_name} should be editable")
            else:
                self.assertTrue(field.disabled, f"{field_name} should be disabled")

    @parameterized.expand(
        [(application,) for application in NimbusExperiment.Application]
    )
    def test_targeting_config_choices_filtered_by_application(self, application):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED, application=application
        )

        form = AudienceForm(instance=experiment, request=self.request)

        actual_slugs = {slug for slug, _ in form.fields["targeting_config_slug"].choices}

        expected_slugs = {
            targeting.slug
            for targeting in NimbusTargetingConfig.targeting_configs
            if application.name in targeting.application_choice_names
        }

        self.assertEqual(
            actual_slugs,
            expected_slugs,
            msg=(
                f"Targeting config slugs did not match for application: "
                f"{application.name}"
            ),
        )

    def test_channels_choices_filtered_by_application(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
        )

        form = AudienceForm(instance=experiment, request=self.request)

        actual_channels = set(form.fields["channels"].choices)
        expected_channels = {
            (channel.value, channel.label)
            for channel in NimbusExperiment.Channel
            if channel in experiment.application_config.channel_app_id
            and channel.value != NimbusExperiment.Channel.NO_CHANNEL
        }

        self.assertEqual(
            actual_channels,
            expected_channels,
            msg="Channel choices did not match for desktop",
        )


class TestNimbusBranchesForm(RequestFormTestCase):
    def test_branches_form_saves_branches(self):
        application = NimbusExperiment.Application.DESKTOP
        feature_config1 = NimbusFeatureConfigFactory.create(application=application)
        feature_config2 = NimbusFeatureConfigFactory.create(application=application)
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=application,
            feature_configs=[feature_config1, feature_config2],
            equal_branch_ratio=False,
            is_localized=False,
            is_rollout=False,
            localizations=None,
            prevent_pref_conflicts=False,
            warn_feature_schema=False,
        )
        experiment.branches.all().delete()
        experiment.changes.all().delete()

        reference_branch = NimbusBranchFactory.create(experiment=experiment, ratio=1)
        treatment_branch = NimbusBranchFactory.create(experiment=experiment, ratio=1)
        experiment.reference_branch = reference_branch
        experiment.save()

        reference_branch_feature_config1_value = reference_branch.feature_values.filter(
            feature_config=feature_config1
        ).get()
        reference_branch_feature_config2_value = reference_branch.feature_values.filter(
            feature_config=feature_config2
        ).get()
        treatment_branch_feature_config1_value = treatment_branch.feature_values.filter(
            feature_config=feature_config1
        ).get()
        treatment_branch_feature_config2_value = treatment_branch.feature_values.filter(
            feature_config=feature_config2
        ).get()

        reference_screenshot = reference_branch.screenshots.first()
        treatment_screenshot = treatment_branch.screenshots.first()

        # Create a valid in-memory PNG image
        image_bytes = io.BytesIO()
        image = Image.new("RGB", (10, 10), color="red")
        image.save(image_bytes, format="PNG")
        image_bytes.seek(0)
        dummy_image = SimpleUploadedFile(
            "test.png", image_bytes.read(), content_type="image/png"
        )

        form = NimbusBranchesForm(
            instance=experiment,
            data={
                "feature_configs": [feature_config1.id, feature_config2.id],
                "equal_branch_ratio": False,
                "is_rollout": False,
                "prevent_pref_conflicts": True,
                "warn_feature_schema": True,
                "branches-TOTAL_FORMS": "2",
                "branches-INITIAL_FORMS": "2",
                "branches-MIN_NUM_FORMS": "0",
                "branches-MAX_NUM_FORMS": "1000",
                "branches-0-id": reference_branch.id,
                "branches-0-name": "Control",
                "branches-0-description": "Control Description",
                "branches-0-ratio": 2,
                "branches-0-feature-value-TOTAL_FORMS": "2",
                "branches-0-feature-value-INITIAL_FORMS": "2",
                "branches-0-feature-value-MIN_NUM_FORMS": "0",
                "branches-0-feature-value-MAX_NUM_FORMS": "1000",
                "branches-0-feature-value-0-id": (
                    reference_branch_feature_config1_value.id
                ),
                "branches-0-feature-value-0-value": json.dumps(
                    {"control-feature1-key": "control-feature-1-value"}
                ),
                "branches-0-feature-value-1-id": (
                    reference_branch_feature_config2_value.id
                ),
                "branches-0-feature-value-1-value": json.dumps(
                    {"control-feature-2-key": "control-feature-2-value"}
                ),
                "branches-0-screenshots-TOTAL_FORMS": "1",
                "branches-0-screenshots-INITIAL_FORMS": "1",
                "branches-0-screenshots-MIN_NUM_FORMS": "0",
                "branches-0-screenshots-MAX_NUM_FORMS": "1000",
                "branches-0-screenshots-0-id": reference_screenshot.id,
                "branches-0-screenshots-0-description": "Updated control screenshot",
                "branches-0-screenshots-0-image": dummy_image,
                "branches-1-id": treatment_branch.id,
                "branches-1-name": "Treatment",
                "branches-1-description": "Treatment Description",
                "branches-1-ratio": 3,
                "branches-1-feature-value-TOTAL_FORMS": "2",
                "branches-1-feature-value-INITIAL_FORMS": "2",
                "branches-1-feature-value-MIN_NUM_FORMS": "0",
                "branches-1-feature-value-MAX_NUM_FORMS": "1000",
                "branches-1-feature-value-0-id": (
                    treatment_branch_feature_config1_value.id
                ),
                "branches-1-feature-value-0-value": json.dumps(
                    {"treatment-feature-1-key": "treatment-feature-1-value"}
                ),
                "branches-1-feature-value-1-id": (
                    treatment_branch_feature_config2_value.id
                ),
                "branches-1-feature-value-1-value": json.dumps(
                    {"treatment-feature-2-key": "treatment-feature-2-value"}
                ),
                "branches-1-screenshots-TOTAL_FORMS": "1",
                "branches-1-screenshots-INITIAL_FORMS": "1",
                "branches-1-screenshots-MIN_NUM_FORMS": "0",
                "branches-1-screenshots-MAX_NUM_FORMS": "1000",
                "branches-1-screenshots-0-id": treatment_screenshot.id,
                "branches-1-screenshots-0-description": "Updated treatment screenshot",
                "branches-1-screenshots-0-image": dummy_image,
                "is_localized": True,
                "localizations": json.dumps({"localization-key": "localization-value"}),
            },
            files={
                "branches-0-screenshots-0-image": dummy_image,
                "branches-1-screenshots-0-image": dummy_image,
            },
            request=self.request,
        )

        self.assertTrue(form.is_valid(), form.errors)

        form.save()
        experiment = NimbusExperiment.objects.get(id=experiment.id)

        self.assertEqual(
            set(experiment.feature_configs.all()), {feature_config1, feature_config2}
        )
        self.assertFalse(experiment.equal_branch_ratio)
        self.assertFalse(experiment.is_rollout)
        self.assertTrue(experiment.prevent_pref_conflicts)
        self.assertTrue(experiment.warn_feature_schema)
        self.assertTrue(experiment.is_localized)
        self.assertEqual(
            experiment.localizations,
            json.dumps({"localization-key": "localization-value"}),
        )
        self.assertEqual(experiment.reference_branch.name, "Control")
        self.assertEqual(experiment.reference_branch.slug, "control")
        self.assertEqual(experiment.reference_branch.description, "Control Description")
        self.assertEqual(experiment.reference_branch.ratio, 2)
        self.assertEqual(
            experiment.reference_branch.feature_values.filter(
                feature_config=feature_config1
            )
            .get()
            .value,
            json.dumps({"control-feature1-key": "control-feature-1-value"}),
        )
        self.assertEqual(
            experiment.reference_branch.feature_values.filter(
                feature_config=feature_config2
            )
            .get()
            .value,
            json.dumps({"control-feature-2-key": "control-feature-2-value"}),
        )

        treatment_branch = experiment.treatment_branches[0]
        self.assertEqual(treatment_branch.name, "Treatment")
        self.assertEqual(treatment_branch.slug, "treatment")
        self.assertEqual(treatment_branch.description, "Treatment Description")
        self.assertEqual(treatment_branch.ratio, 3)
        self.assertEqual(
            treatment_branch.feature_values.filter(feature_config=feature_config1)
            .get()
            .value,
            json.dumps({"treatment-feature-1-key": "treatment-feature-1-value"}),
        )
        self.assertEqual(
            treatment_branch.feature_values.filter(feature_config=feature_config2)
            .get()
            .value,
            json.dumps({"treatment-feature-2-key": "treatment-feature-2-value"}),
        )

        self.assertEqual(
            experiment.reference_branch.screenshots.get(
                id=reference_screenshot.id
            ).description,
            "Updated control screenshot",
        )
        self.assertEqual(
            experiment.treatment_branches[0]
            .screenshots.get(id=treatment_screenshot.id)
            .description,
            "Updated treatment screenshot",
        )

        changelog = experiment.changes.get()
        self.assertIn("updated branches", changelog.message)

    def test_branches_form_saves_added_feature_config(self):
        application = NimbusExperiment.Application.DESKTOP
        feature_config1 = NimbusFeatureConfigFactory.create(application=application)
        feature_config2 = NimbusFeatureConfigFactory.create(application=application)
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=application,
            feature_configs=[feature_config1],
            equal_branch_ratio=False,
        )
        experiment.branches.all().delete()

        reference_branch = NimbusBranchFactory.create(experiment=experiment)
        treatment_branch = NimbusBranchFactory.create(experiment=experiment)
        experiment.reference_branch = reference_branch
        experiment.save()

        reference_branch_feature_config1_value = reference_branch.feature_values.filter(
            feature_config=feature_config1
        ).get()
        treatment_branch_feature_config1_value = treatment_branch.feature_values.filter(
            feature_config=feature_config1
        ).get()

        form = NimbusBranchesForm(
            instance=experiment,
            data={
                "feature_configs": [feature_config1.id, feature_config2.id],
                "equal_branch_ratio": True,
                "branches-TOTAL_FORMS": "2",
                "branches-INITIAL_FORMS": "2",
                "branches-MIN_NUM_FORMS": "0",
                "branches-MAX_NUM_FORMS": "1000",
                "branches-0-id": reference_branch.id,
                "branches-0-name": "Control",
                "branches-0-description": "Control Description",
                "branches-0-feature-value-TOTAL_FORMS": "1",
                "branches-0-feature-value-INITIAL_FORMS": "1",
                "branches-0-feature-value-MIN_NUM_FORMS": "0",
                "branches-0-feature-value-MAX_NUM_FORMS": "1000",
                "branches-0-feature-value-0-id": (
                    reference_branch_feature_config1_value.id
                ),
                "branches-0-feature-value-0-value": json.dumps(
                    {"control-feature1-key": "control-feature-1-value"}
                ),
                "branches-1-id": treatment_branch.id,
                "branches-1-name": "Treatment",
                "branches-1-description": "Treatment Description",
                "branches-1-feature-value-TOTAL_FORMS": "1",
                "branches-1-feature-value-INITIAL_FORMS": "1",
                "branches-1-feature-value-MIN_NUM_FORMS": "0",
                "branches-1-feature-value-MAX_NUM_FORMS": "1000",
                "branches-1-feature-value-0-id": (
                    treatment_branch_feature_config1_value.id
                ),
                "branches-1-feature-value-0-value": json.dumps(
                    {"treatment-feature-1-key": "treatment-feature-1-value"}
                ),
                "is_localized": True,
                "localizations": json.dumps({"localization-key": "localization-value"}),
            },
            request=self.request,
        )

        self.assertTrue(form.is_valid(), form.errors)

        form.save()
        experiment = NimbusExperiment.objects.get(id=experiment.id)

        self.assertEqual(
            set(experiment.feature_configs.all()), {feature_config1, feature_config2}
        )
        self.assertEqual(
            experiment.reference_branch.feature_values.filter(
                feature_config=feature_config1
            ).get(),
            reference_branch_feature_config1_value,
        )
        self.assertTrue(
            experiment.reference_branch.feature_values.filter(
                feature_config=feature_config2, value="{}"
            ).exists()
        )

        treatment_branch = experiment.treatment_branches[0]
        self.assertEqual(
            treatment_branch.feature_values.filter(feature_config=feature_config1).get(),
            treatment_branch_feature_config1_value,
        )
        self.assertTrue(
            treatment_branch.feature_values.filter(
                feature_config=feature_config2, value="{}"
            ).exists(),
        )

    def test_branches_form_saves_removed_feature_config(self):
        application = NimbusExperiment.Application.DESKTOP
        feature_config1 = NimbusFeatureConfigFactory.create(application=application)
        feature_config2 = NimbusFeatureConfigFactory.create(application=application)
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=application,
            feature_configs=[feature_config1, feature_config2],
            equal_branch_ratio=False,
        )
        experiment.branches.all().delete()

        reference_branch = NimbusBranchFactory.create(experiment=experiment)
        treatment_branch = NimbusBranchFactory.create(experiment=experiment)
        experiment.reference_branch = reference_branch
        experiment.save()

        reference_branch_feature_config1_value = reference_branch.feature_values.filter(
            feature_config=feature_config1
        ).get()
        reference_branch_feature_config2_value = reference_branch.feature_values.filter(
            feature_config=feature_config2
        ).get()
        treatment_branch_feature_config1_value = treatment_branch.feature_values.filter(
            feature_config=feature_config1
        ).get()
        treatment_branch_feature_config2_value = treatment_branch.feature_values.filter(
            feature_config=feature_config2
        ).get()

        form = NimbusBranchesForm(
            instance=experiment,
            data={
                "feature_configs": [feature_config1.id],
                "equal_branch_ratio": True,
                "branches-TOTAL_FORMS": "2",
                "branches-INITIAL_FORMS": "2",
                "branches-MIN_NUM_FORMS": "0",
                "branches-MAX_NUM_FORMS": "1000",
                "branches-0-id": reference_branch.id,
                "branches-0-name": "Control",
                "branches-0-description": "Control Description",
                "branches-0-feature-value-TOTAL_FORMS": "2",
                "branches-0-feature-value-INITIAL_FORMS": "2",
                "branches-0-feature-value-MIN_NUM_FORMS": "0",
                "branches-0-feature-value-MAX_NUM_FORMS": "1000",
                "branches-0-feature-value-0-id": (
                    reference_branch_feature_config1_value.id
                ),
                "branches-0-feature-value-0-value": {
                    "control-feature1-key": "control-feature-1-value"
                },
                "branches-0-feature-value-1-id": (
                    reference_branch_feature_config2_value.id
                ),
                "branches-0-feature-value-1-value": {
                    "control-feature-2-key": "control-feature-2-value"
                },
                "branches-1-id": treatment_branch.id,
                "branches-1-name": "Treatment",
                "branches-1-description": "Treatment Description",
                "branches-1-feature-value-TOTAL_FORMS": "2",
                "branches-1-feature-value-INITIAL_FORMS": "2",
                "branches-1-feature-value-MIN_NUM_FORMS": "0",
                "branches-1-feature-value-MAX_NUM_FORMS": "1000",
                "branches-1-feature-value-0-id": (
                    treatment_branch_feature_config1_value.id
                ),
                "branches-1-feature-value-0-value": {
                    "treatment-feature-1-key": "treatment-feature-1-value"
                },
                "branches-1-feature-value-1-id": (
                    treatment_branch_feature_config2_value.id
                ),
                "branches-1-feature-value-1-value": {
                    "treatment-feature-2-key": "treatment-feature-2-value"
                },
                "is_localized": True,
                "localizations": {"localization-key": "localization-value"},
            },
            request=self.request,
        )

        self.assertTrue(form.is_valid(), form.errors)

        form.save()
        experiment = NimbusExperiment.objects.get(id=experiment.id)

        self.assertEqual(set(experiment.feature_configs.all()), {feature_config1})
        self.assertEqual(
            experiment.reference_branch.feature_values.filter(
                feature_config=feature_config1
            ).get(),
            reference_branch_feature_config1_value,
        )
        self.assertFalse(
            experiment.reference_branch.feature_values.filter(
                feature_config=feature_config2
            ).exists()
        )

        treatment_branch = experiment.treatment_branches[0]
        self.assertEqual(
            treatment_branch.feature_values.filter(feature_config=feature_config1).get(),
            treatment_branch_feature_config1_value,
        )
        self.assertFalse(
            treatment_branch.feature_values.filter(
                feature_config=feature_config2
            ).exists(),
        )

    def test_branches_form_equal_branch_ratio_sets_ratio_to_1(self):
        application = NimbusExperiment.Application.DESKTOP
        feature_config1 = NimbusFeatureConfigFactory.create(application=application)
        feature_config2 = NimbusFeatureConfigFactory.create(application=application)
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=application,
            feature_configs=[feature_config1, feature_config2],
            equal_branch_ratio=False,
        )
        experiment.branches.all().delete()
        experiment.changes.all().delete()

        reference_branch = NimbusBranchFactory.create(experiment=experiment, ratio=2)
        treatment_branch = NimbusBranchFactory.create(experiment=experiment, ratio=3)
        experiment.reference_branch = reference_branch
        experiment.save()

        reference_branch_feature_config1_value = reference_branch.feature_values.filter(
            feature_config=feature_config1
        ).get()
        reference_branch_feature_config2_value = reference_branch.feature_values.filter(
            feature_config=feature_config2
        ).get()
        treatment_branch_feature_config1_value = treatment_branch.feature_values.filter(
            feature_config=feature_config1
        ).get()
        treatment_branch_feature_config2_value = treatment_branch.feature_values.filter(
            feature_config=feature_config2
        ).get()

        form = NimbusBranchesForm(
            instance=experiment,
            data={
                "feature_configs": [feature_config1.id, feature_config2.id],
                "equal_branch_ratio": True,
                "branches-TOTAL_FORMS": "2",
                "branches-INITIAL_FORMS": "2",
                "branches-MIN_NUM_FORMS": "0",
                "branches-MAX_NUM_FORMS": "1000",
                "branches-0-id": reference_branch.id,
                "branches-0-name": "Control",
                "branches-0-description": "Control Description",
                "branches-0-feature-value-TOTAL_FORMS": "2",
                "branches-0-feature-value-INITIAL_FORMS": "2",
                "branches-0-feature-value-MIN_NUM_FORMS": "0",
                "branches-0-feature-value-MAX_NUM_FORMS": "1000",
                "branches-0-feature-value-0-id": (
                    reference_branch_feature_config1_value.id
                ),
                "branches-0-feature-value-0-value": {
                    "control-feature1-key": "control-feature-1-value"
                },
                "branches-0-feature-value-1-id": (
                    reference_branch_feature_config2_value.id
                ),
                "branches-0-feature-value-1-value": {
                    "control-feature-2-key": "control-feature-2-value"
                },
                "branches-1-id": treatment_branch.id,
                "branches-1-name": "Treatment",
                "branches-1-description": "Treatment Description",
                "branches-1-feature-value-TOTAL_FORMS": "2",
                "branches-1-feature-value-INITIAL_FORMS": "2",
                "branches-1-feature-value-MIN_NUM_FORMS": "0",
                "branches-1-feature-value-MAX_NUM_FORMS": "1000",
                "branches-1-feature-value-0-id": (
                    treatment_branch_feature_config1_value.id
                ),
                "branches-1-feature-value-0-value": {
                    "treatment-feature-1-key": "treatment-feature-1-value"
                },
                "branches-1-feature-value-1-id": (
                    treatment_branch_feature_config2_value.id
                ),
                "branches-1-feature-value-1-value": {
                    "treatment-feature-2-key": "treatment-feature-2-value"
                },
                "is_localized": True,
                "localizations": {"localization-key": "localization-value"},
            },
            request=self.request,
        )

        self.assertTrue(form.is_valid(), form.errors)

        form.save()
        experiment = NimbusExperiment.objects.get(id=experiment.id)
        self.assertTrue(experiment.equal_branch_ratio)

        self.assertEqual(experiment.reference_branch.ratio, 1)

        treatment_branch = experiment.treatment_branches[0]
        self.assertEqual(treatment_branch.ratio, 1)

    def test_errors_propagate(self):
        application = NimbusExperiment.Application.DESKTOP
        feature_config1 = NimbusFeatureConfigFactory.create(application=application)
        feature_config2 = NimbusFeatureConfigFactory.create(application=application)
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=application,
            feature_configs=[feature_config1, feature_config2],
            equal_branch_ratio=False,
            is_localized=False,
            localizations=None,
        )
        experiment.branches.all().delete()

        reference_branch = NimbusBranchFactory.create(experiment=experiment, ratio=1)
        experiment.reference_branch = reference_branch
        experiment.save()

        form = NimbusBranchesForm(
            instance=experiment,
            data={
                "feature_configs": [feature_config1.id, feature_config2.id],
                "equal_branch_ratio": False,
                "branches-TOTAL_FORMS": "1",
                "branches-INITIAL_FORMS": "1",
                "branches-MIN_NUM_FORMS": "0",
                "branches-MAX_NUM_FORMS": "1000",
                "branches-0-id": reference_branch.id,
                "branches-0-name": "Control",
                "branches-0-description": "Control Description",
                "branches-0-ratio": 2,
                # create a phantom missing form to force validation failure
                "branches-0-feature-value-TOTAL_FORMS": "1",
                "branches-0-feature-value-INITIAL_FORMS": "1",
                "branches-0-feature-value-MIN_NUM_FORMS": "0",
                "branches-0-feature-value-MAX_NUM_FORMS": "1000",
                # Screenshot formset with missing id field to force validation failure
                "branches-0-screenshots-TOTAL_FORMS": "1",
                "branches-0-screenshots-INITIAL_FORMS": "1",
                "branches-0-screenshots-MIN_NUM_FORMS": "0",
                "branches-0-screenshots-MAX_NUM_FORMS": "1000",
                # No id for screenshot 0
                "is_localized": True,
                "localizations": json.dumps({"localization-key": "localization-value"}),
            },
            request=self.request,
        )

        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors,
            {
                "branches": [
                    {
                        "branch_feature_values": [
                            {"id": ["This field is required."]},
                        ],
                        "screenshots": [
                            {"id": ["This field is required."]},
                        ],
                    },
                ]
            },
        )

    def test_is_rollout_deletes_treatment_branches(self):
        application = NimbusExperiment.Application.DESKTOP
        feature_config1 = NimbusFeatureConfigFactory.create(application=application)
        feature_config2 = NimbusFeatureConfigFactory.create(application=application)
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=application,
            feature_configs=[feature_config1, feature_config2],
            equal_branch_ratio=False,
            is_localized=False,
            localizations=None,
            is_rollout=False,
        )
        experiment.branches.all().delete()
        experiment.changes.all().delete()

        reference_branch = NimbusBranchFactory.create(experiment=experiment, ratio=1)
        treatment_branch = NimbusBranchFactory.create(experiment=experiment, ratio=1)
        experiment.reference_branch = reference_branch
        experiment.save()

        reference_branch_feature_config1_value = reference_branch.feature_values.filter(
            feature_config=feature_config1
        ).get()
        reference_branch_feature_config2_value = reference_branch.feature_values.filter(
            feature_config=feature_config2
        ).get()
        treatment_branch_feature_config1_value = treatment_branch.feature_values.filter(
            feature_config=feature_config1
        ).get()
        treatment_branch_feature_config2_value = treatment_branch.feature_values.filter(
            feature_config=feature_config2
        ).get()

        form = NimbusBranchesForm(
            instance=experiment,
            data={
                "feature_configs": [feature_config1.id, feature_config2.id],
                "equal_branch_ratio": False,
                "is_rollout": True,
                "branches-TOTAL_FORMS": "2",
                "branches-INITIAL_FORMS": "2",
                "branches-MIN_NUM_FORMS": "0",
                "branches-MAX_NUM_FORMS": "1000",
                "branches-0-id": reference_branch.id,
                "branches-0-name": "Control",
                "branches-0-description": "Control Description",
                "branches-0-ratio": 2,
                "branches-0-feature-value-TOTAL_FORMS": "2",
                "branches-0-feature-value-INITIAL_FORMS": "2",
                "branches-0-feature-value-MIN_NUM_FORMS": "0",
                "branches-0-feature-value-MAX_NUM_FORMS": "1000",
                "branches-0-feature-value-0-id": (
                    reference_branch_feature_config1_value.id
                ),
                "branches-0-feature-value-0-value": json.dumps(
                    {"control-feature1-key": "control-feature-1-value"}
                ),
                "branches-0-feature-value-1-id": (
                    reference_branch_feature_config2_value.id
                ),
                "branches-0-feature-value-1-value": json.dumps(
                    {"control-feature-2-key": "control-feature-2-value"}
                ),
                "branches-1-id": treatment_branch.id,
                "branches-1-name": "Treatment",
                "branches-1-description": "Treatment Description",
                "branches-1-ratio": 3,
                "branches-1-feature-value-TOTAL_FORMS": "2",
                "branches-1-feature-value-INITIAL_FORMS": "2",
                "branches-1-feature-value-MIN_NUM_FORMS": "0",
                "branches-1-feature-value-MAX_NUM_FORMS": "1000",
                "branches-1-feature-value-0-id": (
                    treatment_branch_feature_config1_value.id
                ),
                "branches-1-feature-value-0-value": json.dumps(
                    {"treatment-feature-1-key": "treatment-feature-1-value"}
                ),
                "branches-1-feature-value-1-id": (
                    treatment_branch_feature_config2_value.id
                ),
                "branches-1-feature-value-1-value": json.dumps(
                    {"treatment-feature-2-key": "treatment-feature-2-value"}
                ),
                "is_localized": True,
                "localizations": json.dumps({"localization-key": "localization-value"}),
            },
            request=self.request,
        )

        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        experiment = NimbusExperiment.objects.get(id=experiment.id)

        self.assertTrue(experiment.is_rollout)
        self.assertIsNotNone(experiment.reference_branch)
        self.assertEqual(experiment.branches.count(), 1)
        self.assertEqual(len(experiment.treatment_branches), 0)

    def test_show_errors_flag_adds_query_param_to_hx_post(self):
        application = NimbusExperiment.Application.DESKTOP
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=application,
        )
        experiment.branches.all().delete()

        self.request.GET = {"show_errors": "true"}

        form = NimbusBranchesForm(instance=experiment, request=self.request)

        for field in form.update_on_change_fields:
            self.assertIn("show_errors", form.fields[field].widget.attrs["hx-post"])

    def test_branches_form_saves_firefox_labs_fields(self):
        application = NimbusExperiment.Application.DESKTOP
        feature_config = NimbusFeatureConfigFactory.create(application=application)
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=application,
            feature_configs=[feature_config],
            equal_branch_ratio=False,
            is_localized=False,
            is_rollout=False,
            localizations=None,
            prevent_pref_conflicts=False,
            warn_feature_schema=False,
        )
        experiment.branches.all().delete()
        experiment.changes.all().delete()

        reference_branch = NimbusBranchFactory.create(experiment=experiment, ratio=1)
        experiment.reference_branch = reference_branch
        experiment.save()

        labs_title = "labs-title-id"
        labs_description = "labs-description-id"
        labs_description_links = '{"link1": "https://example.com"}'
        labs_group = NimbusExperiment.FirefoxLabsGroups.CUSTOMIZE_BROWSING
        requires_restart = True

        form = NimbusBranchesForm(
            instance=experiment,
            data={
                "feature_configs": [feature_config.id],
                "equal_branch_ratio": False,
                "is_rollout": False,
                "prevent_pref_conflicts": True,
                "warn_feature_schema": True,
                "branches-TOTAL_FORMS": "1",
                "branches-INITIAL_FORMS": "1",
                "branches-MIN_NUM_FORMS": "0",
                "branches-MAX_NUM_FORMS": "1000",
                "branches-0-id": reference_branch.id,
                "branches-0-name": "Control",
                "branches-0-description": "Control Description",
                "branches-0-ratio": 2,
                "branches-0-feature-value-TOTAL_FORMS": "1",
                "branches-0-feature-value-INITIAL_FORMS": "1",
                "branches-0-feature-value-MIN_NUM_FORMS": "0",
                "branches-0-feature-value-MAX_NUM_FORMS": "1000",
                "branches-0-feature-value-0-id": (
                    reference_branch.feature_values.first().id
                ),
                "branches-0-feature-value-0-value": "{}",
                "branches-0-screenshots-TOTAL_FORMS": "0",
                "branches-0-screenshots-INITIAL_FORMS": "0",
                "branches-0-screenshots-MIN_NUM_FORMS": "0",
                "branches-0-screenshots-MAX_NUM_FORMS": "1000",
                "is_firefox_labs_opt_in": True,
                "firefox_labs_title": labs_title,
                "firefox_labs_description": labs_description,
                "firefox_labs_description_links": labs_description_links,
                "firefox_labs_group": labs_group,
                "requires_restart": requires_restart,
            },
            request=self.request,
        )

        self.assertTrue(form.is_valid(), form.errors)
        experiment = form.save()
        self.assertTrue(experiment.is_firefox_labs_opt_in)
        self.assertEqual(experiment.firefox_labs_title, labs_title)
        self.assertEqual(experiment.firefox_labs_description, labs_description)
        self.assertEqual(
            experiment.firefox_labs_description_links, labs_description_links
        )
        self.assertEqual(experiment.firefox_labs_group, labs_group)
        self.assertTrue(experiment.requires_restart)

    def test_labs_opt_in_sets_is_rollout(self):
        application = NimbusExperiment.Application.DESKTOP
        feature_config = NimbusFeatureConfigFactory.create(application=application)
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=application,
            feature_configs=[feature_config],
            is_rollout=False,
            is_firefox_labs_opt_in=False,
        )
        experiment.branches.all().delete()
        experiment.changes.all().delete()
        reference_branch = NimbusBranchFactory.create(experiment=experiment, ratio=1)
        experiment.reference_branch = reference_branch
        experiment.save()

        form = NimbusBranchesForm(
            instance=experiment,
            data={
                "feature_configs": [feature_config.id],
                "equal_branch_ratio": False,
                "is_rollout": False,
                "is_firefox_labs_opt_in": True,
                "branches-TOTAL_FORMS": "1",
                "branches-INITIAL_FORMS": "1",
                "branches-MIN_NUM_FORMS": "0",
                "branches-MAX_NUM_FORMS": "1000",
                "branches-0-id": reference_branch.id,
                "branches-0-name": "Control",
                "branches-0-description": "Control Description",
                "branches-0-ratio": 1,
                "branches-0-feature-value-TOTAL_FORMS": "1",
                "branches-0-feature-value-INITIAL_FORMS": "1",
                "branches-0-feature-value-MIN_NUM_FORMS": "0",
                "branches-0-feature-value-MAX_NUM_FORMS": "1000",
                "branches-0-feature-value-0-id": (
                    reference_branch.feature_values.first().id
                ),
                "branches-0-feature-value-0-value": "{}",
                "branches-0-screenshots-TOTAL_FORMS": "0",
                "branches-0-screenshots-INITIAL_FORMS": "0",
                "branches-0-screenshots-MIN_NUM_FORMS": "0",
                "branches-0-screenshots-MAX_NUM_FORMS": "1000",
            },
            request=self.request,
        )
        self.assertTrue(form.is_valid(), form.errors)
        experiment = form.save()
        self.assertTrue(experiment.is_firefox_labs_opt_in)
        self.assertTrue(experiment.is_rollout)

    def test_unset_is_rollout_unsets_labs_opt_in(self):
        application = NimbusExperiment.Application.DESKTOP
        feature_config = NimbusFeatureConfigFactory.create(application=application)
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=application,
            feature_configs=[feature_config],
            is_rollout=True,
            is_firefox_labs_opt_in=True,
            firefox_labs_title="title",
            firefox_labs_description="description",
            firefox_labs_group=NimbusExperiment.FirefoxLabsGroups.CUSTOMIZE_BROWSING,
        )
        experiment.branches.all().delete()
        experiment.changes.all().delete()
        reference_branch = NimbusBranchFactory.create(experiment=experiment, ratio=1)
        experiment.reference_branch = reference_branch
        experiment.save()

        form = NimbusBranchesForm(
            instance=experiment,
            data={
                "feature_configs": [feature_config.id],
                "equal_branch_ratio": False,
                "is_rollout": False,
                "is_firefox_labs_opt_in": True,
                "branches-TOTAL_FORMS": "1",
                "branches-INITIAL_FORMS": "1",
                "branches-MIN_NUM_FORMS": "0",
                "branches-MAX_NUM_FORMS": "1000",
                "branches-0-id": reference_branch.id,
                "branches-0-name": "Control",
                "branches-0-description": "Control Description",
                "branches-0-ratio": 1,
                "branches-0-feature-value-TOTAL_FORMS": "1",
                "branches-0-feature-value-INITIAL_FORMS": "1",
                "branches-0-feature-value-MIN_NUM_FORMS": "0",
                "branches-0-feature-value-MAX_NUM_FORMS": "1000",
                "branches-0-feature-value-0-id": (
                    reference_branch.feature_values.first().id
                ),
                "branches-0-feature-value-0-value": "{}",
                "branches-0-screenshots-TOTAL_FORMS": "0",
                "branches-0-screenshots-INITIAL_FORMS": "0",
                "branches-0-screenshots-MIN_NUM_FORMS": "0",
                "branches-0-screenshots-MAX_NUM_FORMS": "1000",
            },
            request=self.request,
        )
        self.assertTrue(form.is_valid(), form.errors)
        experiment = form.save()
        self.assertFalse(experiment.is_rollout)
        self.assertFalse(experiment.is_firefox_labs_opt_in)

    def test_is_rollout_true_labs_opt_in_false(self):
        application = NimbusExperiment.Application.DESKTOP
        feature_config = NimbusFeatureConfigFactory.create(application=application)
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=application,
            feature_configs=[feature_config],
            is_rollout=False,
            is_firefox_labs_opt_in=False,
        )
        experiment.branches.all().delete()
        experiment.changes.all().delete()
        reference_branch = NimbusBranchFactory.create(experiment=experiment, ratio=1)
        experiment.reference_branch = reference_branch
        experiment.save()

        form = NimbusBranchesForm(
            instance=experiment,
            data={
                "feature_configs": [feature_config.id],
                "equal_branch_ratio": False,
                "is_rollout": True,
                "is_firefox_labs_opt_in": False,
                "branches-TOTAL_FORMS": "1",
                "branches-INITIAL_FORMS": "1",
                "branches-MIN_NUM_FORMS": "0",
                "branches-MAX_NUM_FORMS": "1000",
                "branches-0-id": reference_branch.id,
                "branches-0-name": "Control",
                "branches-0-description": "Control Description",
                "branches-0-ratio": 1,
                "branches-0-feature-value-TOTAL_FORMS": "1",
                "branches-0-feature-value-INITIAL_FORMS": "1",
                "branches-0-feature-value-MIN_NUM_FORMS": "0",
                "branches-0-feature-value-MAX_NUM_FORMS": "1000",
                "branches-0-feature-value-0-id": (
                    reference_branch.feature_values.first().id
                ),
                "branches-0-feature-value-0-value": "{}",
                "branches-0-screenshots-TOTAL_FORMS": "0",
                "branches-0-screenshots-INITIAL_FORMS": "0",
                "branches-0-screenshots-MIN_NUM_FORMS": "0",
                "branches-0-screenshots-MAX_NUM_FORMS": "1000",
            },
            request=self.request,
        )
        self.assertTrue(form.is_valid(), form.errors)
        experiment = form.save()
        self.assertTrue(experiment.is_rollout)
        self.assertFalse(experiment.is_firefox_labs_opt_in)


class TestNimbusBranchCreateForm(RequestFormTestCase):
    def test_form_saves_branches(self):
        application = NimbusExperiment.Application.DESKTOP
        feature_config1 = NimbusFeatureConfigFactory.create(application=application)
        feature_config2 = NimbusFeatureConfigFactory.create(application=application)
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=application,
            feature_configs=[feature_config1, feature_config2],
            equal_branch_ratio=False,
            is_localized=False,
            is_rollout=False,
            localizations=None,
            prevent_pref_conflicts=False,
            warn_feature_schema=False,
        )
        experiment.branches.all().delete()
        experiment.changes.all().delete()

        reference_branch = NimbusBranchFactory.create(experiment=experiment, ratio=1)
        treatment_branch = NimbusBranchFactory.create(experiment=experiment, ratio=1)
        experiment.reference_branch = reference_branch
        experiment.save()

        reference_branch_feature_config1_value = reference_branch.feature_values.filter(
            feature_config=feature_config1
        ).get()
        reference_branch_feature_config2_value = reference_branch.feature_values.filter(
            feature_config=feature_config2
        ).get()
        treatment_branch_feature_config1_value = treatment_branch.feature_values.filter(
            feature_config=feature_config1
        ).get()
        treatment_branch_feature_config2_value = treatment_branch.feature_values.filter(
            feature_config=feature_config2
        ).get()

        reference_screenshot = reference_branch.screenshots.first()
        treatment_screenshot = treatment_branch.screenshots.first()

        # Create a valid in-memory PNG image
        image_bytes = io.BytesIO()
        image = Image.new("RGB", (10, 10), color="red")
        image.save(image_bytes, format="PNG")
        image_bytes.seek(0)
        dummy_image = SimpleUploadedFile(
            "test.png", image_bytes.read(), content_type="image/png"
        )

        form = NimbusBranchCreateForm(
            instance=experiment,
            data={
                "feature_configs": [feature_config1.id, feature_config2.id],
                "equal_branch_ratio": False,
                "is_rollout": False,
                "prevent_pref_conflicts": True,
                "warn_feature_schema": True,
                "branches-TOTAL_FORMS": "2",
                "branches-INITIAL_FORMS": "2",
                "branches-MIN_NUM_FORMS": "0",
                "branches-MAX_NUM_FORMS": "1000",
                "branches-0-id": reference_branch.id,
                "branches-0-name": "Control",
                "branches-0-description": "Control Description",
                "branches-0-ratio": 2,
                "branches-0-feature-value-TOTAL_FORMS": "2",
                "branches-0-feature-value-INITIAL_FORMS": "2",
                "branches-0-feature-value-MIN_NUM_FORMS": "0",
                "branches-0-feature-value-MAX_NUM_FORMS": "1000",
                "branches-0-feature-value-0-id": (
                    reference_branch_feature_config1_value.id
                ),
                "branches-0-feature-value-0-value": json.dumps(
                    {"control-feature1-key": "control-feature-1-value"}
                ),
                "branches-0-feature-value-1-id": (
                    reference_branch_feature_config2_value.id
                ),
                "branches-0-feature-value-1-value": json.dumps(
                    {"control-feature-2-key": "control-feature-2-value"}
                ),
                "branches-0-screenshots-TOTAL_FORMS": "1",
                "branches-0-screenshots-INITIAL_FORMS": "1",
                "branches-0-screenshots-MIN_NUM_FORMS": "0",
                "branches-0-screenshots-MAX_NUM_FORMS": "1000",
                "branches-0-screenshots-0-id": reference_screenshot.id,
                "branches-0-screenshots-0-description": "Updated control screenshot",
                "branches-0-screenshots-0-image": dummy_image,
                "branches-1-id": treatment_branch.id,
                "branches-1-name": "Treatment",
                "branches-1-description": "Treatment Description",
                "branches-1-ratio": 3,
                "branches-1-feature-value-TOTAL_FORMS": "2",
                "branches-1-feature-value-INITIAL_FORMS": "2",
                "branches-1-feature-value-MIN_NUM_FORMS": "0",
                "branches-1-feature-value-MAX_NUM_FORMS": "1000",
                "branches-1-feature-value-0-id": (
                    treatment_branch_feature_config1_value.id
                ),
                "branches-1-feature-value-0-value": json.dumps(
                    {"treatment-feature-1-key": "treatment-feature-1-value"}
                ),
                "branches-1-feature-value-1-id": (
                    treatment_branch_feature_config2_value.id
                ),
                "branches-1-feature-value-1-value": json.dumps(
                    {"treatment-feature-2-key": "treatment-feature-2-value"}
                ),
                "branches-1-screenshots-TOTAL_FORMS": "1",
                "branches-1-screenshots-INITIAL_FORMS": "1",
                "branches-1-screenshots-MIN_NUM_FORMS": "0",
                "branches-1-screenshots-MAX_NUM_FORMS": "1000",
                "branches-1-screenshots-0-id": treatment_screenshot.id,
                "branches-1-screenshots-0-description": "Updated treatment screenshot",
                "branches-1-screenshots-0-image": dummy_image,
                "is_localized": True,
                "localizations": json.dumps({"localization-key": "localization-value"}),
            },
            files={
                "branches-0-screenshots-0-image": dummy_image,
                "branches-1-screenshots-0-image": dummy_image,
            },
            request=self.request,
        )

        self.assertTrue(form.is_valid(), form.errors)

        form.save()
        experiment = NimbusExperiment.objects.get(id=experiment.id)

        self.assertEqual(
            set(experiment.feature_configs.all()), {feature_config1, feature_config2}
        )
        self.assertFalse(experiment.equal_branch_ratio)
        self.assertFalse(experiment.is_rollout)
        self.assertTrue(experiment.prevent_pref_conflicts)
        self.assertTrue(experiment.warn_feature_schema)
        self.assertTrue(experiment.is_localized)
        self.assertEqual(
            experiment.localizations,
            json.dumps({"localization-key": "localization-value"}),
        )
        self.assertEqual(experiment.reference_branch.name, "Control")
        self.assertEqual(experiment.reference_branch.slug, "control")
        self.assertEqual(experiment.reference_branch.description, "Control Description")
        self.assertEqual(experiment.reference_branch.ratio, 2)
        self.assertEqual(
            experiment.reference_branch.feature_values.filter(
                feature_config=feature_config1
            )
            .get()
            .value,
            json.dumps({"control-feature1-key": "control-feature-1-value"}),
        )
        self.assertEqual(
            experiment.reference_branch.feature_values.filter(
                feature_config=feature_config2
            )
            .get()
            .value,
            json.dumps({"control-feature-2-key": "control-feature-2-value"}),
        )

        treatment_branch = experiment.treatment_branches[0]
        self.assertEqual(treatment_branch.name, "Treatment")
        self.assertEqual(treatment_branch.slug, "treatment")
        self.assertEqual(treatment_branch.description, "Treatment Description")
        self.assertEqual(treatment_branch.ratio, 3)
        self.assertEqual(
            treatment_branch.feature_values.filter(feature_config=feature_config1)
            .get()
            .value,
            json.dumps({"treatment-feature-1-key": "treatment-feature-1-value"}),
        )
        self.assertEqual(
            treatment_branch.feature_values.filter(feature_config=feature_config2)
            .get()
            .value,
            json.dumps({"treatment-feature-2-key": "treatment-feature-2-value"}),
        )

        self.assertEqual(
            experiment.reference_branch.screenshots.get(
                id=reference_screenshot.id
            ).description,
            "Updated control screenshot",
        )
        self.assertEqual(
            experiment.treatment_branches[0]
            .screenshots.get(id=treatment_screenshot.id)
            .description,
            "Updated treatment screenshot",
        )

    def test_form_creates_reference_branch(self):
        feature_config1 = NimbusFeatureConfigFactory.create(
            application=NimbusExperiment.Application.DESKTOP
        )
        feature_config2 = NimbusFeatureConfigFactory.create(
            application=NimbusExperiment.Application.DESKTOP
        )
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[feature_config1, feature_config2],
        )
        experiment.branches.all().delete()
        experiment.changes.all().delete()
        experiment.reference_branch = None
        experiment.save()

        form = NimbusBranchCreateForm(
            instance=experiment,
            data={
                "feature_configs": [feature_config1.id, feature_config2.id],
            },
            request=self.request,
        )
        self.assertTrue(form.is_valid())
        experiment = form.save()

        self.assertEqual(experiment.reference_branch.name, "Control")
        self.assertEqual(experiment.reference_branch.slug, "control")
        self.assertEqual(experiment.reference_branch.description, "")
        self.assertEqual(experiment.reference_branch.ratio, 1)
        self.assertEqual(experiment.reference_branch.feature_values.count(), 2)
        self.assertEqual(
            set(
                experiment.reference_branch.feature_values.values_list(
                    "feature_config", flat=True
                )
            ),
            {feature_config1.id, feature_config2.id},
        )

        change = experiment.changes.get()
        self.assertIn("added a branch", change.message)

    def test_form_creates_treatment_branches(self):
        feature_config1 = NimbusFeatureConfigFactory.create(
            application=NimbusExperiment.Application.DESKTOP
        )
        feature_config2 = NimbusFeatureConfigFactory.create(
            application=NimbusExperiment.Application.DESKTOP
        )
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[feature_config1, feature_config2],
        )
        experiment.branches.all().exclude(id=experiment.reference_branch.id).delete()

        form = NimbusBranchCreateForm(
            instance=experiment,
            data={
                "feature_configs": [feature_config1.id, feature_config2.id],
            },
            request=self.request,
        )
        self.assertTrue(form.is_valid())
        experiment = form.save()

        treatment_branch = experiment.treatment_branches[0]
        self.assertEqual(treatment_branch.name, "Treatment A")
        self.assertEqual(treatment_branch.slug, "treatment-a")
        self.assertEqual(treatment_branch.description, "")
        self.assertEqual(treatment_branch.ratio, 1)
        self.assertEqual(treatment_branch.feature_values.count(), 2)
        self.assertEqual(
            set(treatment_branch.feature_values.values_list("feature_config", flat=True)),
            {feature_config1.id, feature_config2.id},
        )

        form = NimbusBranchCreateForm(
            instance=experiment,
            data={
                "feature_configs": [feature_config1.id, feature_config2.id],
            },
            request=self.request,
        )
        self.assertTrue(form.is_valid())
        experiment = form.save()

        treatment_branch = experiment.treatment_branches[1]
        self.assertEqual(treatment_branch.name, "Treatment B")
        self.assertEqual(treatment_branch.slug, "treatment-b")
        self.assertEqual(treatment_branch.description, "")
        self.assertEqual(treatment_branch.ratio, 1)
        self.assertEqual(treatment_branch.feature_values.count(), 2)
        self.assertEqual(
            set(treatment_branch.feature_values.values_list("feature_config", flat=True)),
            {feature_config1.id, feature_config2.id},
        )


class TestNimbusBranchDeleteForm(RequestFormTestCase):
    def test_form_saves_branches(self):
        application = NimbusExperiment.Application.DESKTOP
        feature_config1 = NimbusFeatureConfigFactory.create(application=application)
        feature_config2 = NimbusFeatureConfigFactory.create(application=application)
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=application,
            feature_configs=[feature_config1, feature_config2],
            equal_branch_ratio=False,
            is_localized=False,
            is_rollout=False,
            localizations=None,
            prevent_pref_conflicts=False,
            warn_feature_schema=False,
        )
        experiment.branches.all().delete()
        experiment.changes.all().delete()

        reference_branch = NimbusBranchFactory.create(experiment=experiment, ratio=1)
        treatment_branch = NimbusBranchFactory.create(experiment=experiment, ratio=1)
        deletable_branch = NimbusBranchFactory.create(experiment=experiment, ratio=1)

        experiment.reference_branch = reference_branch
        experiment.save()

        reference_branch_feature_config1_value = reference_branch.feature_values.filter(
            feature_config=feature_config1
        ).get()
        reference_branch_feature_config2_value = reference_branch.feature_values.filter(
            feature_config=feature_config2
        ).get()
        treatment_branch_feature_config1_value = treatment_branch.feature_values.filter(
            feature_config=feature_config1
        ).get()
        treatment_branch_feature_config2_value = treatment_branch.feature_values.filter(
            feature_config=feature_config2
        ).get()

        reference_screenshot = reference_branch.screenshots.first()
        treatment_screenshot = treatment_branch.screenshots.first()

        # Create a valid in-memory PNG image
        image_bytes = io.BytesIO()
        image = Image.new("RGB", (10, 10), color="red")
        image.save(image_bytes, format="PNG")
        image_bytes.seek(0)
        dummy_image = SimpleUploadedFile(
            "test.png", image_bytes.read(), content_type="image/png"
        )

        form = NimbusBranchCreateForm(
            instance=experiment,
            data={
                "feature_configs": [feature_config1.id, feature_config2.id],
                "equal_branch_ratio": False,
                "is_rollout": False,
                "prevent_pref_conflicts": True,
                "warn_feature_schema": True,
                "branches-TOTAL_FORMS": "2",
                "branches-INITIAL_FORMS": "2",
                "branches-MIN_NUM_FORMS": "0",
                "branches-MAX_NUM_FORMS": "1000",
                "branches-0-id": reference_branch.id,
                "branches-0-name": "Control",
                "branches-0-description": "Control Description",
                "branches-0-ratio": 2,
                "branches-0-feature-value-TOTAL_FORMS": "2",
                "branches-0-feature-value-INITIAL_FORMS": "2",
                "branches-0-feature-value-MIN_NUM_FORMS": "0",
                "branches-0-feature-value-MAX_NUM_FORMS": "1000",
                "branches-0-feature-value-0-id": (
                    reference_branch_feature_config1_value.id
                ),
                "branches-0-feature-value-0-value": json.dumps(
                    {"control-feature1-key": "control-feature-1-value"}
                ),
                "branches-0-feature-value-1-id": (
                    reference_branch_feature_config2_value.id
                ),
                "branches-0-feature-value-1-value": json.dumps(
                    {"control-feature-2-key": "control-feature-2-value"}
                ),
                "branches-0-screenshots-TOTAL_FORMS": "1",
                "branches-0-screenshots-INITIAL_FORMS": "1",
                "branches-0-screenshots-MIN_NUM_FORMS": "0",
                "branches-0-screenshots-MAX_NUM_FORMS": "1000",
                "branches-0-screenshots-0-id": reference_screenshot.id,
                "branches-0-screenshots-0-description": "Updated control screenshot",
                "branches-0-screenshots-0-image": dummy_image,
                "branches-1-id": treatment_branch.id,
                "branches-1-name": "Treatment",
                "branches-1-description": "Treatment Description",
                "branches-1-ratio": 3,
                "branches-1-feature-value-TOTAL_FORMS": "2",
                "branches-1-feature-value-INITIAL_FORMS": "2",
                "branches-1-feature-value-MIN_NUM_FORMS": "0",
                "branches-1-feature-value-MAX_NUM_FORMS": "1000",
                "branches-1-feature-value-0-id": (
                    treatment_branch_feature_config1_value.id
                ),
                "branches-1-feature-value-0-value": json.dumps(
                    {"treatment-feature-1-key": "treatment-feature-1-value"}
                ),
                "branches-1-feature-value-1-id": (
                    treatment_branch_feature_config2_value.id
                ),
                "branches-1-feature-value-1-value": json.dumps(
                    {"treatment-feature-2-key": "treatment-feature-2-value"}
                ),
                "branches-1-screenshots-TOTAL_FORMS": "1",
                "branches-1-screenshots-INITIAL_FORMS": "1",
                "branches-1-screenshots-MIN_NUM_FORMS": "0",
                "branches-1-screenshots-MAX_NUM_FORMS": "1000",
                "branches-1-screenshots-0-id": treatment_screenshot.id,
                "branches-1-screenshots-0-description": "Updated treatment screenshot",
                "branches-1-screenshots-0-image": dummy_image,
                "is_localized": True,
                "localizations": json.dumps({"localization-key": "localization-value"}),
                "branch_id": deletable_branch.id,
            },
            files={
                "branches-0-screenshots-0-image": dummy_image,
                "branches-1-screenshots-0-image": dummy_image,
            },
            request=self.request,
        )

        self.assertTrue(form.is_valid(), form.errors)

        form.save()
        experiment = NimbusExperiment.objects.get(id=experiment.id)

        self.assertEqual(
            set(experiment.feature_configs.all()), {feature_config1, feature_config2}
        )
        self.assertFalse(experiment.equal_branch_ratio)
        self.assertFalse(experiment.is_rollout)
        self.assertTrue(experiment.prevent_pref_conflicts)
        self.assertTrue(experiment.warn_feature_schema)
        self.assertTrue(experiment.is_localized)
        self.assertEqual(
            experiment.localizations,
            json.dumps({"localization-key": "localization-value"}),
        )
        self.assertEqual(experiment.reference_branch.name, "Control")
        self.assertEqual(experiment.reference_branch.slug, "control")
        self.assertEqual(experiment.reference_branch.description, "Control Description")
        self.assertEqual(experiment.reference_branch.ratio, 2)
        self.assertEqual(
            experiment.reference_branch.feature_values.filter(
                feature_config=feature_config1
            )
            .get()
            .value,
            json.dumps({"control-feature1-key": "control-feature-1-value"}),
        )
        self.assertEqual(
            experiment.reference_branch.feature_values.filter(
                feature_config=feature_config2
            )
            .get()
            .value,
            json.dumps({"control-feature-2-key": "control-feature-2-value"}),
        )

        treatment_branch = experiment.treatment_branches[0]
        self.assertEqual(treatment_branch.name, "Treatment")
        self.assertEqual(treatment_branch.slug, "treatment")
        self.assertEqual(treatment_branch.description, "Treatment Description")
        self.assertEqual(treatment_branch.ratio, 3)
        self.assertEqual(
            treatment_branch.feature_values.filter(feature_config=feature_config1)
            .get()
            .value,
            json.dumps({"treatment-feature-1-key": "treatment-feature-1-value"}),
        )
        self.assertEqual(
            treatment_branch.feature_values.filter(feature_config=feature_config2)
            .get()
            .value,
            json.dumps({"treatment-feature-2-key": "treatment-feature-2-value"}),
        )

        self.assertEqual(
            experiment.reference_branch.screenshots.get(
                id=reference_screenshot.id
            ).description,
            "Updated control screenshot",
        )
        self.assertEqual(
            experiment.treatment_branches[0]
            .screenshots.get(id=treatment_screenshot.id)
            .description,
            "Updated treatment screenshot",
        )

    def test_form_cannot_delete_reference_branch(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
        )
        experiment.branches.all().exclude(id=experiment.reference_branch.id).delete()
        experiment.changes.all().delete()

        self.assertIsNotNone(experiment.reference_branch)

        form = NimbusBranchDeleteForm(
            instance=experiment,
            data={"branch_id": experiment.reference_branch.id},
            request=self.request,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("branch_id", form.errors)

    def test_form_deletes_treatment_branch(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.DESKTOP,
        )
        experiment.changes.all().delete()

        branch_count = experiment.branches.count()

        treatment_branch = experiment.treatment_branches[0]

        form = NimbusBranchDeleteForm(
            instance=experiment,
            data={"branch_id": treatment_branch.id},
            request=self.request,
        )
        self.assertTrue(form.is_valid())
        form.save()

        experiment = NimbusExperiment.objects.get(id=experiment.id)

        self.assertEqual(experiment.branches.count(), branch_count - 1)
        self.assertNotIn(treatment_branch, experiment.treatment_branches)
        self.assertEqual(experiment.changes.count(), 1)
        self.assertIn("removed a branch", experiment.changes.get().message)


class TestBranchScreenshotCreateForm(RequestFormTestCase):
    def test_form_saves_branches(self):
        application = NimbusExperiment.Application.DESKTOP
        feature_config1 = NimbusFeatureConfigFactory.create(application=application)
        feature_config2 = NimbusFeatureConfigFactory.create(application=application)
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=application,
            feature_configs=[feature_config1, feature_config2],
            equal_branch_ratio=False,
            is_localized=False,
            is_rollout=False,
            localizations=None,
            prevent_pref_conflicts=False,
            warn_feature_schema=False,
        )
        experiment.branches.all().delete()
        experiment.changes.all().delete()

        reference_branch = NimbusBranchFactory.create(experiment=experiment, ratio=1)
        treatment_branch = NimbusBranchFactory.create(experiment=experiment, ratio=1)
        experiment.reference_branch = reference_branch
        experiment.save()

        reference_branch_feature_config1_value = reference_branch.feature_values.filter(
            feature_config=feature_config1
        ).get()
        reference_branch_feature_config2_value = reference_branch.feature_values.filter(
            feature_config=feature_config2
        ).get()
        treatment_branch_feature_config1_value = treatment_branch.feature_values.filter(
            feature_config=feature_config1
        ).get()
        treatment_branch_feature_config2_value = treatment_branch.feature_values.filter(
            feature_config=feature_config2
        ).get()

        reference_screenshot = reference_branch.screenshots.first()
        treatment_screenshot = treatment_branch.screenshots.first()

        # Create a valid in-memory PNG image
        image_bytes = io.BytesIO()
        image = Image.new("RGB", (10, 10), color="red")
        image.save(image_bytes, format="PNG")
        image_bytes.seek(0)
        dummy_image = SimpleUploadedFile(
            "test.png", image_bytes.read(), content_type="image/png"
        )

        form = BranchScreenshotCreateForm(
            instance=experiment,
            data={
                "feature_configs": [feature_config1.id, feature_config2.id],
                "equal_branch_ratio": False,
                "is_rollout": False,
                "prevent_pref_conflicts": True,
                "warn_feature_schema": True,
                "branches-TOTAL_FORMS": "2",
                "branches-INITIAL_FORMS": "2",
                "branches-MIN_NUM_FORMS": "0",
                "branches-MAX_NUM_FORMS": "1000",
                "branches-0-id": reference_branch.id,
                "branches-0-name": "Control",
                "branches-0-description": "Control Description",
                "branches-0-ratio": 2,
                "branches-0-feature-value-TOTAL_FORMS": "2",
                "branches-0-feature-value-INITIAL_FORMS": "2",
                "branches-0-feature-value-MIN_NUM_FORMS": "0",
                "branches-0-feature-value-MAX_NUM_FORMS": "1000",
                "branches-0-feature-value-0-id": (
                    reference_branch_feature_config1_value.id
                ),
                "branches-0-feature-value-0-value": json.dumps(
                    {"control-feature1-key": "control-feature-1-value"}
                ),
                "branches-0-feature-value-1-id": (
                    reference_branch_feature_config2_value.id
                ),
                "branches-0-feature-value-1-value": json.dumps(
                    {"control-feature-2-key": "control-feature-2-value"}
                ),
                "branches-0-screenshots-TOTAL_FORMS": "1",
                "branches-0-screenshots-INITIAL_FORMS": "1",
                "branches-0-screenshots-MIN_NUM_FORMS": "0",
                "branches-0-screenshots-MAX_NUM_FORMS": "1000",
                "branches-0-screenshots-0-id": reference_screenshot.id,
                "branches-0-screenshots-0-description": "Updated control screenshot",
                "branches-0-screenshots-0-image": dummy_image,
                "branches-1-id": treatment_branch.id,
                "branches-1-name": "Treatment",
                "branches-1-description": "Treatment Description",
                "branches-1-ratio": 3,
                "branches-1-feature-value-TOTAL_FORMS": "2",
                "branches-1-feature-value-INITIAL_FORMS": "2",
                "branches-1-feature-value-MIN_NUM_FORMS": "0",
                "branches-1-feature-value-MAX_NUM_FORMS": "1000",
                "branches-1-feature-value-0-id": (
                    treatment_branch_feature_config1_value.id
                ),
                "branches-1-feature-value-0-value": json.dumps(
                    {"treatment-feature-1-key": "treatment-feature-1-value"}
                ),
                "branches-1-feature-value-1-id": (
                    treatment_branch_feature_config2_value.id
                ),
                "branches-1-feature-value-1-value": json.dumps(
                    {"treatment-feature-2-key": "treatment-feature-2-value"}
                ),
                "branches-1-screenshots-TOTAL_FORMS": "1",
                "branches-1-screenshots-INITIAL_FORMS": "1",
                "branches-1-screenshots-MIN_NUM_FORMS": "0",
                "branches-1-screenshots-MAX_NUM_FORMS": "1000",
                "branches-1-screenshots-0-id": treatment_screenshot.id,
                "branches-1-screenshots-0-description": "Updated treatment screenshot",
                "branches-1-screenshots-0-image": dummy_image,
                "is_localized": True,
                "localizations": json.dumps({"localization-key": "localization-value"}),
                "branch_id": reference_branch.id,
            },
            files={
                "branches-0-screenshots-0-image": dummy_image,
                "branches-1-screenshots-0-image": dummy_image,
            },
            request=self.request,
        )

        self.assertTrue(form.is_valid(), form.errors)

        form.save()
        experiment = NimbusExperiment.objects.get(id=experiment.id)

        self.assertEqual(
            set(experiment.feature_configs.all()), {feature_config1, feature_config2}
        )
        self.assertFalse(experiment.equal_branch_ratio)
        self.assertFalse(experiment.is_rollout)
        self.assertTrue(experiment.prevent_pref_conflicts)
        self.assertTrue(experiment.warn_feature_schema)
        self.assertTrue(experiment.is_localized)
        self.assertEqual(
            experiment.localizations,
            json.dumps({"localization-key": "localization-value"}),
        )
        self.assertEqual(experiment.reference_branch.name, "Control")
        self.assertEqual(experiment.reference_branch.slug, "control")
        self.assertEqual(experiment.reference_branch.description, "Control Description")
        self.assertEqual(experiment.reference_branch.ratio, 2)
        self.assertEqual(
            experiment.reference_branch.feature_values.filter(
                feature_config=feature_config1
            )
            .get()
            .value,
            json.dumps({"control-feature1-key": "control-feature-1-value"}),
        )
        self.assertEqual(
            experiment.reference_branch.feature_values.filter(
                feature_config=feature_config2
            )
            .get()
            .value,
            json.dumps({"control-feature-2-key": "control-feature-2-value"}),
        )

        treatment_branch = experiment.treatment_branches[0]
        self.assertEqual(treatment_branch.name, "Treatment")
        self.assertEqual(treatment_branch.slug, "treatment")
        self.assertEqual(treatment_branch.description, "Treatment Description")
        self.assertEqual(treatment_branch.ratio, 3)
        self.assertEqual(
            treatment_branch.feature_values.filter(feature_config=feature_config1)
            .get()
            .value,
            json.dumps({"treatment-feature-1-key": "treatment-feature-1-value"}),
        )
        self.assertEqual(
            treatment_branch.feature_values.filter(feature_config=feature_config2)
            .get()
            .value,
            json.dumps({"treatment-feature-2-key": "treatment-feature-2-value"}),
        )

        self.assertEqual(
            experiment.reference_branch.screenshots.get(
                id=reference_screenshot.id
            ).description,
            "Updated control screenshot",
        )
        self.assertEqual(
            experiment.treatment_branches[0]
            .screenshots.get(id=treatment_screenshot.id)
            .description,
            "Updated treatment screenshot",
        )

    def test_create_screenshot(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
        )
        branch = experiment.reference_branch
        branch.screenshots.all().delete()
        form = BranchScreenshotCreateForm(
            data={"branch_id": branch.id},
            instance=experiment,
            request=self.request,
        )
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.assertEqual(branch.screenshots.count(), 1)


class TestBranchScreenshotDeleteForm(RequestFormTestCase):
    def test_branches_form_saves_branches(self):
        application = NimbusExperiment.Application.DESKTOP
        feature_config1 = NimbusFeatureConfigFactory.create(application=application)
        feature_config2 = NimbusFeatureConfigFactory.create(application=application)
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=application,
            feature_configs=[feature_config1, feature_config2],
            equal_branch_ratio=False,
            is_localized=False,
            is_rollout=False,
            localizations=None,
            prevent_pref_conflicts=False,
            warn_feature_schema=False,
        )
        experiment.branches.all().delete()
        experiment.changes.all().delete()

        reference_branch = NimbusBranchFactory.create(experiment=experiment, ratio=1)
        treatment_branch = NimbusBranchFactory.create(experiment=experiment, ratio=1)
        experiment.reference_branch = reference_branch
        experiment.save()

        reference_branch_feature_config1_value = reference_branch.feature_values.filter(
            feature_config=feature_config1
        ).get()
        reference_branch_feature_config2_value = reference_branch.feature_values.filter(
            feature_config=feature_config2
        ).get()
        treatment_branch_feature_config1_value = treatment_branch.feature_values.filter(
            feature_config=feature_config1
        ).get()
        treatment_branch_feature_config2_value = treatment_branch.feature_values.filter(
            feature_config=feature_config2
        ).get()

        reference_screenshot = reference_branch.screenshots.first()
        treatment_screenshot = treatment_branch.screenshots.first()
        deleteable_screenshot = reference_branch.screenshots.create()

        # Create a valid in-memory PNG image
        image_bytes = io.BytesIO()
        image = Image.new("RGB", (10, 10), color="red")
        image.save(image_bytes, format="PNG")
        image_bytes.seek(0)
        dummy_image = SimpleUploadedFile(
            "test.png", image_bytes.read(), content_type="image/png"
        )

        form = BranchScreenshotDeleteForm(
            instance=experiment,
            data={
                "feature_configs": [feature_config1.id, feature_config2.id],
                "equal_branch_ratio": False,
                "is_rollout": False,
                "prevent_pref_conflicts": True,
                "warn_feature_schema": True,
                "branches-TOTAL_FORMS": "2",
                "branches-INITIAL_FORMS": "2",
                "branches-MIN_NUM_FORMS": "0",
                "branches-MAX_NUM_FORMS": "1000",
                "branches-0-id": reference_branch.id,
                "branches-0-name": "Control",
                "branches-0-description": "Control Description",
                "branches-0-ratio": 2,
                "branches-0-feature-value-TOTAL_FORMS": "2",
                "branches-0-feature-value-INITIAL_FORMS": "2",
                "branches-0-feature-value-MIN_NUM_FORMS": "0",
                "branches-0-feature-value-MAX_NUM_FORMS": "1000",
                "branches-0-feature-value-0-id": (
                    reference_branch_feature_config1_value.id
                ),
                "branches-0-feature-value-0-value": json.dumps(
                    {"control-feature1-key": "control-feature-1-value"}
                ),
                "branches-0-feature-value-1-id": (
                    reference_branch_feature_config2_value.id
                ),
                "branches-0-feature-value-1-value": json.dumps(
                    {"control-feature-2-key": "control-feature-2-value"}
                ),
                "branches-0-screenshots-TOTAL_FORMS": "1",
                "branches-0-screenshots-INITIAL_FORMS": "1",
                "branches-0-screenshots-MIN_NUM_FORMS": "0",
                "branches-0-screenshots-MAX_NUM_FORMS": "1000",
                "branches-0-screenshots-0-id": reference_screenshot.id,
                "branches-0-screenshots-0-description": "Updated control screenshot",
                "branches-0-screenshots-0-image": dummy_image,
                "branches-1-id": treatment_branch.id,
                "branches-1-name": "Treatment",
                "branches-1-description": "Treatment Description",
                "branches-1-ratio": 3,
                "branches-1-feature-value-TOTAL_FORMS": "2",
                "branches-1-feature-value-INITIAL_FORMS": "2",
                "branches-1-feature-value-MIN_NUM_FORMS": "0",
                "branches-1-feature-value-MAX_NUM_FORMS": "1000",
                "branches-1-feature-value-0-id": (
                    treatment_branch_feature_config1_value.id
                ),
                "branches-1-feature-value-0-value": json.dumps(
                    {"treatment-feature-1-key": "treatment-feature-1-value"}
                ),
                "branches-1-feature-value-1-id": (
                    treatment_branch_feature_config2_value.id
                ),
                "branches-1-feature-value-1-value": json.dumps(
                    {"treatment-feature-2-key": "treatment-feature-2-value"}
                ),
                "branches-1-screenshots-TOTAL_FORMS": "1",
                "branches-1-screenshots-INITIAL_FORMS": "1",
                "branches-1-screenshots-MIN_NUM_FORMS": "0",
                "branches-1-screenshots-MAX_NUM_FORMS": "1000",
                "branches-1-screenshots-0-id": treatment_screenshot.id,
                "branches-1-screenshots-0-description": "Updated treatment screenshot",
                "branches-1-screenshots-0-image": dummy_image,
                "is_localized": True,
                "localizations": json.dumps({"localization-key": "localization-value"}),
                "screenshot_id": deleteable_screenshot.id,
            },
            files={
                "branches-0-screenshots-0-image": dummy_image,
                "branches-1-screenshots-0-image": dummy_image,
            },
            request=self.request,
        )

        self.assertTrue(form.is_valid(), form.errors)

        form.save()
        experiment = NimbusExperiment.objects.get(id=experiment.id)

        self.assertEqual(
            set(experiment.feature_configs.all()), {feature_config1, feature_config2}
        )
        self.assertFalse(experiment.equal_branch_ratio)
        self.assertFalse(experiment.is_rollout)
        self.assertTrue(experiment.prevent_pref_conflicts)
        self.assertTrue(experiment.warn_feature_schema)
        self.assertTrue(experiment.is_localized)
        self.assertEqual(
            experiment.localizations,
            json.dumps({"localization-key": "localization-value"}),
        )
        self.assertEqual(experiment.reference_branch.name, "Control")
        self.assertEqual(experiment.reference_branch.slug, "control")
        self.assertEqual(experiment.reference_branch.description, "Control Description")
        self.assertEqual(experiment.reference_branch.ratio, 2)
        self.assertEqual(
            experiment.reference_branch.feature_values.filter(
                feature_config=feature_config1
            )
            .get()
            .value,
            json.dumps({"control-feature1-key": "control-feature-1-value"}),
        )
        self.assertEqual(
            experiment.reference_branch.feature_values.filter(
                feature_config=feature_config2
            )
            .get()
            .value,
            json.dumps({"control-feature-2-key": "control-feature-2-value"}),
        )

        treatment_branch = experiment.treatment_branches[0]
        self.assertEqual(treatment_branch.name, "Treatment")
        self.assertEqual(treatment_branch.slug, "treatment")
        self.assertEqual(treatment_branch.description, "Treatment Description")
        self.assertEqual(treatment_branch.ratio, 3)
        self.assertEqual(
            treatment_branch.feature_values.filter(feature_config=feature_config1)
            .get()
            .value,
            json.dumps({"treatment-feature-1-key": "treatment-feature-1-value"}),
        )
        self.assertEqual(
            treatment_branch.feature_values.filter(feature_config=feature_config2)
            .get()
            .value,
            json.dumps({"treatment-feature-2-key": "treatment-feature-2-value"}),
        )

        self.assertEqual(
            experiment.reference_branch.screenshots.get(
                id=reference_screenshot.id
            ).description,
            "Updated control screenshot",
        )
        self.assertEqual(
            experiment.treatment_branches[0]
            .screenshots.get(id=treatment_screenshot.id)
            .description,
            "Updated treatment screenshot",
        )

    def test_delete_screenshot(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
        )
        branch = experiment.reference_branch
        screenshot = branch.screenshots.create(description="To be deleted")
        form = BranchScreenshotDeleteForm(
            data={"screenshot_id": screenshot.id},
            instance=experiment,
            request=self.request,
        )
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.assertFalse(branch.screenshots.filter(id=screenshot.id).exists())

    def test_initial_value_empty_when_instance_value_is_none_or_empty_dict(self):
        instance_none = NimbusBranchFeatureValue(value=None)
        form_none = NimbusBranchFeatureValueForm(instance=instance_none)
        self.assertEqual(form_none.fields["value"].initial, "")

        instance_empty = NimbusBranchFeatureValue(value={})
        form_empty = NimbusBranchFeatureValueForm(instance=instance_empty)
        self.assertEqual(form_empty.fields["value"].initial, "")

    def test_initial_value_not_overridden_for_existing_value(self):
        instance = NimbusBranchFeatureValue(value={"foo": "bar"})
        form = NimbusBranchFeatureValueForm(instance=instance)
        self.assertIsNone(form.fields["value"].initial)


class TestBranchFeatureValueForm(RequestFormTestCase):
    def test_schemas(self):
        feature_with_schema = NimbusFeatureConfigFactory.create(
            name="with-schema",
            application=NimbusExperiment.Application.IOS,
            schemas=[NimbusVersionedSchemaFactory.build(version=None)],
        )

        feature_without_schema = NimbusFeatureConfigFactory.create(
            name="without-schema",
            application=NimbusExperiment.Application.IOS,
            schemas=[
                NimbusVersionedSchemaFactory.build(version=None, schema=None),
            ],
        )

        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=NimbusExperiment.Application.IOS,
            feature_configs=[feature_with_schema, feature_without_schema],
        )

        forms = {
            fv.feature_config.slug: NimbusBranchFeatureValueForm(instance=fv)
            for fv in experiment.reference_branch.feature_values.all()
        }

        self.assertEqual(
            json.loads(forms["with-schema"].fields["value"].widget.attrs["data-schema"]),
            {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "description": (
                    "Fake schema that matches NimbusBranchFactory feature_value factory"
                ),
                "type": "object",
                "patternProperties": {"^.*$": {"type": "string"}},
                "additionalProperties": False,
            },
        )
        self.assertNotIn(
            "data-schema", forms["without-schema"].fields["value"].widget.attrs
        )


class TestFeaturesViewForm(RequestFormTestCase):
    def setUp(self):
        super().setUp()
        self.applications = [
            NimbusExperiment.Application.DESKTOP,
            NimbusExperiment.Application.IOS,
            NimbusExperiment.Application.FENIX,
        ]
        self.feature_configs = {}
        for app in self.applications:
            self.feature_configs[app] = NimbusFeatureConfigFactory.create(
                slug=f"feature-{app.value}",
                name=f"Feature {app.value}",
                application=app,
            )

    def test_features_view_default_fields_are_firefox_desktop(self):
        NimbusExperimentFactory.create(owner=self.user)
        form = FeaturesForm()
        application = form.fields["application"]
        feature_configs = form.fields["feature_configs"]
        self.assertEqual(application.initial, NimbusExperiment.Application.DESKTOP.value)
        self.assertIsNone(feature_configs.initial)

    @parameterized.expand(
        [
            (
                NimbusExperiment.Application.DESKTOP,
                [NimbusExperiment.Application.IOS, NimbusExperiment.Application.FENIX],
            ),
            (
                NimbusExperiment.Application.IOS,
                [
                    NimbusExperiment.Application.DESKTOP,
                    NimbusExperiment.Application.FENIX,
                ],
            ),
            (
                NimbusExperiment.Application.FENIX,
                [NimbusExperiment.Application.IOS, NimbusExperiment.Application.DESKTOP],
            ),
        ]
    )
    def test_features_view_feature_config_field_updates_correctly(
        self, expected_app, excluded_apps
    ):
        NimbusExperimentFactory.create(owner=self.user)
        form = FeaturesForm(data={"application": expected_app})
        feature_configs = form.fields["feature_configs"]

        self.assertIn(
            (
                self.feature_configs[expected_app].id,
                f"{self.feature_configs[expected_app].name} - {self.feature_configs[expected_app].description}",  # noqa
            ),
            feature_configs.choices,
        )
        self.assertNotIn(
            (
                self.feature_configs[excluded_apps[0]].id,
                f"{self.feature_configs[excluded_apps[0]].name} - {self.feature_configs[excluded_apps[0]].description}",  # noqa
            ),
            feature_configs.choices,
        )
        self.assertNotIn(
            (
                self.feature_configs[excluded_apps[1]].id,
                f"{self.feature_configs[excluded_apps[1]].name} - {self.feature_configs[excluded_apps[1]].description}",  # noqa
            ),
            feature_configs.choices,
        )
