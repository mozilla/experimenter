import datetime
import decimal
import json

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.utils import timezone
from django.utils.text import slugify
from faker import Factory as FakerFactory
from parameterized import parameterized_class
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
    ExperimentVariantGenericForm,
    ExperimentVariantPrefForm,
    ExperimentDesignGenericForm,
    ExperimentDesignAddonForm,
    ExperimentDesignPrefForm,
    ExperimentResultsForm,
    JSONField,
    NormandyIdForm,
    ExperimentTimelinePopulationForm,
    ExperimentOrderingForm,
)
from experimenter.experiments.models import (
    Experiment,
    ExperimentVariant,
    ExperimentChangeLog,
)
from experimenter.base.tests.factories import CountryFactory, LocaleFactory
from experimenter.experiments.tests.factories import (
    ExperimentFactory,
    UserFactory,
    ExperimentVariantFactory,
)
from experimenter.experiments.tests.mixins import (
    MockBugzillaMixin,
    MockTasksMixin,
    MockRequestMixin,
)

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


class TestExperimentVariantGenericForm(TestCase):

    def setUp(self):
        self.experiment = ExperimentFactory.create()
        self.data = {
            "description": "Its the control! So controlly.",
            "experiment": self.experiment.id,
            "is_control": True,
            "name": "The Control Variant",
            "ratio": 50,
        }

    def test_form_creates_variant(self):
        form = ExperimentVariantGenericForm(self.data)

        self.assertTrue(form.is_valid())

        saved_variant = form.save()
        variant = ExperimentVariant.objects.get(id=saved_variant.id)

        self.assertEqual(variant.experiment.id, self.experiment.id)
        self.assertTrue(variant.is_control)
        self.assertEqual(variant.description, self.data["description"])
        self.assertEqual(variant.name, self.data["name"])
        self.assertEqual(variant.ratio, self.data["ratio"])
        self.assertEqual(variant.slug, "the-control-variant")

    def test_ratio_must_be_greater_than_0(self):
        self.data["ratio"] = 0
        form = ExperimentVariantGenericForm(self.data)

        self.assertFalse(form.is_valid())
        self.assertIn("ratio", form.errors)

    def test_ratio_must_be_less_than_or_equal_to_100(self):
        self.data["ratio"] = 101
        form = ExperimentVariantGenericForm(self.data)

        self.assertFalse(form.is_valid())
        self.assertIn("ratio", form.errors)

    def test_checks_empty_slug(self):
        self.data["name"] = "!"
        form = ExperimentVariantGenericForm(self.data)

        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)

    def test_updates_variant_slug(self):
        variant = ExperimentVariantFactory.create(slug="the-treatment-variant")
        form = ExperimentVariantGenericForm(self.data, instance=variant)

        self.assertTrue(form.is_valid())

        saved_variant = form.save()
        self.assertEqual(saved_variant.slug, "the-control-variant")


