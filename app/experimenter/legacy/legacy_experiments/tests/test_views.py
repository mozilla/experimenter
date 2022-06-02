import json
import random
import re
from urllib.parse import urlencode

import mock
from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse

from experimenter.base.models import Country, Locale
from experimenter.base.tests.factories import CountryFactory, LocaleFactory
from experimenter.legacy.bugzilla.tests.mixins import MockBugzillaTasksMixin
from experimenter.legacy.legacy_experiments.forms import (
    RADIO_NO,
    RADIO_YES,
    NormandyIdForm,
)
from experimenter.legacy.legacy_experiments.models import Experiment
from experimenter.legacy.legacy_experiments.tests.factories import ExperimentFactory
from experimenter.legacy.legacy_experiments.views import (
    ExperimentFormMixin,
    ExperimentOrderingForm,
)
from experimenter.openidc.tests.factories import UserFactory


class TestExperimentListView(TestCase):
    def test_list_view_lists_experiments_with_default_order_no_archived(self):
        user_email = "user@example.com"

        # Archived experiment is ommitted
        ExperimentFactory.create_with_status(Experiment.STATUS_DRAFT, archived=True)

        for i in range(3):
            ExperimentFactory.create_with_status(
                random.choice(Experiment.STATUS_CHOICES)[0]
            )

        experiments = (
            Experiment.objects.all()
            .filter(archived=False)
            .order_by(ExperimentOrderingForm.ORDERING_CHOICES[0][0])
        )

        response = self.client.get(
            reverse("home"), **{settings.OPENIDC_EMAIL_HEADER: user_email}
        )

        context = response.context[0]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(context["experiments"]), list(experiments))

    def test_list_view_shows_all_including_archived(self):
        user_email = "user@example.com"

        # Archived experiment is included
        ExperimentFactory.create_with_status(Experiment.STATUS_DRAFT, archived=True)

        for i in range(3):
            ExperimentFactory.create_with_status(
                random.choice(Experiment.STATUS_CHOICES)[0]
            )

        experiments = Experiment.objects.all()

        response = self.client.get(
            "{url}?{params}".format(
                url=reverse("home"), params=urlencode({"archived": True})
            ),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        context = response.context[0]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(context["experiments"]), set(experiments))

    def test_list_view_filters_and_orders_experiments(self):
        user_email = "user@example.com"

        ordering = "latest_change"
        filtered_channel = Experiment.CHANNEL_CHOICES[1][0]
        filtered_owner = UserFactory.create()
        filtered_status = Experiment.STATUS_DRAFT
        filtered_types = (Experiment.TYPE_PREF, Experiment.TYPE_GENERIC)
        filtered_version = Experiment.VERSION_CHOICES[1][0]

        for i in range(3):
            for filtered_type in filtered_types:
                ExperimentFactory.create_with_status(
                    firefox_channel=filtered_channel,
                    firefox_min_version=filtered_version,
                    owner=filtered_owner,
                    target_status=filtered_status,
                    type=filtered_type,
                )

        for i in range(3):
            ExperimentFactory.create_with_status(
                random.choice(Experiment.STATUS_CHOICES)[0]
            )

        filtered_ordered_experiments = Experiment.objects.filter(
            firefox_channel=filtered_channel,
            firefox_min_version=filtered_version,
            owner=filtered_owner,
            status=filtered_status,
            type__in=filtered_types,
        ).order_by(ordering)

        response = self.client.get(
            "{url}?{params}".format(
                url=reverse("home"),
                params=urlencode(
                    {
                        "firefox_channel": filtered_channel,
                        "firefox_version": filtered_version,
                        "ordering": ordering,
                        "owner": filtered_owner.id,
                        "status": filtered_status,
                        "type": filtered_types,
                    },
                    True,
                ),
            ),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        context = response.context[0]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(context["experiments"]), list(filtered_ordered_experiments))

    def test_list_view_total_experiments_count(self):
        user_email = "user@example.com"

        number_of_experiments = settings.EXPERIMENTS_PAGINATE_BY + 1
        for i in range(number_of_experiments):
            ExperimentFactory.create_with_status(
                random.choice(Experiment.STATUS_CHOICES)[0]
            )

        response = self.client.get(
            reverse("home"), **{settings.OPENIDC_EMAIL_HEADER: user_email}
        )
        self.assertEqual(response.status_code, 200)
        html = response.content.decode("utf-8")
        total_count_regex = re.compile(rf"{number_of_experiments}\s+Deliveries")
        self.assertTrue(total_count_regex.search(html))

        # Go to page 2, and the total shouldn't change.
        response = self.client.get(
            "{url}?{params}".format(url=reverse("home"), params=urlencode({"page": 2})),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200)
        html = response.content.decode("utf-8")
        self.assertTrue(total_count_regex.search(html))
        self.assertTrue("Page 2" in html)


