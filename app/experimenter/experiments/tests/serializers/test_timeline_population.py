from django.test import TestCase
import datetime

from experimenter.experiments.tests.factories import (
    ExperimentFactory,
    LocaleFactory,
    CountryFactory,
)

from experimenter.experiments.serializers.timeline_population import (
    ExperimentTimelinePopSerializer,
    CountrySerializerMultiSelect,
    LocaleSerializerMultiSelect,
)
from experimenter.experiments.constants import ExperimentConstants
from experimenter.experiments.tests.mixins import MockRequestMixin


class TestLocaleSerializerMultiSelect(TestCase):
    def test_serializer_outputs_expected_schema(self):
        locale = LocaleFactory.create()
        serializer = LocaleSerializerMultiSelect(locale)
        self.assertEqual(serializer.data, {"value": locale.id, "label": locale.name})


class TestCountrySerializerMultiSelect(TestCase):
    def test_serializer_outputs_expected_schema(self):
        country = CountryFactory.create()
        serializer = CountrySerializerMultiSelect(country)
        self.assertEqual(serializer.data, {"value": country.id, "label": country.name})


class TestExperimentTimelinePopSerializer(MockRequestMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.locale = LocaleFactory.create()
        self.country = CountryFactory.create()
        self.experiment = ExperimentFactory.create_with_status(
            ExperimentConstants.STATUS_DRAFT,
            type=ExperimentConstants.TYPE_PREF,
            locales=[self.locale],
            countries=[self.country],
            population_percent="30.0000",
            platforms=[ExperimentConstants.PLATFORM_WINDOWS],
        )

    def test_serializer_outputs_expected_schema_pref(self):
        serializer = ExperimentTimelinePopSerializer(self.experiment)

        self.assertEqual(
            serializer.data,
            {
                "proposed_start_date": self.experiment.proposed_start_date.strftime(
                    "%Y-%m-%d"
                ),
                "rollout_playbook": None,
                "proposed_enrollment": self.experiment.proposed_enrollment,
                "proposed_duration": self.experiment.proposed_duration,
                "population_percent": self.experiment.population_percent,
                "firefox_channel": self.experiment.firefox_channel,
                "firefox_min_version": self.experiment.firefox_min_version,
                "firefox_max_version": self.experiment.firefox_max_version,
                "locales": [{"value": self.locale.id, "label": self.locale.name}],
                "countries": [{"value": self.country.id, "label": self.country.name}],
                "platforms": [
                    {
                        "value": ExperimentConstants.PLATFORM_WINDOWS,
                        "label": ExperimentConstants.PLATFORM_WINDOWS,
                    }
                ],
                "client_matching": self.experiment.client_matching,
            },
        )

    def test_all_values_are_optional(self):
        data = {}
        serializer = ExperimentTimelinePopSerializer(instance=self.experiment, data=data)
        self.assertTrue(serializer.is_valid())

    def test_serializer_saves_values(self):
        country = CountryFactory()
        locale = LocaleFactory()
        countries = [{"value": country.id, "label": country.name}]
        locales = [{"value": locale.id, "label": locale.name}]

        data = {
            "proposed_start_date": datetime.date.today(),
            "proposed_duration": 50,
            "proposed_enrollment": 20,
            "population_percent": 32,
            "firefox_channel": "Nightly",
            "firefox_min_version": "67.0",
            "firefox_max_version": "68.0",
            "countries": countries,
            "locales": locales,
            "platforms": [
                {
                    "value": ExperimentConstants.PLATFORM_WINDOWS,
                    "label": ExperimentConstants.PLATFORM_WINDOWS,
                }
            ],
            "client_matching": "matching client.",
        }

        serializer = ExperimentTimelinePopSerializer(
            instance=self.experiment, data=data, context={"request": self.request}
        )

        self.assertTrue(serializer.is_valid())

        experiment = serializer.save()

        self.assertEqual(experiment.changes.count(), 2)
        self.assertEqual(experiment.proposed_start_date, data["proposed_start_date"])
        self.assertEqual(experiment.proposed_duration, data["proposed_duration"])
        self.assertEqual(experiment.proposed_enrollment, data["proposed_enrollment"])
        self.assertEqual(experiment.population_percent, data["population_percent"])
        self.assertEqual(experiment.firefox_channel, data["firefox_channel"])
        self.assertEqual(experiment.firefox_min_version, data["firefox_min_version"])
        self.assertEqual(experiment.firefox_max_version, data["firefox_max_version"])
        self.assertEqual(experiment.countries.get(), country)
        self.assertEqual(experiment.locales.get(), locale)
        self.assertEqual(experiment.platforms, [ExperimentConstants.PLATFORM_WINDOWS])
        self.assertEqual(experiment.client_matching, data["client_matching"])

    def test_serializer_rejects_firefox_min_less_max(self):
        data = {
            "firefox_min_version": "69.0",
            "firefox_max_version": "68.0",
            "countries": [],
            "locales": [],
        }

        serializer = ExperimentTimelinePopSerializer(instance=self.experiment, data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("firefox_max_version", serializer.errors)

    def test_serializer_rejects_date_in_past(self):
        data = {"proposed_start_date": "2019-2-01", "countries": [], "locales": []}

        serializer = ExperimentTimelinePopSerializer(instance=self.experiment, data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("proposed_start_date", serializer.errors)

    def test_serializer_rejects_enrollment_greater_duration(self):
        data = {
            "countries": [],
            "locales": [],
            "proposed_enrollment": 40,
            "proposed_duration": 30,
        }

        serializer = ExperimentTimelinePopSerializer(instance=self.experiment, data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("proposed_enrollment", serializer.errors)

    def test_serializer_rejects_empty_platforms(self):
        data = {"countries": [], "locales": [], "platforms": []}

        serializer = ExperimentTimelinePopSerializer(instance=self.experiment, data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("platforms", serializer.errors)

    def test_serializer_outputs_expected_schema_rollout(self):
        experiment = ExperimentFactory.create(
            type=ExperimentConstants.TYPE_ROLLOUT,
            rollout_playbook="Low Risk Schedule",
            locales=[self.locale],
            countries=[self.country],
            population_percent="30.0000",
            proposed_enrollment=None,
            platforms=[ExperimentConstants.PLATFORM_WINDOWS],
        )

        serializer = ExperimentTimelinePopSerializer(experiment)

        self.assertEqual(
            serializer.data,
            {
                "proposed_start_date": experiment.proposed_start_date.strftime(
                    "%Y-%m-%d"
                ),
                "proposed_enrollment": experiment.proposed_enrollment,
                "rollout_playbook": experiment.rollout_playbook,
                "proposed_duration": experiment.proposed_duration,
                "population_percent": experiment.population_percent,
                "firefox_channel": experiment.firefox_channel,
                "firefox_min_version": experiment.firefox_min_version,
                "firefox_max_version": experiment.firefox_max_version,
                "locales": [{"value": self.locale.id, "label": self.locale.name}],
                "countries": [{"value": self.country.id, "label": self.country.name}],
                "platforms": [
                    {
                        "value": ExperimentConstants.PLATFORM_WINDOWS,
                        "label": ExperimentConstants.PLATFORM_WINDOWS,
                    }
                ],
                "client_matching": experiment.client_matching,
            },
        )

    def test_serializer_saves_rollout_playbook_field(self):
        experiment = ExperimentFactory.create(
            type=ExperimentConstants.TYPE_ROLLOUT,
            rollout_playbook=ExperimentConstants.ROLLOUT_PLAYBOOK_LOW_RISK,
            locales=[self.locale],
            countries=[self.country],
            population_percent="30.0000",
            proposed_enrollment=None,
        )

        data = {
            "rollout_playbook": ExperimentConstants.ROLLOUT_PLAYBOOK_HIGH_RISK,
            "countries": [],
            "locales": [],
        }

        serializer = ExperimentTimelinePopSerializer(
            instance=experiment, data=data, context={"request": self.request}
        )

        self.assertTrue(serializer.is_valid())

        experiment = serializer.save()

        self.assertEqual(
            experiment.rollout_playbook, ExperimentConstants.ROLLOUT_PLAYBOOK_HIGH_RISK
        )