class TestExperimentVariantPrefForm(TestCase):

    def test_form_creates_variant(self):
        experiment = ExperimentFactory.create()

        data = {
            "description": "Its the control! So controlly.",
            "experiment": experiment.id,
            "is_control": True,
            "name": "The Control Variant",
            "ratio": 50,
            "value": "true",
        }

        form = ExperimentVariantPrefForm(data)

        self.assertTrue(form.is_valid())

        saved_variant = form.save()
        variant = ExperimentVariant.objects.get(id=saved_variant.id)

        self.assertEqual(variant.experiment.id, experiment.id)
        self.assertTrue(variant.is_control)
        self.assertEqual(variant.description, data["description"])
        self.assertEqual(variant.name, data["name"])
        self.assertEqual(variant.ratio, data["ratio"])
        self.assertEqual(variant.slug, "the-control-variant")
        self.assertEqual(variant.value, "true")


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
                "display_name": "Proposed Delivery Duration (days)",
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

    def test_changelog_values_with_prev_log(self):
        experiment = ExperimentFactory.create_with_variants(
            type=Experiment.TYPE_PREF,
            num_variants=0,
            pref_type=Experiment.PREF_TYPE_INT,
            pref_branch=Experiment.PREF_BRANCH_DEFAULT,
        )
        addon_url = "https://www.example.com/old-branch-1-name-release.xpi"

        ExperimentVariantFactory(
            name="old branch 1 name",
            slug="old-branch-1-name",
            ratio=50,
            value=8,
            is_control=True,
            description="old branch 1 desc",
            experiment=experiment,
            addon_release_url=addon_url,
        )

        changed_values = {
            "variants": {
                "old_value": None,
                "new_value": [
                    {
                        "name": "old branch 1 name",
                        "slug": "old-branch-1-name",
                        "ratio": 50,
                        "value": "8",
                        "is_control": True,
                        "description": "old branch 1 desc",
                        "addon_release_url": addon_url,
                    }
                ],
                "display_name": "Branches",
            }
        }

        ExperimentChangeLog.objects.create(
            experiment=experiment,
            changed_by=self.request.user,
            old_status=Experiment.STATUS_ACCEPTED,
            new_status=Experiment.STATUS_DRAFT,
            changed_values=changed_values,
            message="",
        )

        data = {
            "pref_key": experiment.pref_key,
            "pref_type": Experiment.PREF_TYPE_INT,
            "pref_branch": Experiment.PREF_BRANCH_DEFAULT,
            "addon_experiment_id": experiment.addon_experiment_id,
            "addon_release_url": experiment.addon_release_url,
            "variants-TOTAL_FORMS": "2",
            "variants-INITIAL_FORMS": "0",
            "variants-MIN_NUM_FORMS": "0",
            "variants-MAX_NUM_FORMS": "1000",
            "variants-0-is_control": True,
            "variants-0-ratio": "50",
            "variants-0-name": "variant 0 name",
            "variants-0-description": "variant 0 desc",
            "variants-0-value": 5,
            "variants-1-is_control": False,
            "variants-1-ratio": "50",
            "variants-1-name": "branch 1 name",
            "variants-1-description": "branch 1 desc",
            "variants-1-value": 8,
        }

        form = ExperimentDesignPrefForm(
            request=self.request, data=data, instance=experiment
        )
        self.assertTrue(form.is_valid())
        experiment = form.save()
        latest_changes = experiment.changes.latest()

        old_value = [
            {
                "description": "old branch 1 desc",
                "is_control": True,
                "name": "old branch 1 name",
                "ratio": 50,
                "slug": "old-branch-1-name",
                "value": "8",
                "addon_release_url": addon_url,
            }
        ]

        new_value = [
            {
                "description": "branch 1 desc",
                "is_control": False,
                "name": "branch 1 name",
                "ratio": 50,
                "slug": "branch-1-name",
                "value": "8",
                "addon_release_url": None,
            },
            {
                "description": "variant 0 desc",
                "is_control": True,
                "name": "variant 0 name",
                "ratio": 50,
                "slug": "variant-0-name",
                "value": "5",
                "addon_release_url": None,
            },
            {
                "description": "old branch 1 desc",
                "is_control": True,
                "name": "old branch 1 name",
                "ratio": 50,
                "slug": "old-branch-1-name",
                "value": "8",
                "addon_release_url": addon_url,
            },
        ]

        variant_changes = latest_changes.changed_values["variants"]

        self.assertEqual(variant_changes["display_name"], "Branches")
        self.assertEqual(variant_changes["old_value"], old_value)
        self.assertCountEqual(variant_changes["new_value"], new_value)


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

    def test_minimum_required_fields(self):
        bug_url = "https://bugzilla.mozilla.org/show_bug.cgi?id=123"

        data = {
            "type": Experiment.TYPE_PREF,
            "owner": self.user.id,
            "name": "A new experiment!",
            "short_description": "Let us learn new things",
            "data_science_bugzilla_url": bug_url,
            "analysis_owner": self.user.id,
            "public_name": "Public Name",
            "public_description": "Public Description",
        }
        form = ExperimentOverviewForm(request=self.request, data=data)
        self.assertTrue(form.is_valid())

        experiment = form.save()

        self.assertEqual(experiment.owner, self.user)
        self.assertEqual(experiment.status, experiment.STATUS_DRAFT)
        self.assertEqual(experiment.name, self.data["name"])
        self.assertEqual(experiment.slug, "a-new-experiment")
        self.assertEqual(experiment.short_description, self.data["short_description"])

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