class TestExperimentFormMixin(TestCase):
    def test_get_form_kwargs_adds_request(self):
        class BaseTestView(object):
            def __init__(self, request):
                self.request = request

            def get_form_kwargs(self):
                return {}

        class TestView(ExperimentFormMixin, BaseTestView):
            pass

        request = mock.Mock()
        view = TestView(request=request)
        form_kwargs = view.get_form_kwargs()
        self.assertEqual(form_kwargs["request"], request)

    @mock.patch("experimenter.legacy.legacy_experiments.views.reverse")
    def test_get_success_url_returns_next_url_if_action_is_continue(self, mock_reverse):
        class BaseTestView(object):
            def __init__(self, request, instance):
                self.request = request
                self.object = instance

        class TestView(ExperimentFormMixin, BaseTestView):
            next_view_name = "next-test-view"

        def mock_reverser(url_name, *args, **kwargs):
            return url_name

        mock_reverse.side_effect = mock_reverser

        instance = mock.Mock()
        instance.slug = "slug"

        request = mock.Mock()
        request.POST = {"action": "continue"}

        view = TestView(request, instance)
        redirect = view.get_success_url()
        self.assertEqual(redirect, TestView.next_view_name)
        mock_reverse.assert_called_with(
            TestView.next_view_name, kwargs={"slug": instance.slug}
        )

    @mock.patch("experimenter.legacy.legacy_experiments.views.reverse")
    def test_get_success_url_returns_detail_url_if_action_is_empty(self, mock_reverse):
        class BaseTestView(object):
            def __init__(self, request, instance):
                self.request = request
                self.object = instance

        class TestView(ExperimentFormMixin, BaseTestView):
            next_view_name = "next-test-view"

        def mock_reverser(url_name, *args, **kwargs):
            return url_name

        mock_reverse.side_effect = mock_reverser

        instance = mock.Mock()
        instance.slug = "slug"

        request = mock.Mock()
        request.POST = {}

        view = TestView(request, instance)
        redirect = view.get_success_url()
        self.assertEqual(redirect, "experiments-detail")
        mock_reverse.assert_called_with(
            "experiments-detail", kwargs={"slug": instance.slug}
        )


class TestExperimentCreateView(TestCase):
    def test_view_creates_experiment(self):
        user = UserFactory.create()
        user_email = user.email

        ds_issue_url = "https://jira.example.com/browse/DS-123"
        bugzilla_url = "https://bugzilla.example.com/show_bug.cgi?id=123"
        data = {
            "action": "continue",
            "type": Experiment.TYPE_PREF,
            "name": "A new experiment!",
            "short_description": "Let us learn new things",
            "public_description": "Public Description",
            "data_science_issue_url": ds_issue_url,
            "feature_bugzilla_url": bugzilla_url,
            "related_work": "Designs: https://www.example.com/myproject/",
            "owner": user.id,
            "analysis_owner": user.id,
        }

        with self.settings(
            BUGZILLA_HOST="https://bugzilla.example.com",
            DS_ISSUE_HOST="https://jira.example.com/browse/",
        ):
            response = self.client.post(
                reverse("experiments-create"),
                data,
                **{settings.OPENIDC_EMAIL_HEADER: user_email},
            )

        self.assertEqual(response.status_code, 302)

        experiment = Experiment.objects.get()
        self.assertEqual(experiment.status, experiment.STATUS_DRAFT)
        self.assertEqual(experiment.name, data["name"])

        self.assertEqual(experiment.changes.count(), 1)

        change = experiment.changes.get()

        self.assertEqual(change.changed_by, user)
        self.assertEqual(change.old_status, None)
        self.assertEqual(change.new_status, experiment.STATUS_DRAFT)


