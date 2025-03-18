from unittest.mock import patch

from django.test import RequestFactory, TestCase
from django.urls import reverse

from experimenter.base.tests.factories import (
    CountryFactory,
    LanguageFactory,
    LocaleFactory,
)
from experimenter.experiments.models import (
    NimbusExperiment,
    NimbusExperimentBranchThroughExcluded,
    NimbusExperimentBranchThroughRequired,
)
from experimenter.experiments.tests.factories import (
    NimbusDocumentationLinkFactory,
    NimbusExperimentFactory,
)
from experimenter.kinto.tasks import (
    nimbus_check_kinto_push_queue_by_collection,
    nimbus_synchronize_preview_experiments_in_kinto,
)
from experimenter.nimbus_ui_new.constants import NimbusUIConstants
from experimenter.nimbus_ui_new.forms import (
    AudienceForm,
    DocumentationLinkCreateForm,
    DocumentationLinkDeleteForm,
    DraftToPreviewForm,
    DraftToReviewForm,
    MetricsForm,
    NimbusExperimentCloneForm,
    NimbusExperimentCreateForm,
    OverviewForm,
    PreviewToDraftForm,
    PreviewToReviewForm,
    QAStatusForm,
    ReviewToApproveForm,
    ReviewToDraftForm,
    ReviewToRejectForm,
    SignoffForm,
    SubscribeForm,
    TakeawaysForm,
    ToggleArchiveForm,
    UnsubscribeForm,
    UpdateCloneSlugForm,
)
from experimenter.openidc.tests.factories import UserFactory
from experimenter.outcomes import Outcomes
from experimenter.outcomes.tests import mock_valid_outcomes
from experimenter.projects.tests.factories import ProjectFactory
from experimenter.segments import Segments
from experimenter.segments.tests.mock_segments import mock_get_segments


class RequestFormTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory.create(email="dev@example.com")
        request_factory = RequestFactory()
        self.request = request_factory.get(reverse("nimbus-new-create"))
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