class TestExperimentTimelinePopulationForm(MockRequestMixin, TestCase):

    def setUp(self):
        super().setUp()

        self.data = {
            "population_percent": "10.0",
            "proposed_start_date": timezone.now().date(),
            "firefox_min_version": "67.0",
            "firefox_max_version": "69.0",
            "firefox_channel": Experiment.CHANNEL_NIGHTLY,
            "client_matching": "en-us",
            "platform": Experiment.PLATFORM_WINDOWS,
            "proposed_enrollment": 10,
            "proposed_duration": 20,
            "locales": [],
            "countries": [],
        }

    def test_no_fields_required(self):
        experiment = ExperimentFactory.create()
        form = ExperimentTimelinePopulationForm(
            request=self.request, data={}, instance=experiment
        )
        self.assertTrue(form.is_valid())

    def test_form_saves_timeline_population_data(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT, countries=[], locales=[]
        )
        form = ExperimentTimelinePopulationForm(
            request=self.request, data=self.data, instance=experiment
        )

        experiment = form.save()

        self.assertEqual(experiment.proposed_start_date, self.data["proposed_start_date"])
        self.assertEqual(experiment.firefox_max_version, self.data["firefox_max_version"])
        self.assertEqual(experiment.firefox_channel, self.data["firefox_channel"])

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

    def test_form_saves_population(self):
        experiment = ExperimentFactory.create_with_status(Experiment.STATUS_DRAFT)

        form = ExperimentTimelinePopulationForm(
            request=self.request, data=self.data, instance=experiment
        )

        self.assertTrue(form.is_valid())

        experiment = form.save()

        self.assertEqual(experiment.population_percent, decimal.Decimal("10.000"))
        self.assertEqual(experiment.firefox_min_version, self.data["firefox_min_version"])
        self.assertEqual(experiment.firefox_channel, self.data["firefox_channel"])
        self.assertEqual(experiment.client_matching, self.data["client_matching"])
        self.assertEqual(experiment.platform, self.data["platform"])

    def test_form_is_invalid_if_firefox_max_is_lower_than_min(self):
        self.data["firefox_min_version"] = "66.0"
        self.data["firefox_max_version"] = "64.0"
        form = ExperimentTimelinePopulationForm(request=self.request, data=self.data)
        self.assertFalse(form.is_valid())
        self.assertIn("firefox_max_version", form.errors)


@parameterized_class(
    ["form_class"],
    [
        [ExperimentDesignGenericForm],
        [ExperimentDesignAddonForm],
        [ExperimentDesignPrefForm],
    ],
)
class TestExperimentVariantFormSet(MockRequestMixin, TestCase):

    def setUp(self):
        super().setUp()

        self.experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT, num_variants=0
        )

        self.data = get_design_form_data()

    def test_formset_valid_if_sizes_sum_to_100(self):
        self.data["variants-0-ratio"] = "34"
        self.data["variants-1-ratio"] = "33"
        self.data["variants-2-ratio"] = "33"
        form = self.form_class(
            request=self.request, data=self.data, instance=self.experiment
        )
        self.assertTrue(form.is_valid())

    def test_formset_invalid_if_sizes_sum_to_less_than_100(self):
        self.data["variants-0-ratio"] = "33"
        self.data["variants-1-ratio"] = "33"
        self.data["variants-2-ratio"] = "33"
        form = self.form_class(
            request=self.request, data=self.data, instance=self.experiment
        )
        self.assertFalse(form.is_valid())

        for form in form.variants_formset.forms:
            self.assertIn("ratio", form.errors)

    def test_formset_invalid_if_sizes_sum_to_more_than_100(self):
        self.data["variants-0-ratio"] = "35"
        self.data["variants-1-ratio"] = "33"
        self.data["variants-2-ratio"] = "33"
        form = self.form_class(
            request=self.request, data=self.data, instance=self.experiment
        )
        self.assertFalse(form.is_valid())

        for form in form.variants_formset.forms:
            self.assertIn("ratio", form.errors)

    def test_formset_invalid_if_duplicate_names_appear(self):
        self.data["variants-0-name"] = self.data["variants-1-name"]
        form = self.form_class(
            request=self.request, data=self.data, instance=self.experiment
        )
        self.assertFalse(form.is_valid())

        for form in form.variants_formset.forms:
            self.assertIn("name", form.errors)

    def test_empty_branch_size_raises_validation_error(self):
        del self.data["variants-0-ratio"]
        form = self.form_class(
            request=self.request, data=self.data, instance=self.experiment
        )
        self.assertFalse(form.is_valid())