@override_settings(
    BUGZILLA_HOST="https://bugzilla.example.com/",
    DS_ISSUE_HOST="https://jira.example.com/browse/",
)
class TestExperimentOverviewUpdateView(TestCase):
    def test_view_saves_experiment(self):
        user = UserFactory.create()
        user_email = user.email
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT, proposed_enrollment=1, proposed_duration=2
        )

        ds_url = "{base}DS-123".format(base=settings.DS_ISSUE_HOST)
        bug_url = "{base}show_bug.cgi?id=123".format(base=settings.BUGZILLA_HOST)

        data = {
            "action": "continue",
            "type": Experiment.TYPE_PREF,
            "name": "A new name!",
            "short_description": "A new description!",
            "public_description": "Public Description",
            "data_science_issue_url": ds_url,
            "feature_bugzilla_url": bug_url,
            "related_work": "Designs: https://www.example.com/myproject/",
            "owner": user.id,
            "analysis_owner": user.id,
        }

        response = self.client.post(
            reverse("experiments-overview-update", kwargs={"slug": experiment.slug}),
            data,
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 302)

        experiment = Experiment.objects.get()
        self.assertEqual(experiment.name, data["name"])
        self.assertEqual(experiment.short_description, data["short_description"])
        self.assertEqual(experiment.analysis_owner, user)

        self.assertEqual(experiment.changes.count(), 2)

        change = experiment.changes.latest()

        self.assertEqual(change.changed_by, user)
        self.assertEqual(change.old_status, experiment.STATUS_DRAFT)
        self.assertEqual(change.new_status, experiment.STATUS_DRAFT)


