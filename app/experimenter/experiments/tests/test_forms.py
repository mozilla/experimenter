import datetime
import decimal
import json

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.utils import timezone
from faker import Factory as FakerFactory
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from experimenter.experiments.forms import (
    BugzillaURLField,
    ChangeLogMixin,
    CustomModelMultipleChoiceField,
    ExperimentArchiveForm,
    ExperimentCommentForm,
    ExperimentObjectivesForm,
    ExperimentOverviewForm,
    ExperimentReviewForm,
    ExperimentRisksForm,
    ExperimentStatusForm,
    ExperimentSubscribedForm,
    ExperimentResultsForm,
    JSONField,
    NormandyIdForm,
    ExperimentTimelinePopulationForm,
    ExperimentOrderingForm,
)
from experimenter.experiments.models import Experiment
from experimenter.base.tests.factories import CountryFactory, LocaleFactory
from experimenter.experiments.tests.factories import ExperimentFactory, UserFactory
from experimenter.bugzilla.tests.mixins import MockBugzillaMixin
from experimenter.experiments.tests.mixins import MockTasksMixin, MockRequestMixin

from experimenter.notifications.models import Notification


faker = FakerFactory.create()


class TestJSONField(TestCase):

    def test_jsonfield_accepts_valid_json(self):
        valid_json = json.dumps({"a": True, 2: ["b", 3, 4.0]})
        field = JSONField()
        cleaned = field.clean(valid_json)
        self.assertEqual(cleaned, valid_json)

    def test_jsonfield_rejects_invalid_json(self):
        invalid_json = "{this isnt valid"
        field = JSONField()

        with self.assertRaises(ValidationError):
            field.clean(invalid_json)


@override_settings(BUGZILLA_HOST="https://bugzilla.mozilla.org")
class TestBugzillaURLField(TestCase):

    def test_accepts_bugzilla_url(self):
        field = BugzillaURLField()
        bugzilla_url = "{base}/show_bug.cgi?id=123".format(base=settings.BUGZILLA_HOST)
        cleaned = field.clean(bugzilla_url)
        self.assertEqual(cleaned, bugzilla_url)

    def test_rejects_non_show_bug_bugzilla_url(self):
        field = BugzillaURLField()
        bugzilla_url = "{base}/123".format(base=settings.BUGZILLA_HOST)

        with self.assertRaises(ValidationError):
            field.clean(bugzilla_url)

    def test_rejects_non_bugzilla_url(self):
        field = BugzillaURLField()

        with self.assertRaises(ValidationError):
            field.clean("www.example.com")


class TestChangeLogMixin(MockRequestMixin, TestCase):

    def test_mixin_creates_change_log_with_request_user_on_save(self):

        class TestForm(ChangeLogMixin, forms.ModelForm):

            class Meta:
                model = Experiment
                fields = ("name",)

        data = ExperimentFactory.attributes()
        form = TestForm(request=self.request, data=data)

        self.assertTrue(form.is_valid())
        experiment = form.save()

        self.assertEqual(experiment.changes.count(), 1)

        change = experiment.changes.get()
        self.assertEqual(change.changed_by, self.user)

    def test_mixin_sets_old_and_new_status(self):
        old_status = Experiment.STATUS_DRAFT
        new_status = Experiment.STATUS_REVIEW
        experiment = ExperimentFactory.create_with_status(old_status)

        self.assertEqual(experiment.changes.count(), 1)

        class TestForm(ChangeLogMixin, forms.ModelForm):

            class Meta:
                model = Experiment
                fields = ("status",)

        form = TestForm(
            request=self.request, data={"status": new_status}, instance=experiment
        )
        self.assertTrue(form.is_valid())

        form.save()

        self.assertEqual(experiment.changes.count(), 2)

        change = experiment.changes.latest()

        self.assertEqual(change.old_status, old_status)
        self.assertEqual(change.new_status, new_status)

    def test_changelog_not_produced_when_no_change(self):

        experiment = ExperimentFactory.create_with_status(
            target_status=Experiment.STATUS_DRAFT
        )
        num_of_changes = experiment.changes.count()

        class TestForm(ChangeLogMixin, forms.ModelForm):

            class Meta:
                model = Experiment
                fields = ("name",)

        form = TestForm(
            request=self.request, data={"name": experiment.name}, instance=experiment
        )
        self.assertTrue(form.is_valid())
        form.save()
        experiment = Experiment.objects.get(id=experiment.id)
        self.assertEqual(experiment.changes.count(), num_of_changes)

    def test_changelog_values(self):
        experiment = Experiment()
        experiment.save()

        country1 = CountryFactory(code="CA", name="Canada")
        country2 = CountryFactory(code="US", name="United States")
        locale1 = LocaleFactory(code="da", name="Danish")
        locale2 = LocaleFactory(code="de", name="German")

        data = {
            "proposed_start_date": timezone.now().date(),
            "proposed_duration": 20,
            "population_percent": "10",
            "firefox_min_version": "56.0",
            "firefox_max_version": "58.0",
            "firefox_channel": Experiment.CHANNEL_BETA,
            "client_matching": "en-us",
            "platform": Experiment.PLATFORM_WINDOWS,
            "locales": [locale1, locale2],
            "countries": [country1, country2],
        }

        form = ExperimentTimelinePopulationForm(
            request=self.request, data=data, instance=experiment
        )
        self.assertTrue(form.is_valid())
        experiment = form.save()
        latest_changes = experiment.changes.latest()

        expected_data = {
            "locales": {
                "new_value": ["da", "de"],
                "old_value": None,
                "display_name": "Locales",
            },
            "platform": {
                "new_value": "All Windows",
                "old_value": None,
                "display_name": "Platform",
            },
            "countries": {
                "new_value": ["CA", "US"],
                "old_value": None,
                "display_name": "Countries",
            },
            "client_matching": {
                "new_value": "en-us",
                "old_value": None,
                "display_name": "Population Filtering",
            },
            "firefox_channel": {
                "new_value": "Beta",
                "old_value": None,
                "display_name": "Firefox Channel",
            },
            "proposed_duration": {
                "new_value": 20,
                "old_value": None,
                "display_name": "Proposed Total Duration (days)",
            },
            "population_percent": {
                "new_value": "10.0000",
                "old_value": None,
                "display_name": "Population Percentage",
            },
            "firefox_min_version": {
                "new_value": "56.0",
                "old_value": None,
                "display_name": "Firefox Min Version",
            },
            "firefox_max_version": {
                "new_value": "58.0",
                "old_value": None,
                "display_name": "Firefox Max Version",
            },
            "proposed_start_date": {
                "new_value": timezone.now().date().strftime("%Y-%m-%d"),
                "old_value": None,
                "display_name": "Proposed Start Date",
            },
        }

        self.assertEqual(expected_data, latest_changes.changed_values)