@parameterized_class(
    ["form_class"],
    [
        [ExperimentDesignGenericForm],
        [ExperimentDesignAddonForm],
        [ExperimentDesignPrefForm],
    ],
)
class TestExperimentDesignBaseForm(MockRequestMixin, TestCase):

    def setUp(self):
        super().setUp()

        self.experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT, num_variants=0, countries=[], locales=[]
        )

        self.data = get_design_form_data()

    def test_formset_saves_new_variants(self):
        form = self.form_class(
            request=self.request, data=self.data, instance=self.experiment
        )

        self.assertTrue(form.is_valid())

        self.assertEqual(self.experiment.variants.count(), 0)
        experiment = form.save()

        self.assertEqual(experiment.variants.count(), 3)

        branch0 = experiment.variants.get(name=self.data["variants-0-name"])
        self.assertTrue(branch0.is_control)
        self.assertTrue(branch0.slug, "control-name")
        self.assertEqual(branch0.ratio, 34)
        self.assertEqual(branch0.description, self.data["variants-0-description"])

        branch1 = experiment.variants.get(name=self.data["variants-1-name"])
        self.assertFalse(branch1.is_control)
        self.assertEqual(branch1.slug, "branch-1-name")
        self.assertEqual(branch1.ratio, 33)
        self.assertEqual(branch1.description, self.data["variants-1-description"])

        branch2 = experiment.variants.get(name=self.data["variants-2-name"])
        self.assertFalse(branch2.is_control)
        self.assertEqual(branch2.slug, "branch-2-name")
        self.assertEqual(branch2.ratio, 33)
        self.assertEqual(branch2.description, self.data["variants-2-description"])

    def test_formset_edits_existing_variants(self):
        form = self.form_class(
            request=self.request, data=self.data, instance=self.experiment
        )

        self.assertTrue(form.is_valid())

        self.assertEqual(self.experiment.variants.count(), 0)

        experiment = form.save()

        self.assertEqual(experiment.variants.count(), 3)

        self.data["variants-INITIAL_FORMS"] = 3

        branch0 = experiment.variants.get(name=self.data["variants-0-name"])
        self.data["variants-0-id"] = branch0.id
        self.data["variants-0-DELETE"] = False
        self.data["variants-0-name"] = "new branch 0 name"
        self.data["variants-0-description"] = "new branch 0 description"

        branch1 = experiment.variants.get(name=self.data["variants-1-name"])
        self.data["variants-1-id"] = branch1.id
        self.data["variants-1-DELETE"] = False
        self.data["variants-1-name"] = "new branch 1 name"
        self.data["variants-1-description"] = "new branch 1 description"

        branch2 = experiment.variants.get(name=self.data["variants-2-name"])
        self.data["variants-2-id"] = branch2.id
        self.data["variants-2-DELETE"] = False
        self.data["variants-2-name"] = "new branch 2 name"
        self.data["variants-2-description"] = "new branch 2 description"

        form = self.form_class(request=self.request, data=self.data, instance=experiment)

        self.assertTrue(form.is_valid())

        experiment = form.save()

        self.assertEqual(experiment.variants.count(), 3)

        branch0 = experiment.variants.get(name=self.data["variants-0-name"])
        self.assertTrue(branch0.is_control)
        self.assertEqual(branch0.ratio, 34)
        self.assertEqual(branch0.description, self.data["variants-0-description"])

        branch1 = experiment.variants.get(name=self.data["variants-1-name"])
        self.assertFalse(branch1.is_control)
        self.assertEqual(branch1.ratio, 33)
        self.assertEqual(branch1.description, self.data["variants-1-description"])

        branch2 = experiment.variants.get(name=self.data["variants-2-name"])
        self.assertFalse(branch2.is_control)
        self.assertEqual(branch2.ratio, 33)
        self.assertEqual(branch2.description, self.data["variants-2-description"])

    def test_formset_adds_new_variant(self):
        form = self.form_class(
            request=self.request, data=self.data, instance=self.experiment
        )

        self.assertTrue(form.is_valid())

        self.assertEqual(self.experiment.variants.count(), 0)

        experiment = form.save()

        self.assertEqual(experiment.variants.count(), 3)

        self.data["variants-INITIAL_FORMS"] = 3
        self.data["variants-TOTAL_FORMS"] = 4

        branch0 = experiment.variants.get(name=self.data["variants-0-name"])
        self.data["variants-0-id"] = branch0.id
        self.data["variants-0-ratio"] = 25

        branch1 = experiment.variants.get(name=self.data["variants-1-name"])
        self.data["variants-1-id"] = branch1.id
        self.data["variants-1-ratio"] = 25

        branch2 = experiment.variants.get(name=self.data["variants-2-name"])
        self.data["variants-2-id"] = branch2.id
        self.data["variants-2-ratio"] = 25

        self.data["variants-3-DELETE"] = False
        self.data["variants-3-name"] = "new branch 0 name"
        self.data["variants-3-description"] = "new branch 0 description"
        self.data["variants-3-ratio"] = 25
        self.data["variants-3-value"] = '"new branch 3 value"'

        form = self.form_class(request=self.request, data=self.data, instance=experiment)

        self.assertTrue(form.is_valid())

        experiment = form.save()

        self.assertEqual(experiment.variants.count(), 4)

        branch0 = experiment.variants.get(name=self.data["variants-0-name"])
        self.assertEqual(branch0.ratio, 25)

        branch1 = experiment.variants.get(name=self.data["variants-1-name"])
        self.assertEqual(branch1.ratio, 25)

        branch2 = experiment.variants.get(name=self.data["variants-2-name"])
        self.assertEqual(branch2.ratio, 25)

        branch3 = experiment.variants.get(name=self.data["variants-3-name"])
        self.assertEqual(branch3.ratio, 25)
        self.assertEqual(branch3.description, self.data["variants-3-description"])

    def test_formset_removes_variant(self):
        form = self.form_class(
            request=self.request, data=self.data, instance=self.experiment
        )

        self.assertTrue(form.is_valid())

        self.assertEqual(self.experiment.variants.count(), 0)

        experiment = form.save()

        self.assertEqual(experiment.variants.count(), 3)

        self.data["variants-INITIAL_FORMS"] = 3
        self.data["variants-TOTAL_FORMS"] = 3

        branch0 = experiment.variants.get(name=self.data["variants-0-name"])
        self.data["variants-0-id"] = branch0.id
        self.data["variants-0-ratio"] = 50

        branch1 = experiment.variants.get(name=self.data["variants-1-name"])
        self.data["variants-1-id"] = branch1.id
        self.data["variants-1-DELETE"] = True

        branch2 = experiment.variants.get(name=self.data["variants-2-name"])
        self.data["variants-2-id"] = branch2.id
        self.data["variants-2-ratio"] = 50

        form = self.form_class(request=self.request, data=self.data, instance=experiment)

        self.assertTrue(form.is_valid())

        experiment = form.save()

        self.assertEqual(experiment.variants.count(), 2)

        self.assertTrue(
            experiment.variants.filter(name=self.data["variants-0-name"]).exists()
        )
        self.assertFalse(
            experiment.variants.filter(name=self.data["variants-1-name"]).exists()
        )
        self.assertTrue(
            experiment.variants.filter(name=self.data["variants-2-name"]).exists()
        )

    def test_formset_checks_uniqueness_for_single_experiment_not_all(self):
        # We want to make sure that all the branches in a single
        # experiment have unique names/slugs but not that they're
        # unique across all experiments.  This behaviour was accidentally
        # introduced in 30c210183cd1568850d54132633b0f23e3e56c98
        # so I'm adding a test for it.
        experiment1 = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT, num_variants=0
        )
        self.data["addon_experiment_id"] = "addon-experiment-1"
        form1 = self.form_class(
            request=self.request, data=self.data, instance=experiment1
        )
        self.assertTrue(form1.is_valid())
        experiment1 = form1.save()
        self.assertEqual(experiment1.variants.count(), 3)

        experiment2 = ExperimentFactory.create_with_status(
            Experiment.STATUS_DRAFT, num_variants=0
        )
        self.data["addon_experiment_id"] = "addon-experiment-2"
        form2 = self.form_class(
            request=self.request, data=self.data, instance=experiment2
        )
        self.assertTrue(form2.is_valid())
        experiment2 = form2.save()
        self.assertEqual(experiment2.variants.count(), 3)


