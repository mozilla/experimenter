from django.test import RequestFactory, TestCase
from django.urls import reverse

from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tests.factories import (
    NimbusDocumentationLinkFactory,
    NimbusExperimentFactory,
)
from experimenter.nimbus_ui_new.constants import NimbusUIConstants
from experimenter.nimbus_ui_new.forms import (
    DocumentationLinkCreateForm,
    DocumentationLinkDeleteForm,
    DraftToPreviewForm,
    DraftToReviewForm,
    MetricsForm,
    NimbusExperimentCreateForm,
    OverviewForm,
    PreviewToDraftForm,
    PreviewToReviewForm,
    QAStatusForm,
    ReviewToDraftForm,
    SignoffForm,
    SubscribeForm,
    TakeawaysForm,
    UnsubscribeForm,
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

    def test_draft_to_preview_form(self):
        form = DraftToPreviewForm(data={}, instance=self.experiment, request=self.request)
        self.assertTrue(form.is_valid(), form.errors)

        experiment = form.save()
        self.assertEqual(experiment.status, NimbusExperiment.Status.PREVIEW)
        self.assertEqual(experiment.status_next, NimbusExperiment.Status.PREVIEW)
        self.assertEqual(experiment.publish_status, NimbusExperiment.PublishStatus.IDLE)

        changelog = experiment.changes.latest("changed_on")
        self.assertEqual(changelog.changed_by, self.user)
        self.assertIn("launched experiment to Preview", changelog.message)

    def test_draft_to_review_form(self):
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

    def test_review_to_draft_form(self):
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