@override_settings(BUGZILLA_HOST="https://bugzilla.mozilla.org")
class TestExperimentOverviewForm(MockRequestMixin, TestCase):

    def setUp(self):
        super().setUp()

        bug_url = "https://bugzilla.mozilla.org/show_bug.cgi?id=123"
        self.related_exp = ExperimentFactory.create()

        self.data = {
            "type": Experiment.TYPE_PREF,
            "name": "A new experiment!",
            "short_description": "Let us learn new things",
            "data_science_bugzilla_url": bug_url,
            "owner": self.user.id,
            "analysis_owner": self.user.id,
            "engineering_owner": "Lisa the Engineer",
            "public_name": "A new public experiment!",
            "public_description": "Let us learn new public things",
            "related_to": [self.related_exp],
            "feature_bugzilla_url": bug_url,
            "related_work": "Designs: https://www.example.com/myproject/",
        }

    def test_minimum_required_fields_for_experiment(self):
        bug_url = "https://bugzilla.mozilla.org/show_bug.cgi?id=123"

        data = {
            "type": Experiment.TYPE_PREF,
            "owner": self.user.id,
            "name": "A new experiment!",
            "short_description": "Let us learn new things",
            "data_science_bugzilla_url": bug_url,
            "public_name": "Public Name",
            "public_description": "Public Description",
        }
        form = ExperimentOverviewForm(request=self.request, data=data)
        self.assertTrue(form.is_valid())

        experiment = form.save()

        self.assertEqual(experiment.owner, self.user)
        self.assertEqual(experiment.status, experiment.STATUS_DRAFT)
        self.assertEqual(experiment.name, data["name"])
        self.assertEqual(experiment.slug, "a-new-experiment")
        self.assertEqual(experiment.short_description, data["short_description"])
        self.assertEqual(experiment.public_name, data["public_name"])
        self.assertEqual(experiment.public_description, data["public_description"])
        self.assertEqual(experiment.changes.count(), 1)

    def test_minimum_required_fields_for_rollout(self):
        data = {
            "type": Experiment.TYPE_ROLLOUT,
            "owner": self.user.id,
            "name": "A new experiment!",
            "short_description": "Let us learn new things",
        }
        form = ExperimentOverviewForm(request=self.request, data=data)
        self.assertTrue(form.is_valid())

        experiment = form.save()

        self.assertEqual(experiment.owner, self.user)
        self.assertEqual(experiment.status, experiment.STATUS_DRAFT)
        self.assertEqual(experiment.name, self.data["name"])
        self.assertEqual(experiment.slug, "a-new-experiment")
        self.assertEqual(experiment.short_description, self.data["short_description"])
        self.assertEqual(experiment.changes.count(), 1)

    def test_form_creates_experiment(self):
        form = ExperimentOverviewForm(request=self.request, data=self.data)
        self.assertTrue(form.is_valid())
        experiment = form.save()

        self.assertEqual(experiment.owner, self.user)
        self.assertEqual(experiment.engineering_owner, self.data["engineering_owner"])
        self.assertEqual(experiment.status, experiment.STATUS_DRAFT)
        self.assertEqual(experiment.name, self.data["name"])
        self.assertEqual(experiment.slug, "a-new-experiment")
        self.assertEqual(experiment.short_description, self.data["short_description"])
        self.assertTrue(self.related_exp in experiment.related_to.all())

        self.assertEqual(experiment.changes.count(), 1)
        change = experiment.changes.get()
        self.assertEqual(change.old_status, None)
        self.assertEqual(change.new_status, experiment.status)
        self.assertEqual(change.changed_by, self.request.user)

    def test_empty_slug_raises_error(self):
        self.data["name"] = "#"

        form = ExperimentOverviewForm(request=self.request, data=self.data)
        self.assertFalse(form.is_valid())

    def test_unique_name_with_same_slug_raises_error(self):
        ExperimentFactory.create(slug="slug")
        self.data["name"] = "slug#"

        form = ExperimentOverviewForm(request=self.request, data=self.data)
        self.assertFalse(form.is_valid())

    def test_bugzilla_url_required_for_non_rollout(self):
        self.data["type"] = Experiment.TYPE_PREF
        del self.data["data_science_bugzilla_url"]

        form = ExperimentOverviewForm(request=self.request, data=self.data)
        self.assertFalse(form.is_valid())

    def test_bugzilla_url_optional_for_rollout(self):
        self.data["type"] = Experiment.TYPE_ROLLOUT
        del self.data["data_science_bugzilla_url"]

        form = ExperimentOverviewForm(request=self.request, data=self.data)
        self.assertTrue(form.is_valid())

    def test_invalid_bugzilla_url(self):
        self.data["data_science_bugzilla_url"] = "https://example.com/notbugzilla"

        form = ExperimentOverviewForm(request=self.request, data=self.data)
        self.assertFalse(form.is_valid())