def get_variants_form_data():
    return {
        "variants-TOTAL_FORMS": "3",
        "variants-INITIAL_FORMS": "0",
        "variants-MIN_NUM_FORMS": "0",
        "variants-MAX_NUM_FORMS": "1000",
        "variants-0-is_control": True,
        "variants-0-ratio": "34",
        "variants-0-name": "control name",
        "variants-0-description": "control desc",
        "variants-0-value": '"control value"',
        "variants-1-is_control": False,
        "variants-1-ratio": "33",
        "variants-1-name": "branch 1 name",
        "variants-1-description": "branch 1 desc",
        "variants-1-value": '"branch 1 value"',
        "variants-2-is_control": False,
        "variants-2-ratio": "33",
        "variants-2-name": "branch 2 name",
        "variants-2-description": "branch 2 desc",
        "variants-2-value": '"branch 2 value"',
    }


def get_design_form_data():
    data = get_variants_form_data()
    data.update(
        {
            "pref_key": "browser.test.example",
            "pref_type": Experiment.PREF_TYPE_STR,
            "pref_branch": Experiment.PREF_BRANCH_DEFAULT,
            "addon_experiment_id": slugify(faker.catch_phrase()),
            "addon_release_url": "https://www.example.com/release.xpi",
            "design": "Design",
        }
    )
    return data


