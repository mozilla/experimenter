from django.test import TestCase
from rest_framework import serializers

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


class TestLocaleSerializerMultiSelect(serializers.ModelSerializer):

    def test_serializer_outputs_expected_schema(self):
        locale = LocaleFactory.create()
        serializer = LocaleSerializerMultiSelect(locale)

        self.assertEqual(serializer.data, {"value": locale.code, "label": locale.name})


class TestCountrySerializerMultiSelect(serializers.ModelSerializer):

    def test_serializer_outputs_expected_schema(self):
        country = CountryFactory.create()
        serializer = CountrySerializerMultiSelect(country)

        self.assertEqual(serializer.data, {"value": country.code, "label": country.name})


class TestExperimentTimelinePopSerializer(MockRequestMixin, TestCase):

    def setUp(self):
        super().setUp()

        self.experiment = ExperimentFactory.create(
            type=ExperimentConstants.TYPE_PREF,
            locales=[LocaleFactory.create()],
            countries=[CountryFactory.create()],
        )

    def test_serializer_outputs_expected_schema(self):

        serializer = ExperimentTimelinePopSerializer(self.experiment)

        self.assertEqual(
            serializer.data["proposed_start_date"],
            self.experiment.proposed_start_date.strftime("%Y-%m-%d"),
        )
        self.assertEqual(
            serializer.data["firefox_channel"], self.experiment.firefox_channel
        )
        self.assertEqual(serializer.data["platform"], self.experiment.platform)

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
            "firefox_min_version": "67.0",
            "firefox_max_version": "68.0",
            "countries": countries,
            "locales": locales,
        }

        serializer = ExperimentTimelinePopSerializer(
            instance=self.experiment, data=data, context={"request": self.request}
        )

        self.assertTrue(serializer.is_valid())

        experiment = serializer.save()

        self.assertEqual(experiment.changes.count(), 1)
        self.assertEqual(experiment.firefox_min_version, "67.0")
        self.assertEqual(experiment.firefox_max_version, "68.0")

    def test_serializer_rejects_firefox_min_less_max(self):
        data = {
            "firefox_min_version": "69.0",
            "firefox_max_version": "68.0",
            "countries": [],
            "locales": [],
        }

        serializer = ExperimentTimelinePopSerializer(instance=self.experiment, data=data)

        self.assertFalse(serializer.is_valid())

    def test_serializer_rejects_date_in_past(self):
        data = {"proposed_start_date": "2019-2-01", "countries": [], "locales": []}

        serializer = ExperimentTimelinePopSerializer(instance=self.experiment, data=data)

        self.assertFalse(serializer.is_valid())

    def test_serializer_rejects_enrollment_greater_duration(self):
        data = {
            "countries": [],
            "locales": [],
            "proposed_enrollment": 40,
            "proposed_duration": 30,
        }

        serializer = ExperimentTimelinePopSerializer(instance=self.experiment, data=data)

        self.assertFalse(serializer.is_valid())