class TestExperimentTimelinePopulationForm(MockRequestMixin, TestCase):

    def setUp(self):
        super().setUp()

        self.data = {
            "proposed_start_date": timezone.now().date(),
            "proposed_duration": 20,
            "proposed_enrollment": 10,
            "population_percent": "10.0",
            "firefox_channel": Experiment.CHANNEL_NIGHTLY,
            "firefox_min_version": "67.0",
            "firefox_max_version": "69.0",
            "locales": [],
            "countries": [],
            "platform": Experiment.PLATFORM_WINDOWS,
            "client_matching": "en-us",
        }

    def test_no_fields_required(self):
        experiment = ExperimentFactory.create()
        data = {
            "proposed_start_date": "",
            "proposed_duration": "",
            "proposed_enrollment": "",
            "population_percent": "",
            "firefox_channel": "",
            "firefox_min_version": "",
            "firefox_max_version": "",
            "locales": [],
            "countries": [],
            "platform": "",
            "client_matching": "",
        }
        form = ExperimentTimelinePopulationForm(
            request=self.request, data=data, instance=experiment
        )
        self.assertTrue(form.is_valid())
        experiment = form.save()

    def test_form_saves_experiment_timeline_population_data(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT, countries=[], locales=[]
        )
        form = ExperimentTimelinePopulationForm(
            request=self.request, data=self.data, instance=experiment
        )

        self.assertEqual(experiment.changes.count(), 1)

        experiment = form.save()

        self.assertEqual(experiment.proposed_start_date, self.data["proposed_start_date"])
        self.assertEqual(experiment.proposed_duration, self.data["proposed_duration"])
        self.assertEqual(experiment.proposed_enrollment, self.data["proposed_enrollment"])
        self.assertEqual(experiment.population_percent, decimal.Decimal("10.000"))
        self.assertEqual(experiment.firefox_channel, self.data["firefox_channel"])
        self.assertEqual(experiment.firefox_min_version, self.data["firefox_min_version"])
        self.assertEqual(experiment.firefox_max_version, self.data["firefox_max_version"])
        self.assertEqual(experiment.platform, self.data["platform"])
        self.assertEqual(experiment.client_matching, self.data["client_matching"])

        self.assertEqual(experiment.changes.count(), 2)

    def test_form_saves_rollout_timeline_population_data(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT,
            type=Experiment.TYPE_ROLLOUT,
            countries=[],
            locales=[],
        )

        data = {
            "proposed_start_date": timezone.now().date(),
            "proposed_duration": 20,
            "rollout_playbook": Experiment.ROLLOUT_PLAYBOOK_LOW_RISK,
            "firefox_channel": Experiment.CHANNEL_NIGHTLY,
            "firefox_min_version": "67.0",
            "firefox_max_version": "69.0",
            "locales": [],
            "countries": [],
        }

        form = ExperimentTimelinePopulationForm(
            request=self.request, data=data, instance=experiment
        )

        self.assertEqual(experiment.changes.count(), 1)

        experiment = form.save()

        self.assertEqual(experiment.proposed_start_date, data["proposed_start_date"])
        self.assertEqual(experiment.firefox_min_version, data["firefox_min_version"])
        self.assertEqual(experiment.firefox_max_version, data["firefox_max_version"])
        self.assertEqual(experiment.firefox_channel, data["firefox_channel"])
        self.assertEqual(experiment.population_percent, decimal.Decimal("25.000"))

        self.assertEqual(experiment.changes.count(), 2)

    def test_enrollment_must_be_less_or_equal_duration(self):
        self.data["proposed_enrollment"] = 2
        self.data["proposed_duration"] = 1

        form = ExperimentTimelinePopulationForm(request=self.request, data=self.data)
        self.assertFalse(form.is_valid())

    def test_large_duration_is_invalid(self):
        self.data["proposed_duration"] = Experiment.MAX_DURATION + 1

        form = ExperimentTimelinePopulationForm(request=self.request, data=self.data)
        self.assertFalse(form.is_valid())

    def test_large_enrollment_duration_is_invalid(self):
        self.data["proposed_enrollment"] = Experiment.MAX_DURATION + 1

        form = ExperimentTimelinePopulationForm(request=self.request, data=self.data)
        self.assertFalse(form.is_valid())

    def test_start_date_must_be_greater_or_equal_to_current_date(self):
        experiment = ExperimentFactory.create_with_status(Experiment.STATUS_DRAFT)
        self.data["proposed_start_date"] = timezone.now().date() - datetime.timedelta(
            days=1
        )

        form = ExperimentTimelinePopulationForm(
            request=self.request, data=self.data, instance=experiment
        )
        self.assertFalse(form.is_valid())

    def test_locales_choices(self):
        locale1 = LocaleFactory(code="sv-SE", name="Swedish")
        locale2 = LocaleFactory(code="fr", name="French")
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT, countries=[], locales=[]
        )
        form = ExperimentTimelinePopulationForm(
            request=self.request, data=self.data, instance=experiment
        )
        self.assertEqual(
            list(form.fields["locales"].choices),
            [
                (CustomModelMultipleChoiceField.ALL_KEY, "All locales"),
                (locale2.code, str(locale2)),
                (locale1.code, str(locale1)),
            ],
        )

    def test_locales_initials(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT, locales=[]
        )
        locale1 = LocaleFactory(code="sv-SE", name="Swedish")
        locale2 = LocaleFactory(code="fr", name="French")
        experiment.locales.add(locale1)
        experiment.locales.add(locale2)
        form = ExperimentTimelinePopulationForm(
            request=self.request, data=self.data, instance=experiment
        )
        self.assertEqual(form.initial["locales"], [locale2, locale1])

    def test_locales_initials_all_locales(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT, locales=[]
        )
        form = ExperimentTimelinePopulationForm(
            request=self.request, data=self.data, instance=experiment
        )
        self.assertEqual(
            form.initial["locales"], [CustomModelMultipleChoiceField.ALL_KEY]
        )

    def test_clean_locales(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT, num_variants=0
        )
        locale1 = LocaleFactory(code="sv-SE", name="Swedish")
        locale2 = LocaleFactory(code="fr", name="French")
        self.data["locales"] = [locale2.code, locale1.code]
        form = ExperimentTimelinePopulationForm(
            request=self.request, data=self.data, instance=experiment
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(set(form.cleaned_data["locales"]), set([locale2, locale1]))

    def test_clean_locales_all(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT, num_variants=0
        )
        locale1 = LocaleFactory(code="sv-SE", name="Swedish")
        locale2 = LocaleFactory(code="fr", name="French")
        self.data["locales"] = [
            locale2.code,
            CustomModelMultipleChoiceField.ALL_KEY,
            locale1.code,
        ]
        form = ExperimentTimelinePopulationForm(
            request=self.request, data=self.data, instance=experiment
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(list(form.cleaned_data["locales"]), [])

    def test_clean_unrecognized_locales(self):
        experiment = ExperimentFactory.create_with_status(Experiment.STATUS_DRAFT)
        self.data["locales"] = ["xxx"]
        form = ExperimentTimelinePopulationForm(
            request=self.request, data=self.data, instance=experiment
        )
        self.assertTrue(not form.is_valid())
        self.assertTrue(form.errors["locales"])

    def test_countries_choices(self):
        country1 = CountryFactory(code="SV", name="Sweden")
        country2 = CountryFactory(code="FR", name="France")

        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT, countries=[], locales=[]
        )
        form = ExperimentTimelinePopulationForm(
            request=self.request, data=self.data, instance=experiment
        )
        self.assertEqual(
            list(form.fields["countries"].choices),
            [
                (CustomModelMultipleChoiceField.ALL_KEY, "All countries"),
                (country2.code, str(country2)),
                (country1.code, str(country1)),
            ],
        )

    def test_countries_initials(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT, countries=[]
        )
        country1 = CountryFactory(code="SV", name="Sweden")
        country2 = CountryFactory(code="FR", name="France")
        experiment.countries.add(country1)
        experiment.countries.add(country2)
        form = ExperimentTimelinePopulationForm(
            request=self.request, data=self.data, instance=experiment
        )
        self.assertEqual(form.initial["countries"], [country2, country1])

    def test_countries_initials_all(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT, num_variants=0, countries=[]
        )
        form = ExperimentTimelinePopulationForm(
            request=self.request, data=self.data, instance=experiment
        )
        self.assertEqual(
            form.initial["countries"], [CustomModelMultipleChoiceField.ALL_KEY]
        )

    def test_clean_countries(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT, num_variants=0
        )
        country1 = CountryFactory(code="SV", name="Sweden")
        country2 = CountryFactory(code="FR", name="France")
        self.data["countries"] = [country1.code, country2.code]
        form = ExperimentTimelinePopulationForm(
            request=self.request, data=self.data, instance=experiment
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(
            # form.cleaned_data["countries"] is a QuerySet to exhaust it.
            list(form.cleaned_data["countries"]),
            [country2, country1],
        )

    def test_clean_countries_all(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT, num_variants=0
        )
        country1 = CountryFactory(code="SV", name="Sweden")
        country2 = CountryFactory(code="FR", name="France")
        self.data["countries"] = [
            country1.code,
            CustomModelMultipleChoiceField.ALL_KEY,
            country2.code,
        ]
        form = ExperimentTimelinePopulationForm(
            request=self.request, data=self.data, instance=experiment
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(list(form.cleaned_data["countries"]), [])

    def test_clean_unrecognized_countries(self):
        experiment = ExperimentFactory.create_with_status(Experiment.STATUS_DRAFT)
        self.data["countries"] = ["xxx"]
        form = ExperimentTimelinePopulationForm(
            request=self.request, data=self.data, instance=experiment
        )
        self.assertTrue(not form.is_valid())
        self.assertTrue(form.errors["countries"])

    def test_form_is_invalid_if_population_percent_below_0(self):
        self.data["population_percent"] = "-1"
        form = ExperimentTimelinePopulationForm(request=self.request, data=self.data)
        self.assertFalse(form.is_valid())
        self.assertIn("population_percent", form.errors)

    def test_form_is_invalid_if_population_percent_above_100(self):
        self.data["population_percent"] = "101"
        form = ExperimentTimelinePopulationForm(request=self.request, data=self.data)
        self.assertFalse(form.is_valid())
        self.assertIn("population_percent", form.errors)

    def test_form_is_invalid_if_firefox_max_is_lower_than_min(self):
        self.data["firefox_min_version"] = "66.0"
        self.data["firefox_max_version"] = "64.0"
        form = ExperimentTimelinePopulationForm(request=self.request, data=self.data)
        self.assertFalse(form.is_valid())
        self.assertIn("firefox_max_version", form.errors)

    def test_form_is_valid_if_firefox_max_is_equal_to_min(self):
        self.data["firefox_min_version"] = "66.0"
        self.data["firefox_max_version"] = "66.0"
        form = ExperimentTimelinePopulationForm(request=self.request, data=self.data)
        self.assertTrue(form.is_valid())


class TestExperimentObjectivesForm(MockRequestMixin, TestCase):

    def test_no_fields_required(self):
        experiment = ExperimentFactory.create()
        form = ExperimentObjectivesForm(
            request=self.request, data={}, instance=experiment
        )
        self.assertTrue(form.is_valid())

    def test_form_saves_objectives(self):
        created_experiment = ExperimentFactory.create_with_status(Experiment.STATUS_DRAFT)
        self.assertEqual(created_experiment.changes.count(), 1)

        data = {
            "objectives": "The objective is to experiment!",
            "analysis": "Lets analyze the results!",
            "survey_required": True,
            "survey_urls": "example.com",
            "survey_instructions": "Here are the launch instructions.",
        }

        form = ExperimentObjectivesForm(
            request=self.request, data=data, instance=created_experiment
        )

        self.assertTrue(form.is_valid())
        experiment = form.save()

        self.assertEqual(experiment.objectives, data["objectives"])
        self.assertEqual(experiment.analysis, data["analysis"])
        self.assertTrue(experiment.survey_required)
        self.assertEqual(experiment.survey_urls, data["survey_urls"])
        self.assertEqual(experiment.survey_instructions, data["survey_instructions"])

        self.assertEqual(experiment.changes.count(), 2)


class TestExperimentRisksForm(MockRequestMixin, TestCase):

    valid_data = {
        "risk_partner_related": False,
        "risk_brand": True,
        "risk_fast_shipped": True,
        "risk_confidential": True,
        "risk_release_population": True,
        "risk_revenue": True,
        "risk_data_category": True,
        "risk_external_team_impact": True,
        "risk_telemetry_data": True,
        "risk_ux": True,
        "risk_security": True,
        "risk_revision": True,
        "risk_technical": True,
        "risk_technical_description": "It's complicated",
        "risks": "There are some risks",
        "testing": "Always be sure to test!",
        "test_builds": "Latest build",
        "qa_status": "It ain't easy being green",
    }

    def test_no_fields_required(self):
        experiment = ExperimentFactory.create()
        form = ExperimentRisksForm(request=self.request, data={}, instance=experiment)
        self.assertTrue(form.is_valid())

    def test_form_saves_risks(self):
        created_experiment = ExperimentFactory.create_with_status(Experiment.STATUS_DRAFT)
        self.assertEqual(created_experiment.changes.count(), 1)

        data = self.valid_data.copy()
        form = ExperimentRisksForm(
            request=self.request, data=data, instance=created_experiment
        )

        self.assertTrue(form.is_valid())

        experiment = form.save()
        self.assertFalse(experiment.risk_partner_related)
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


class TestExperimentResultsForm(MockRequestMixin, TestCase):

    def test_form_saves_results(self):
        experiment = ExperimentFactory.create()
        self.assertEqual(experiment.changes.count(), 0)
        data = {
            "results_url": "https://example.com",
            "results_initial": "Initially, all went well.",
            "results_lessons_learned": "Lessons were learned.",
        }

        form = ExperimentResultsForm(request=self.request, data=data, instance=experiment)

        self.assertTrue(form.is_valid())

        experiment = form.save()

        self.assertEqual(experiment.results_url, "https://example.com")
        self.assertEqual(experiment.results_initial, "Initially, all went well.")

        self.assertEqual(experiment.changes.count(), 1)


class TestExperimentReviewForm(
    MockRequestMixin, MockBugzillaMixin, MockTasksMixin, TestCase
):

    def test_form_saves_reviews(self):
        user = UserFactory.create()
        content_type = ContentType.objects.get_for_model(Experiment)
        experiment_model_permissions = Permission.objects.filter(
            content_type=content_type, codename__startswith="can_check"
        )
        for permission in experiment_model_permissions:
            user.user_permissions.add(permission)

        self.request.user = user

        experiment = ExperimentFactory.create_with_status(Experiment.STATUS_REVIEW)
        self.assertEqual(experiment.changes.count(), 2)

        self.assertFalse(experiment.review_science)
        self.assertFalse(experiment.review_engineering)
        self.assertFalse(experiment.review_qa_requested)
        self.assertFalse(experiment.review_intent_to_ship)
        self.assertFalse(experiment.review_bugzilla)
        self.assertFalse(experiment.review_qa)
        self.assertFalse(experiment.review_relman)
        self.assertFalse(experiment.review_advisory)
        self.assertFalse(experiment.review_legal)
        self.assertFalse(experiment.review_ux)
        self.assertFalse(experiment.review_security)
        self.assertFalse(experiment.review_vp)
        self.assertFalse(experiment.review_data_steward)
        self.assertFalse(experiment.review_comms)
        self.assertFalse(experiment.review_impacted_teams)

        data = {
            "review_science": True,
            "review_engineering": True,
            "review_qa_requested": True,
            "review_intent_to_ship": True,
            "review_bugzilla": True,
            "review_qa": True,
            "review_relman": True,
            "review_advisory": True,
            "review_legal": True,
            "review_ux": True,
            "review_security": True,
            "review_vp": True,
            "review_data_steward": True,
            "review_comms": True,
            "review_impacted_teams": True,
        }

        form = ExperimentReviewForm(request=self.request, data=data, instance=experiment)

        self.assertTrue(form.is_valid())
        experiment = form.save()

        self.assertTrue(experiment.review_science)
        self.assertTrue(experiment.review_engineering)
        self.assertTrue(experiment.review_qa_requested)
        self.assertTrue(experiment.review_intent_to_ship)
        self.assertTrue(experiment.review_bugzilla)
        self.assertTrue(experiment.review_qa)
        self.assertTrue(experiment.review_relman)
        self.assertTrue(experiment.review_advisory)
        self.assertTrue(experiment.review_legal)
        self.assertTrue(experiment.review_ux)
        self.assertTrue(experiment.review_security)
        self.assertTrue(experiment.review_vp)
        self.assertTrue(experiment.review_data_steward)
        self.assertTrue(experiment.review_comms)
        self.assertTrue(experiment.review_impacted_teams)

        self.assertEqual(experiment.changes.count(), 3)

    def test_added_reviews_property(self):
        experiment = ExperimentFactory.create_with_status(Experiment.STATUS_REVIEW)
        self.assertEqual(experiment.changes.count(), 2)

        data = {"review_bugzilla": True, "review_science": True}

        form = ExperimentReviewForm(request=self.request, data=data, instance=experiment)

        self.assertTrue(form.is_valid())
        experiment = form.save()

        self.assertEqual(len(form.added_reviews), 2)
        self.assertEqual(len(form.removed_reviews), 0)
        self.assertIn(form.fields["review_bugzilla"].label, form.added_reviews)
        self.assertIn(form.fields["review_science"].label, form.added_reviews)

        self.assertEqual(experiment.changes.count(), 3)

    def test_removed_reviews_property(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_REVIEW, review_bugzilla=True, review_science=True
        )

        self.assertEqual(experiment.changes.count(), 2)

        data = {"review_bugzilla": False, "review_science": False}

        form = ExperimentReviewForm(request=self.request, data=data, instance=experiment)

        self.assertTrue(form.is_valid())
        experiment = form.save()

        self.assertEqual(len(form.added_reviews), 0)
        self.assertEqual(len(form.removed_reviews), 2)
        self.assertIn(form.fields["review_bugzilla"].label, form.removed_reviews)
        self.assertIn(form.fields["review_science"].label, form.removed_reviews)

        self.assertEqual(experiment.changes.count(), 3)

    def test_required_reviews(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_REVIEW,
            type=Experiment.TYPE_PREF,
            review_relman=True,
            review_science=True,
        )

        form = ExperimentReviewForm(request=self.request, data={}, instance=experiment)

        self.assertEqual(
            set([f.name for f in form.required_reviews]),
            set(
                [
                    "review_science",
                    "review_advisory",
                    "review_engineering",
                    "review_qa_requested",
                    "review_intent_to_ship",
                    "review_bugzilla",
                    "review_qa",
                    "review_relman",
                ]
            ),
        )

    def test_required_reviews_when_a_risk_partner_related_is_true(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_REVIEW,
            review_relman=True,
            review_science=True,
            risk_partner_related=True,
        )

        form = ExperimentReviewForm(request=self.request, data={}, instance=experiment)

        self.assertIn(form["review_vp"], form.required_reviews)
        self.assertIn(form["review_legal"], form.required_reviews)
        self.assertNotIn(form["review_vp"], form.optional_reviews)
        self.assertNotIn(form["review_legal"], form.optional_reviews)

    def test_optional_reviews(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_REVIEW, review_relman=True, review_science=True
        )

        form = ExperimentReviewForm(request=self.request, data={}, instance=experiment)

        self.assertEqual(
            form.optional_reviews,
            [
                form["review_comms"],
                form["review_data_steward"],
                form["review_impacted_teams"],
                form["review_legal"],
                form["review_security"],
                form["review_ux"],
                form["review_vp"],
            ],
        )

    def test_optional_reviews_when_a_risk_option_is_true(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_REVIEW,
            review_relman=True,
            review_science=True,
            risk_partner_related=True,
        )

        form = ExperimentReviewForm(request=self.request, data={}, instance=experiment)

        self.assertNotIn(form["review_vp"], form.optional_reviews)
        self.assertIn(form["review_vp"], form.required_reviews)

    def test_required_reviews_for_rollout(self):
        experiment = ExperimentFactory.create(type=Experiment.TYPE_ROLLOUT)

        form = ExperimentReviewForm(self.request, instance=experiment)

        self.assertEqual(
            set([f.name for f in form.required_reviews]),
            set(
                [
                    "review_qa",
                    "review_intent_to_ship",
                    "review_qa_requested",
                    "review_advisory",
                    "review_relman",
                ]
            ),
        )

    def test_optional_reviews_for_rollout(self):
        experiment = ExperimentFactory.create(type=Experiment.TYPE_ROLLOUT)

        form = ExperimentReviewForm(self.request, instance=experiment)

        self.assertEqual(
            set([f.name for f in form.optional_reviews]),
            set(
                [
                    "review_impacted_teams",
                    "review_ux",
                    "review_legal",
                    "review_security",
                    "review_vp",
                    "review_comms",
                    "review_data_steward",
                ]
            ),
        )

    def test_cannot_check_review_relman_without_permissions(self):
        user_1 = UserFactory.create()
        user_2 = UserFactory.create()

        content_type = ContentType.objects.get_for_model(Experiment)
        permission = Permission.objects.get(
            content_type=content_type, codename="can_check_relman_signoff"
        )
        user_1.user_permissions.add(permission)

        experiment = ExperimentFactory.create_with_status(Experiment.STATUS_REVIEW)

        self.request.user = user_2
        form = ExperimentReviewForm(
            request=self.request, data={"review_relman": True}, instance=experiment
        )

        self.assertTrue(form.is_valid())
        experiment = form.save()
        self.assertFalse(experiment.review_relman)

        self.request.user = user_1

        form = ExperimentReviewForm(
            request=self.request, data={"review_relman": True}, instance=experiment
        )

        self.assertTrue(form.is_valid())
        experiment = form.save()

        self.assertTrue(experiment.review_relman)

    def test_cannot_check_review_qa_without_permissions(self):
        user_1 = UserFactory.create()
        user_2 = UserFactory.create()

        content_type = ContentType.objects.get_for_model(Experiment)
        permission = Permission.objects.get(
            content_type=content_type, codename="can_check_QA_signoff"
        )
        user_1.user_permissions.add(permission)
        self.assertTrue(user_1.has_perm("experiments.can_check_QA_signoff"))
        self.assertFalse(user_2.has_perm("experiments.can_check_QA_signoff"))

        experiment = ExperimentFactory.create_with_status(Experiment.STATUS_REVIEW)

        self.request.user = user_2
        form = ExperimentReviewForm(
            request=self.request, data={"review_qa": True}, instance=experiment
        )

        self.assertTrue(form.is_valid())
        experiment = form.save()
        self.assertFalse(experiment.review_qa)

        self.request.user = user_1

        form = ExperimentReviewForm(
            request=self.request, data={"review_qa": True}, instance=experiment
        )

        self.assertTrue(form.is_valid())
        experiment = form.save()

        self.assertTrue(experiment.review_qa)


class TestExperimentStatusForm(
    MockBugzillaMixin, MockRequestMixin, MockTasksMixin, TestCase
):

    def test_form_allows_valid_state_transition_and_creates_changelog(self):
        experiment = ExperimentFactory.create_with_status(Experiment.STATUS_DRAFT)
        form = ExperimentStatusForm(
            request=self.request,
            data={"status": experiment.STATUS_REVIEW},
            instance=experiment,
        )
        self.assertTrue(form.is_valid())
        experiment = form.save()
        self.assertEqual(experiment.status, experiment.STATUS_REVIEW)
        change = experiment.changes.latest()
        self.assertEqual(change.old_status, experiment.STATUS_DRAFT)
        self.assertEqual(change.new_status, experiment.STATUS_REVIEW)

    def test_form_rejects_invalid_state_transitions(self):
        experiment = ExperimentFactory.create_with_status(Experiment.STATUS_DRAFT)
        form = ExperimentStatusForm(
            request=self.request,
            data={"status": experiment.STATUS_LIVE},
            instance=experiment,
        )
        self.assertFalse(form.is_valid())

    def test_sets_bugzilla_id_when_draft_becomes_review(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT, bugzilla_id=None
        )
        form = ExperimentStatusForm(
            request=self.request,
            data={"status": experiment.STATUS_REVIEW},
            instance=experiment,
        )
        self.assertTrue(form.is_valid())
        experiment = form.save()
        self.mock_tasks_create_bug.delay.assert_called_with(self.user.id, experiment.id)

    def test_adds_bugzilla_comment_and_normandy_slug_when_becomes_ship(self):
        experiment = ExperimentFactory.create_with_status(
            target_status=Experiment.STATUS_REVIEW,
            type=Experiment.TYPE_PREF,
            name="Experiment Name",
            slug="experiment-slug",
            firefox_min_version="57.0",
            firefox_max_version="",
            firefox_channel=Experiment.CHANNEL_NIGHTLY,
            bugzilla_id="12345",
        )
        self.assertEqual(experiment.normandy_slug, None)

        form = ExperimentStatusForm(
            request=self.request,
            data={"status": experiment.STATUS_SHIP},
            instance=experiment,
        )

        self.assertTrue(form.is_valid())
        experiment = form.save()

        self.assertEqual(
            experiment.normandy_slug, "pref-experiment-name-nightly-57-bug-12345"
        )
        self.mock_tasks_update_experiment_bug.delay.assert_called_with(
            self.user.id, experiment.id
        )


class TestExperimentCommentForm(MockRequestMixin, TestCase):

    def test_form_creates_comment(self):
        text = "hello"
        section = Experiment.SECTION_OVERVIEW
        experiment = ExperimentFactory.create_with_status(Experiment.STATUS_DRAFT)
        form = ExperimentCommentForm(
            request=self.request,
            data={"experiment": experiment.id, "section": section, "text": text},
        )
        self.assertTrue(form.is_valid())
        comment = form.save()
        self.assertEqual(comment.experiment, experiment)
        self.assertEqual(comment.section, section)
        self.assertEqual(comment.created_by, self.user)
        self.assertEqual(comment.text, text)

    def test_section_must_be_valid(self):
        text = "hello"
        section = "invalid section"
        experiment = ExperimentFactory.create_with_status(Experiment.STATUS_DRAFT)
        form = ExperimentCommentForm(
            request=self.request,
            data={"experiment": experiment.id, "section": section, "text": text},
        )
        self.assertFalse(form.is_valid())
        self.assertIn("section", form.errors)

    def test_text_is_required(self):
        text = ""
        section = Experiment.SECTION_OVERVIEW
        experiment = ExperimentFactory.create_with_status(Experiment.STATUS_DRAFT)
        form = ExperimentCommentForm(
            request=self.request,
            data={"experiment": experiment.id, "section": section, "text": text},
        )
        self.assertFalse(form.is_valid())
        self.assertIn("text", form.errors)


class TestExperimentArchiveForm(MockRequestMixin, MockTasksMixin, TestCase):

    def test_form_flips_archive_bool(self):

        experiment = ExperimentFactory.create(archived=False)

        form = ExperimentArchiveForm(self.request, instance=experiment, data={})
        self.assertTrue(form.is_valid())
        experiment = form.save()

        self.assertEqual(self.mock_tasks_update_bug_resolution.delay.call_count, 1)
        self.assertTrue(experiment.archived)
        self.assertEqual(experiment.changes.latest().message, "Archived Delivery")

        form = ExperimentArchiveForm(self.request, instance=experiment, data={})
        self.assertTrue(form.is_valid())

        experiment = form.save()
        self.assertEqual(self.mock_tasks_update_bug_resolution.delay.call_count, 2)
        self.assertFalse(experiment.archived)
        self.assertEqual(experiment.changes.latest().message, "Unarchived Delivery")

    def test_form_stays_unarchived_when_live(self):
        self.assertEqual(Notification.objects.count(), 0)
        experiment = ExperimentFactory.create(
            archived=False, status=Experiment.STATUS_LIVE
        )

        form = ExperimentArchiveForm(self.request, instance=experiment, data={})
        self.assertTrue(form.is_valid())
        experiment = form.save()

        self.mock_tasks_update_bug_resolution.delay.assert_not_called()
        self.assertFalse(experiment.archived)
        self.assertEqual(Notification.objects.count(), 1)


class TestExperimentSubscribedForm(MockRequestMixin, TestCase):

    def test_form_adds_subscribers(self):
        experiment = ExperimentFactory.create()

        self.assertFalse(self.user in experiment.subscribers.all())

        form = ExperimentSubscribedForm(self.request, instance=experiment, data={})
        self.assertTrue(form.is_valid())

        experiment = form.save()
        self.assertTrue(self.user in experiment.subscribers.all())

    def test_form_removes_subscribers(self):
        experiment = ExperimentFactory.create(subscribers=[self.user])

        self.assertTrue(self.user in experiment.subscribers.all())

        form = ExperimentSubscribedForm(self.request, instance=experiment, data={})
        self.assertTrue(form.is_valid())

        experiment = form.save()
        self.assertFalse(self.user in experiment.subscribers.all())


class TestNormandyIdForm(MockRequestMixin, TestCase):

    def test_form_not_valid_with_bad_main_id(self):
        experiment = ExperimentFactory.create()

        form = NormandyIdForm(
            self.request,
            instance=experiment,
            data={"normandy_id": "aaaa", "other_normandy_ids": "434"},
        )

        self.assertFalse(form.is_valid())

    def test_form_not_valid_with_bad_other_ids(self):
        experiment = ExperimentFactory.create()

        form = NormandyIdForm(
            self.request,
            instance=experiment,
            data={"normandy_id": "4343", "other_normandy_ids": "434, aaa"},
        )

        self.assertFalse(form.is_valid())

    def test_form_not_valid_when_other_ids_duplicate_main_id(self):
        experiment = ExperimentFactory.create()

        form = NormandyIdForm(
            self.request,
            instance=experiment,
            data={"normandy_id": "4343", "other_normandy_ids": "4343"},
        )

        self.assertFalse(form.is_valid())

    def test_form_valid_when_other_ids_formatted_correctly(self):
        experiment = ExperimentFactory.create()

        form = NormandyIdForm(
            self.request,
            instance=experiment,
            data={"normandy_id": "4343", "other_normandy_ids": "4323, 5671"},
        )

        self.assertTrue(form.is_valid())

    def test_form_changelog_has_message(self):
        experiment = ExperimentFactory.create()

        form = NormandyIdForm(
            self.request,
            instance=experiment,
            data={"normandy_id": "4343", "other_normandy_ids": "443"},
        )

        self.assertTrue(form.is_valid())

        form.save()

        self.assertTrue(experiment.changes.latest().message, "Recipe ID(s) Added")


class TestExperimentOrderingForm(TestCase):

    def test_accepts_valid_ordering(self):
        ordering = ExperimentOrderingForm.ORDERING_CHOICES[1][0]
        form = ExperimentOrderingForm({"ordering": ordering})
        self.assertTrue(form.is_valid())

    def test_rejects_invalid_ordering(self):
        form = ExperimentOrderingForm({"ordering": "invalid ordering"})
        self.assertFalse(form.is_valid())