class TestNimbusExperimentCloneForm(RequestFormTestCase):
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
        form = NimbusExperimentCloneForm(
            data, parent_slug=parent_experiment.slug, request=self.request
        )
        self.assertTrue(form.is_valid())

        cloned_experiment = form.save()

        self.assertEqual(cloned_experiment.owner, self.user)
        self.assertEqual(cloned_experiment.name, "Cloned Experiment")
        self.assertEqual(cloned_experiment.slug, "cloned-experiment")
        self.assertEqual(
            cloned_experiment.application, NimbusExperiment.Application.DESKTOP
        )

        changelog_message = form.get_changelog_message()
        self.assertEqual(changelog_message, f"{self.user} cloned Original Experiment")

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
        form = NimbusExperimentCloneForm(
            data, parent_slug=parent_experiment.slug, request=self.request
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
        form = NimbusExperimentCloneForm(
            data, parent_slug=parent_experiment.slug, request=self.request
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
    def setUp(self):
        super().setUp()
        self.experiment = NimbusExperimentFactory.create(
            name="Test Experiment",
            owner=self.user,
            qa_signoff=False,
            vp_signoff=False,
            legal_signoff=False,
        )

    def test_signoff_form_valid(self):
        data = {
            "qa_signoff": True,
            "vp_signoff": True,
            "legal_signoff": False,
        }
        form = SignoffForm(data=data, instance=self.experiment, request=self.request)
        self.assertTrue(form.is_valid(), form.errors)

        experiment = form.save()
        self.assertTrue(experiment.qa_signoff)
        self.assertTrue(experiment.vp_signoff)
        self.assertFalse(experiment.legal_signoff)

    def test_signoff_form_saves_to_changelog(self):
        """Test that saving the form also creates an entry in the changelog."""
        data = {
            "qa_signoff": True,
            "vp_signoff": True,
            "legal_signoff": True,
        }
        form = SignoffForm(data=data, instance=self.experiment, request=self.request)
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
    def setUp(self):
        super().setUp()
        self.experiment = NimbusExperimentFactory.create(
            name="Test Experiment",
            owner=self.user,
            qa_signoff=False,
            vp_signoff=False,
            legal_signoff=False,
        )

    def test_subscribe_form_adds_subscriber(self):
        form = SubscribeForm(instance=self.experiment, data={}, request=self.request)
        self.assertTrue(form.is_valid())
        form.save()
        self.assertIn(self.request.user, self.experiment.subscribers.all())
        changelog = self.experiment.changes.latest("changed_on")
        self.assertEqual(changelog.changed_by, self.user)
        self.assertIn("dev@example.com added subscriber", changelog.message)

    def test_unsubscribe_form_removes_subscriber(self):
        self.experiment.subscribers.add(self.request.user)
        form = UnsubscribeForm(instance=self.experiment, data={}, request=self.request)
        self.assertTrue(form.is_valid())
        form.save()
        self.assertNotIn(self.request.user, self.experiment.subscribers.all())
        changelog = self.experiment.changes.latest("changed_on")
        self.assertEqual(changelog.changed_by, self.user)
        self.assertIn("dev@example.com removed subscriber", changelog.message)


class TestLaunchForms(RequestFormTestCase):
    def setUp(self):
        super().setUp()
        self.experiment = NimbusExperimentFactory.create()

        self.mock_preview_task = patch.object(
            nimbus_synchronize_preview_experiments_in_kinto, "apply_async"
        ).start()
        self.mock_push_task = patch.object(
            nimbus_check_kinto_push_queue_by_collection, "apply_async"
        ).start()
        self.mock_allocate_bucket_range = patch.object(
            NimbusExperiment, "allocate_bucket_range"
        ).start()

        self.addCleanup(patch.stopall)

    def test_draft_to_preview_form(self):
        self.experiment.status = NimbusExperiment.Status.DRAFT
        self.experiment.status_next = None
        self.experiment.publish_status = NimbusExperiment.PublishStatus.IDLE
        self.experiment.save()
        form = DraftToPreviewForm(data={}, instance=self.experiment, request=self.request)
        self.assertTrue(form.is_valid(), form.errors)

        experiment = form.save()
        self.assertEqual(experiment.status, NimbusExperiment.Status.PREVIEW)
        self.assertEqual(experiment.status_next, NimbusExperiment.Status.PREVIEW)
        self.assertEqual(experiment.publish_status, NimbusExperiment.PublishStatus.IDLE)

        changelog = experiment.changes.latest("changed_on")
        self.assertEqual(changelog.changed_by, self.user)
        self.assertIn("launched experiment to Preview", changelog.message)
        self.mock_preview_task.assert_called_once_with(countdown=5)
        self.mock_allocate_bucket_range.assert_called_once()

    def test_draft_to_review_form(self):
        self.experiment.status = NimbusExperiment.Status.DRAFT
        self.experiment.status_next = None
        self.experiment.publish_status = NimbusExperiment.PublishStatus.IDLE
        self.experiment.save()
        form = DraftToReviewForm(data={}, instance=self.experiment, request=self.request)
        self.assertTrue(form.is_valid(), form.errors)

        experiment = form.save()
        self.assertEqual(experiment.status, NimbusExperiment.Status.DRAFT)
        self.assertEqual(experiment.status_next, NimbusExperiment.Status.LIVE)
        self.assertEqual(experiment.publish_status, NimbusExperiment.PublishStatus.REVIEW)

        changelog = experiment.changes.latest("changed_on")
        self.assertEqual(changelog.changed_by, self.user)
        self.assertIn("requested launch without Preview", changelog.message)

    def test_preview_to_review_form(self):
        self.experiment.status = NimbusExperiment.Status.PREVIEW
        self.experiment.status_next = NimbusExperiment.Status.PREVIEW
        self.experiment.publish_status = NimbusExperiment.PublishStatus.IDLE
        self.experiment.save()

        form = PreviewToReviewForm(
            data={}, instance=self.experiment, request=self.request
        )
        self.assertTrue(form.is_valid(), form.errors)

        experiment = form.save()
        self.assertEqual(experiment.status, NimbusExperiment.Status.DRAFT)
        self.assertEqual(experiment.status_next, NimbusExperiment.Status.LIVE)
        self.assertEqual(experiment.publish_status, NimbusExperiment.PublishStatus.REVIEW)

        changelog = experiment.changes.latest("changed_on")
        self.assertEqual(changelog.changed_by, self.user)
        self.assertIn("requested launch from Preview", changelog.message)

    def test_preview_to_draft_form(self):
        self.experiment.status = NimbusExperiment.Status.PREVIEW
        self.experiment.status_next = NimbusExperiment.Status.PREVIEW
        self.experiment.publish_status = NimbusExperiment.PublishStatus.IDLE
        self.experiment.save()

        form = PreviewToDraftForm(data={}, instance=self.experiment, request=self.request)
        self.assertTrue(form.is_valid(), form.errors)

        experiment = form.save()
        self.assertEqual(experiment.status, NimbusExperiment.Status.DRAFT)
        self.assertEqual(experiment.status_next, NimbusExperiment.Status.DRAFT)
        self.assertEqual(experiment.publish_status, NimbusExperiment.PublishStatus.IDLE)

        changelog = experiment.changes.latest("changed_on")
        self.assertEqual(changelog.changed_by, self.user)
        self.assertIn("moved the experiment back to Draft", changelog.message)
        self.mock_preview_task.assert_called_once_with(countdown=5)

    def test_review_to_draft_form(self):
        self.experiment.status = NimbusExperiment.Status.DRAFT
        self.experiment.status_next = NimbusExperiment.Status.LIVE
        self.experiment.publish_status = NimbusExperiment.PublishStatus.REVIEW
        self.experiment.save()

        form = ReviewToDraftForm(data={}, instance=self.experiment, request=self.request)
        self.assertTrue(form.is_valid(), form.errors)

        experiment = form.save()
        self.assertEqual(experiment.status, NimbusExperiment.Status.DRAFT)
        self.assertEqual(experiment.status_next, NimbusExperiment.Status.DRAFT)
        self.assertEqual(experiment.publish_status, NimbusExperiment.PublishStatus.IDLE)

        changelog = experiment.changes.latest("changed_on")
        self.assertEqual(changelog.changed_by, self.user)
        self.assertIn("cancelled the review", changelog.message)

    def test_review_to_approve_form(self):
        self.experiment.status = NimbusExperiment.Status.DRAFT
        self.experiment.status_next = NimbusExperiment.Status.LIVE
        self.experiment.publish_status = NimbusExperiment.PublishStatus.REVIEW
        self.experiment.save()

        form = ReviewToApproveForm(
            data={}, instance=self.experiment, request=self.request
        )
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

    def test_review_to_reject_form_with_reason(self):
        self.experiment.status = NimbusExperiment.Status.DRAFT
        self.experiment.status_next = NimbusExperiment.Status.LIVE
        self.experiment.publish_status = NimbusExperiment.PublishStatus.REVIEW
        self.experiment.save()

        form = ReviewToRejectForm(
            data={"changelog_message": "Needs more work."},
            instance=self.experiment,
            request=self.request,
        )
        self.assertTrue(form.is_valid(), form.errors)

        experiment = form.save()
        self.assertEqual(experiment.status, NimbusExperiment.Status.DRAFT)
        self.assertEqual(experiment.status_next, None)
        self.assertEqual(experiment.publish_status, NimbusExperiment.PublishStatus.IDLE)

        changelog = experiment.changes.latest("changed_on")
        self.assertEqual(changelog.changed_by, self.user)
        self.assertIn(
            f"{self.user} rejected the review with reason: Needs more work.",
            changelog.message,
        )


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
            instance=experiment, data={}, request=self.request
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
            data={"link_id": documentation_link.id},
            request=self.request,
        )

        self.assertTrue(form.is_valid())

        experiment = form.save()

        self.assertEqual(experiment.documentation_links.all().count(), 0)


class TestAudienceForm(RequestFormTestCase):
    def test_valid_form_saves(self):
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
        experiment = NimbusExperimentFactory(
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            application=NimbusExperiment.Application.DESKTOP,
            firefox_min_version=NimbusExperiment.Version.NO_VERSION,
            population_percent=0.0,
            proposed_duration=0,
            proposed_enrollment=0,
            proposed_release_date=None,
            targeting_config_slug=NimbusExperiment.TargetingConfig.NO_TARGETING,
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
                "excluded_experiments_branches": [excluded.branch_choices()[0][0]],
                "firefox_max_version": NimbusExperiment.Version.FIREFOX_84,
                "firefox_min_version": NimbusExperiment.Version.FIREFOX_83,
                "is_sticky": True,
                "languages": [language.id],
                "locales": [locale.id],
                "population_percent": 10,
                "proposed_duration": 120,
                "proposed_enrollment": 42,
                "required_experiments_branches": [required.branch_choices()[0][0]],
                "targeting_config_slug": (NimbusExperiment.TargetingConfig.FIRST_RUN),
                "total_enrolled_clients": 100,
            },
            request=self.request,
        )

        self.assertEqual(experiment.changes.count(), 0)
        self.assertTrue(form.is_valid(), form.errors)
        experiment = form.save()

        self.assertEqual(experiment.changes.count(), 1)
        self.assertEqual(experiment.channel, NimbusExperiment.Channel.BETA)
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
        experiment = NimbusExperimentFactory(
            channel=NimbusExperiment.Channel.NO_CHANNEL,
            application=NimbusExperiment.Application.DESKTOP,
            firefox_min_version=NimbusExperiment.Version.NO_VERSION,
            population_percent=0.0,
            proposed_duration=0,
            proposed_enrollment=0,
            proposed_release_date=None,
            targeting_config_slug=NimbusExperiment.TargetingConfig.NO_TARGETING,
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
                "excluded_experiments_branches": [excluded.branch_choices()[0][0]],
                "firefox_max_version": NimbusExperiment.Version.FIREFOX_84,
                "firefox_min_version": NimbusExperiment.Version.FIREFOX_83,
                "is_sticky": True,
                "languages": [language.id],
                "locales": [locale.id],
                "population_percent": 10,
                "proposed_duration": 120,
                "proposed_enrollment": 42,
                "required_experiments_branches": [required.branch_choices()[0][0]],
                "targeting_config_slug": (NimbusExperiment.TargetingConfig.FIRST_RUN),
                "total_enrolled_clients": 100,
            },
            request=self.request,
        )

        self.assertFalse(form.is_valid(), form.errors)
        self.assertIn("excluded_experiments_branches", form.errors)
        self.assertIn("required_experiments_branches", form.errors)