class TestExperimentDesignGenericForm(MockRequestMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.data = get_variants_form_data()
        self.data.update({"design": "Design"})

    def test_form_saves_design_information(self):
        experiment = ExperimentFactory.create(
            type=Experiment.TYPE_GENERIC, design=Experiment.DESIGN_DEFAULT
        )

        form = ExperimentDesignGenericForm(
            request=self.request, data=self.data, instance=experiment
        )

        self.assertTrue(form.is_valid())

        experiment = form.save()

        self.assertEqual(experiment.design, self.data["design"])


class TestExperimentDesignAddonForm(MockRequestMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.data = get_variants_form_data()
        self.data.update(
            {
                "addon_experiment_id": slugify(faker.catch_phrase()),
                "addon_release_url": "https://www.example.com/release.xpi",
            }
        )

    def test_minimum_required_fields(self):
        experiment = ExperimentFactory.create(
            addon_experiment_id=None, addon_release_url=None
        )

        data = get_variants_form_data()
        data["addon_release_url"] = "https://www.example.com/release.xpi"

        form = ExperimentDesignAddonForm(
            request=self.request, data=data, instance=experiment
        )

        self.assertTrue(form.is_valid())

        experiment = form.save()

        self.assertEqual(experiment.addon_release_url, self.data["addon_release_url"])

    def test_addon_experiment_id_is_unique(self):
        experiment1 = ExperimentFactory.create(
            addon_experiment_id=None, addon_release_url=None
        )

        form = ExperimentDesignAddonForm(
            request=self.request, data=self.data, instance=experiment1
        )
        self.assertTrue(form.is_valid())
        experiment1 = form.save()

        self.assertEqual(
            experiment1.addon_experiment_id, self.data["addon_experiment_id"]
        )

        experiment2 = ExperimentFactory.create(
            addon_experiment_id=None, addon_release_url=None
        )

        form = ExperimentDesignAddonForm(
            request=self.request, data=self.data, instance=experiment2
        )
        self.assertFalse(form.is_valid())
        self.assertIn("addon_experiment_id", form.errors)

    def test_addon_experiment_id_is_within_normandy_slug_max_len(self):
        experiment = ExperimentFactory.create(
            addon_experiment_id=None, addon_release_url=None
        )

        self.data["addon_experiment_id"] = "-" * (settings.NORMANDY_SLUG_MAX_LEN + 1)

        form = ExperimentDesignAddonForm(
            request=self.request, data=self.data, instance=experiment
        )

        self.assertFalse(form.is_valid())
        self.assertIn("addon_experiment_id", form.errors)

    def test_addon_experiment_id_allows_duplicate_empty_values(self):
        ExperimentFactory.create(addon_experiment_id="")
        experiment = ExperimentFactory.create(addon_experiment_id=None)

        self.data["addon_experiment_id"] = ""

        form = ExperimentDesignAddonForm(
            request=self.request, data=self.data, instance=experiment
        )

        self.assertTrue(form.is_valid())


class TestExperimentDesignPrefForm(MockRequestMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.data = get_variants_form_data()
        self.data.update(
            {
                "pref_key": "browser.test.example",
                "pref_type": Experiment.PREF_TYPE_STR,
                "pref_branch": Experiment.PREF_BRANCH_DEFAULT,
            }
        )

    def test_minimum_required_fields(self):
        experiment = ExperimentFactory.create(
            pref_key=None, pref_type=None, pref_branch=None
        )

        form = ExperimentDesignPrefForm(
            request=self.request, data=self.data, instance=experiment
        )

        self.assertTrue(form.is_valid())

        experiment = form.save()

        self.assertEqual(experiment.pref_key, self.data["pref_key"])
        self.assertEqual(experiment.pref_type, self.data["pref_type"])
        self.assertEqual(experiment.pref_branch, self.data["pref_branch"])

    def test_form_is_invalid_if_branches_have_duplicate_pref_values(self):
        self.data["variants-0-value"] = self.data["variants-1-value"]
        form = ExperimentDesignPrefForm(request=self.request, data=self.data)
        self.assertFalse(form.is_valid())
        self.assertIn("value", form.variants_formset.errors[0])
        self.assertIn("value", form.variants_formset.errors[1])
        self.assertNotIn("value", form.variants_formset.errors[2])

    def test_form_is_invalid_if_pref_value_do_not_match_pref_type(self):
        self.data["pref_type"] = Experiment.PREF_TYPE_INT
        self.data["variants-0-value"] = "hello"  # str
        self.data["variants-1-value"] = "true"  # bool
        self.data["variants-2-value"] = "5"  # int
        form = ExperimentDesignPrefForm(request=self.request, data=self.data)
        self.assertFalse(form.is_valid())
        self.assertIn("value", form.variants_formset.errors[0])
        self.assertIn("value", form.variants_formset.errors[1])
        self.assertNotIn("value", form.variants_formset.errors[2])

    def test_form_is_valid_if_pref_type_is_string(self):
        self.data["variants-0-value"] = "abc"
        form = ExperimentDesignPrefForm(request=self.request, data=self.data)
        self.assertTrue(form.is_valid())
        self.assertNotIn("value", form.variants_formset.errors[0])
        self.assertNotIn("value", form.variants_formset.errors[1])
        self.assertNotIn("value", form.variants_formset.errors[2])

    def test_form_is_valid_if_pref_type_is_bool(self):

        self.data["pref_type"] = Experiment.PREF_TYPE_BOOL

        # remove the extra variant for uniqueness bool constraint
        self.data.pop("variants-2-value")
        self.data.pop("variants-2-is_control")
        self.data.pop("variants-2-ratio")
        self.data.pop("variants-2-name")
        self.data.pop("variants-2-description")

        # modify remaining values to accomodate for only two variants
        self.data["variants-TOTAL_FORMS"] = 2
        self.data["variants-0-ratio"] = 40
        self.data["variants-1-ratio"] = 60
        self.data["variants-0-value"] = "true"
        self.data["variants-1-value"] = "false"

        form = ExperimentDesignPrefForm(request=self.request, data=self.data)

        self.assertTrue(form.is_valid())
        self.assertNotIn("value", form.variants_formset.errors[0])
        self.assertNotIn("value", form.variants_formset.errors[1])

    def test_form_is_valid_if_pref_type_is_int(self):
        self.data["pref_type"] = Experiment.PREF_TYPE_INT
        self.data["variants-0-value"] = "20"
        self.data["variants-1-value"] = "55"
        self.data["variants-2-value"] = "75"
        form = ExperimentDesignPrefForm(request=self.request, data=self.data)
        self.assertTrue(form.is_valid())
        self.assertNotIn("value", form.variants_formset.errors[0])
        self.assertNotIn("value", form.variants_formset.errors[1])
        self.assertNotIn("value", form.variants_formset.errors[2])

    def test_form_is_valid_if_pref_type_is_json_string(self):
        self.data["pref_type"] = Experiment.PREF_TYPE_JSON_STR
        self.data["variants-0-value"] = "{}"
        self.data["variants-1-value"] = "[1,2,3,4]"
        self.data["variants-2-value"] = '{"variant":[1,2,3,4]}'
        form = ExperimentDesignPrefForm(request=self.request, data=self.data)
        self.assertTrue(form.is_valid())
        self.assertNotIn("value", form.variants_formset.errors[0])
        self.assertNotIn("value", form.variants_formset.errors[1])
        self.assertNotIn("value", form.variants_formset.errors[2])

    def test_form_is_invalid_with_invalid_json(self):
        self.data["pref_type"] = Experiment.PREF_TYPE_JSON_STR
        self.data["variants-0-value"] = "{]"
        self.data["variants-1-value"] = '{5: "something"}'
        self.data["variants-2-value"] = "hi"
        form = ExperimentDesignPrefForm(request=self.request, data=self.data)
        self.assertFalse(form.is_valid())
        self.assertIn("value", form.variants_formset.errors[0])
        self.assertIn("value", form.variants_formset.errors[1])
        self.assertIn("value", form.variants_formset.errors[2])


class TestExperimentObjectivesForm(MockRequestMixin, TestCase):

    def test_no_fields_required(self):
        experiment = ExperimentFactory.create()
        form = ExperimentObjectivesForm(
            request=self.request, data={}, instance=experiment
        )
        self.assertTrue(form.is_valid())

    def test_form_saves_objectives(self):
        created_experiment = ExperimentFactory.create_with_status(Experiment.STATUS_DRAFT)

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


class TestExperimentRisksForm(MockRequestMixin, TestCase):

    valid_data = {
        "risk_internal_only": True,
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

        data = self.valid_data.copy()
        form = ExperimentRisksForm(
            request=self.request, data=data, instance=created_experiment
        )

        self.assertTrue(form.is_valid())

        experiment = form.save()
        self.assertTrue(experiment.risk_internal_only)
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


class TestExperimentResultsForm(MockRequestMixin, TestCase):

    def test_form_saves_results(self):
        experiment = ExperimentFactory.create()
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

    def test_added_reviews_property(self):
        experiment = ExperimentFactory.create_with_status(Experiment.STATUS_REVIEW)

        data = {"review_bugzilla": True, "review_science": True}

        form = ExperimentReviewForm(request=self.request, data=data, instance=experiment)

        self.assertTrue(form.is_valid())
        experiment = form.save()

        self.assertEqual(len(form.added_reviews), 2)
        self.assertEqual(len(form.removed_reviews), 0)
        self.assertIn(form.fields["review_bugzilla"].label, form.added_reviews)
        self.assertIn(form.fields["review_science"].label, form.added_reviews)

    def test_removed_reviews_property(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_REVIEW, review_bugzilla=True, review_science=True
        )

        data = {"review_bugzilla": False, "review_science": False}

        form = ExperimentReviewForm(request=self.request, data=data, instance=experiment)

        self.assertTrue(form.is_valid())
        experiment = form.save()

        self.assertEqual(len(form.added_reviews), 0)
        self.assertEqual(len(form.removed_reviews), 2)
        self.assertIn(form.fields["review_bugzilla"].label, form.removed_reviews)
        self.assertIn(form.fields["review_science"].label, form.removed_reviews)

    def test_required_reviews(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_REVIEW, review_relman=True, review_science=True
        )

        form = ExperimentReviewForm(request=self.request, data={}, instance=experiment)

        self.assertEqual(
            form.required_reviews,
            [
                form["review_science"],
                form["review_advisory"],
                form["review_engineering"],
                form["review_qa_requested"],
                form["review_intent_to_ship"],
                form["review_bugzilla"],
                form["review_qa"],
                form["review_relman"],
            ],
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