class TestExperimentTimelinePopulationUpdateView(TestCase):
    def test_get_view_returns_context(self):
        user_email = "user@example.com"

        experiment = ExperimentFactory.create_with_status(Experiment.STATUS_DRAFT)

        response = self.client.get(
            reverse("experiments-timeline-pop-update", kwargs={"slug": experiment.slug}),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        context = response.context[0]

        countries = list(
            Country.objects.extra(select={"label": "name", "value": "id"}).values(
                "label", "value"
            )
        )

        locales = list(
            Locale.objects.extra(select={"label": "name", "value": "id"}).values(
                "label", "value"
            )
        )

        self.assertEqual(json.loads(context["countries"]), countries)
        self.assertEqual(json.loads(context["locales"]), locales)


class TestExperimentDesignUpdateView(TestCase):
    def test_page_loads(self):
        user_email = "user@example.com"
        experiment = ExperimentFactory.create()
        response = self.client.get(
            reverse("experiments-design-update", kwargs={"slug": experiment.slug}),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200)


class TestExperimentObjectivesUpdateView(TestCase):
    def test_view_saves_experiment(self):
        user_email = "user@example.com"
        experiment = ExperimentFactory.create_with_status(Experiment.STATUS_DRAFT)

        data = {
            "action": "continue",
            "objectives": "Some new objectives!",
            "analysis": "Some new analysis!",
            "survey_required": RADIO_NO,
        }

        response = self.client.post(
            reverse("experiments-objectives-update", kwargs={"slug": experiment.slug}),
            data,
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 302)

        experiment = Experiment.objects.get()
        self.assertEqual(experiment.objectives, data["objectives"])
        self.assertEqual(experiment.analysis, data["analysis"])
        self.assertFalse(experiment.survey_required, data["survey_required"])

        self.assertEqual(experiment.changes.count(), 2)

        change = experiment.changes.latest()

        self.assertEqual(change.changed_by.email, user_email)
        self.assertEqual(change.old_status, experiment.STATUS_DRAFT)
        self.assertEqual(change.new_status, experiment.STATUS_DRAFT)


class TestExperimentRisksUpdateView(TestCase):
    def test_view_saves_experiment(self):
        user_email = "user@example.com"
        experiment = ExperimentFactory.create_with_status(Experiment.STATUS_DRAFT)

        data = {
            "risk_partner_related": RADIO_YES,
            "risk_brand": RADIO_YES,
            "risk_fast_shipped": RADIO_YES,
            "risk_confidential": RADIO_YES,
            "risk_release_population": RADIO_YES,
            "risk_revenue": RADIO_YES,
            "risk_data_category": RADIO_YES,
            "risk_external_team_impact": RADIO_YES,
            "risk_telemetry_data": RADIO_YES,
            "risk_ux": RADIO_YES,
            "risk_security": RADIO_YES,
            "risk_revision": RADIO_YES,
            "risk_technical": RADIO_YES,
            "risk_technical_description": "It's complicated",
            "risks": "There are some risks",
            "testing": "Always be sure to test!",
            "test_builds": "Latest Build",
            "qa_status": "Green",
        }

        response = self.client.post(
            reverse("experiments-risks-update", kwargs={"slug": experiment.slug}),
            data,
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 302)

        experiment = Experiment.objects.get()

        self.assertTrue(experiment.risk_partner_related)
        self.assertTrue(experiment.risk_brand)
        self.assertTrue(experiment.risk_fast_shipped)
        self.assertTrue(experiment.risk_confidential)
        self.assertTrue(experiment.risk_release_population)
        self.assertTrue(experiment.risk_technical)
        self.assertEqual(
            experiment.risk_technical_description, data["risk_technical_description"]
        )
        self.assertEqual(experiment.risks, data["risks"])
        self.assertEqual(experiment.testing, data["testing"])
        self.assertEqual(experiment.test_builds, data["test_builds"])
        self.assertEqual(experiment.qa_status, data["qa_status"])

        self.assertEqual(experiment.changes.count(), 2)

        change = experiment.changes.latest()

        self.assertEqual(change.changed_by.email, user_email)
        self.assertEqual(change.old_status, experiment.STATUS_DRAFT)
        self.assertEqual(change.new_status, experiment.STATUS_DRAFT)


class TestResultsUpdateView(TestCase):
    def test_view_saves_experiment(self):
        user_email = "user@example.com"
        experiment = ExperimentFactory.create_with_status(Experiment.STATUS_COMPLETE)

        data = {
            "results_url": "https://example.com",
            "results_lessons_learned": "Many lessons were learned.",
        }

        response = self.client.post(
            reverse("experiments-results-update", kwargs={"slug": experiment.slug}),
            data,
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 302)

        experiment = Experiment.objects.get()

        self.assertEqual(experiment.results_url, "https://example.com")
        self.assertEqual(experiment.results_lessons_learned, "Many lessons were learned.")


class TestExperimentDetailView(TestCase):
    def test_view_renders_correctly(self):
        user_email = "user@example.com"
        experiment = ExperimentFactory.create_with_status(Experiment.STATUS_DRAFT)

        response = self.client.get(
            reverse("experiments-detail", kwargs={"slug": experiment.slug}),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "experiments/detail_draft.html")
        self.assertTemplateUsed(response, "experiments/detail_base.html")

    def test_view_renders_locales_correctly(self):
        user_email = "user@example.com"
        experiment = ExperimentFactory.create_with_status(Experiment.STATUS_DRAFT)
        experiment.locales.add(LocaleFactory(code="yy", name="Why"))
        experiment.locales.add(LocaleFactory(code="xx", name="Xess"))
        response = self.client.get(
            reverse("experiments-detail", kwargs={"slug": experiment.slug}),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200)

    def test_view_renders_countries_correctly(self):
        user_email = "user@example.com"
        experiment = ExperimentFactory.create_with_status(Experiment.STATUS_DRAFT)
        experiment.countries.add(CountryFactory(code="YY", name="Wazoo"))
        experiment.countries.add(CountryFactory(code="XX", name="Xanadu"))
        response = self.client.get(
            reverse("experiments-detail", kwargs={"slug": experiment.slug}),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200)

    def test_includes_normandy_id_form_in_context(self):
        user_email = "user@example.com"
        experiment = ExperimentFactory.create_with_status(Experiment.STATUS_SHIP)
        response = self.client.get(
            reverse("experiments-detail", kwargs={"slug": experiment.slug}),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertTrue(
            isinstance(response.context[0]["normandy_id_form"], NormandyIdForm)
        )

    def test_includes_bound_normandy_id_form_if_GET_param_set(self):
        user_email = "user@example.com"
        experiment = ExperimentFactory.create_with_status(Experiment.STATUS_SHIP)
        bad_normandy_id = "abc"
        detail_url = reverse("experiments-detail", kwargs={"slug": experiment.slug})
        response = self.client.get(
            f"{detail_url}?normandy_id={bad_normandy_id}",
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        normandy_form = response.context[0]["normandy_id_form"]
        self.assertTrue(isinstance(normandy_form, NormandyIdForm))
        self.assertEqual(normandy_form.data["normandy_id"], bad_normandy_id)
        self.assertFalse(normandy_form.is_valid())


class TestExperimentStatusUpdateView(MockBugzillaTasksMixin, TestCase):
    def test_view_updates_status_and_redirects(self):
        user_email = "user@example.com"
        experiment = ExperimentFactory.create_with_status(Experiment.STATUS_DRAFT)

        new_status = experiment.STATUS_REVIEW

        response = self.client.post(
            reverse("experiments-status-update", kwargs={"slug": experiment.slug}),
            {"status": new_status},
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertRedirects(
            response,
            reverse("experiments-detail", kwargs={"slug": experiment.slug}),
            fetch_redirect_response=False,
        )
        updated_experiment = Experiment.objects.get(slug=experiment.slug)
        self.assertEqual(updated_experiment.status, new_status)

    def test_view_redirects_on_failure(self):
        user_email = "user@example.com"
        original_status = Experiment.STATUS_DRAFT
        experiment = ExperimentFactory.create_with_status(original_status)

        response = self.client.post(
            reverse("experiments-status-update", kwargs={"slug": experiment.slug}),
            {"status": Experiment.STATUS_COMPLETE},
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertRedirects(
            response,
            reverse("experiments-detail", kwargs={"slug": experiment.slug}),
            fetch_redirect_response=False,
        )
        updated_experiment = Experiment.objects.get(slug=experiment.slug)
        self.assertEqual(updated_experiment.status, original_status)


class TestExperimentReviewUpdateView(TestCase):
    def test_view_updates_reviews_and_redirects(self):
        user_email = "user@example.com"
        experiment = ExperimentFactory.create_with_status(Experiment.STATUS_REVIEW)

        data = {
            "review_science": True,
            "review_engineering": True,
            "review_qa_requested": True,
            "review_intent_to_ship": True,
            "review_bugzilla": True,
            "review_advisory": True,
            "review_legal": True,
            "review_ux": True,
            "review_security": True,
            "review_vp": True,
            "review_data_steward": True,
            "review_comms": True,
            "review_impacted_teams": True,
        }

        response = self.client.post(
            reverse("experiments-review-update", kwargs={"slug": experiment.slug}),
            data,
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertRedirects(
            response,
            reverse("experiments-detail", kwargs={"slug": experiment.slug}),
            fetch_redirect_response=False,
        )

        experiment = Experiment.objects.get()

        self.assertTrue(experiment.review_science)
        self.assertTrue(experiment.review_legal)
        self.assertTrue(experiment.review_ux)
        self.assertTrue(experiment.review_security)

        change = experiment.changes.latest()

        self.assertEqual(change.changed_by.email, user_email)
        self.assertEqual(change.old_status, experiment.STATUS_REVIEW)
        self.assertEqual(change.new_status, experiment.STATUS_REVIEW)


class TestExperimentCommentCreateView(TestCase):
    def test_view_creates_comment_redirects_to_detail_page(self):
        user_email = "user@example.com"
        experiment = ExperimentFactory.create_with_status(Experiment.STATUS_DRAFT)

        section = experiment.SECTION_OBJECTIVES
        text = "Hello!"

        response = self.client.post(
            reverse("experiments-comment-create", kwargs={"slug": experiment.slug}),
            {"experiment": experiment.id, "section": section, "text": text},
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertRedirects(
            response,
            "{url}#{section}-comments".format(
                url=reverse("experiments-detail", kwargs={"slug": experiment.slug}),
                section=section,
            ),
            fetch_redirect_response=False,
        )
        comment = experiment.comments.sections[section][0]
        self.assertEqual(comment.text, text)
        self.assertEqual(comment.created_by.email, user_email)

    def test_view_redirects_to_detail_page_when_form_is_invalid(self):
        user_email = "user@example.com"
        experiment = ExperimentFactory.create_with_status(Experiment.STATUS_DRAFT)

        section = "invalid section"
        text = ""

        response = self.client.post(
            reverse("experiments-comment-create", kwargs={"slug": experiment.slug}),
            {"experiment": experiment.id, "section": section, "text": text},
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertRedirects(
            response,
            reverse("experiments-detail", kwargs={"slug": experiment.slug}),
            fetch_redirect_response=False,
        )


class TestExperimentArchiveUpdateView(MockBugzillaTasksMixin, TestCase):
    def test_view_flips_archive_bool_and_redirects(self):
        user_email = "user@example.com"
        experiment = ExperimentFactory.create(archived=False)

        response = self.client.post(
            reverse("experiments-archive-update", kwargs={"slug": experiment.slug}),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        self.assertRedirects(
            response,
            reverse("experiments-detail", kwargs={"slug": experiment.slug}),
            fetch_redirect_response=False,
        )

        experiment = Experiment.objects.get(id=experiment.id)

        self.assertTrue(self.mock_tasks_update_bug_resolution.delay.assert_called_once)
        self.assertTrue(experiment.archived)


class TestExperimentSubscribedUpdateView(TestCase):
    def test_view_flips_subscribed_bool_and_redirects(self):
        user = UserFactory()
        experiment = ExperimentFactory.create()
        self.assertFalse(user in experiment.subscribers.all())

        response = self.client.post(
            reverse("experiments-subscribed-update", kwargs={"slug": experiment.slug}),
            **{settings.OPENIDC_EMAIL_HEADER: user.email},
        )

        self.assertRedirects(
            response,
            reverse("experiments-detail", kwargs={"slug": experiment.slug}),
            fetch_redirect_response=False,
        )

        experiment = Experiment.objects.get(id=experiment.id)
        self.assertTrue(user in experiment.subscribers.all())


class TestExperimentNormandyUpdateView(TestCase):
    def test_valid_recipe_id_updates_experiment_status(self):
        user_email = "user@example.com"
        experiment = ExperimentFactory.create_with_status(Experiment.STATUS_SHIP)
        normandy_id = 123

        response = self.client.post(
            reverse("experiments-normandy-update", kwargs={"slug": experiment.slug}),
            {"normandy_id": normandy_id},
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertRedirects(
            response,
            reverse("experiments-detail", kwargs={"slug": experiment.slug}),
            fetch_redirect_response=False,
        )

        experiment = Experiment.objects.get(id=experiment.id)
        self.assertEqual(experiment.normandy_id, normandy_id)
        self.assertEqual(experiment.status, Experiment.STATUS_ACCEPTED)

    def test_invalid_recipe_id_redirects_to_detail(self):
        user_email = "user@example.com"
        experiment = ExperimentFactory.create_with_status(Experiment.STATUS_SHIP)
        normandy_id = "abc"

        response = self.client.post(
            reverse("experiments-normandy-update", kwargs={"slug": experiment.slug}),
            {"normandy_id": normandy_id},
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        detail_url = reverse("experiments-detail", kwargs={"slug": experiment.slug})
        self.assertRedirects(
            response,
            f"{detail_url}?normandy_id={normandy_id}",
            fetch_redirect_response=False,
        )

    def test_invalid_other_recipe_ids_redirects_to_detail(self):
        user_email = "user@example.com"
        experiment = ExperimentFactory.create_with_status(Experiment.STATUS_SHIP)
        normandy_id = "432"
        other_normandy_ids = "abc"

        response = self.client.post(
            reverse("experiments-normandy-update", kwargs={"slug": experiment.slug}),
            {"normandy_id": normandy_id, "other_normandy_ids": other_normandy_ids},
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )

        detail_url = reverse("experiments-detail", kwargs={"slug": experiment.slug})

        self.assertRedirects(
            response,
            f"{detail_url}?normandy_id={normandy_id}"
            f"&other_normandy_ids={other_normandy_ids}",
            fetch_redirect_response=False,
        )


class TestNimbusUIView(TestCase):
    def test_page_loads(self):
        user_email = "user@example.com"
        response = self.client.get(
            reverse("nimbus-list"),
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertEqual(response.status_code, 200)


class Test404View(TestCase):
    def test_404(self):
        user_email = "user@example.com"
        response = self.client.get(
            # test path should be a string that doesn't match any existing url patterns
            # or django will attempt to 301 and append a slash before 404ing
            "/invalid/",
            **{settings.OPENIDC_EMAIL_HEADER: user_email},
        )
        self.assertTemplateUsed(response, "nimbus/404.html")
        self.assertEqual(response.status_code, 404)
