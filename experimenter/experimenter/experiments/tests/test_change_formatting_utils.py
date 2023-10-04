import datetime
import json

from django.test import TestCase
from django.utils import timezone

from experimenter.base.tests.factories import CountryFactory
from experimenter.experiments.changelog_utils import (
    generate_nimbus_changelog,
    get_formatted_change_object,
)
from experimenter.experiments.constants import ChangeEventType
from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tests.factories import (
    NimbusExperimentFactory,
    NimbusFeatureConfigFactory,
)
from experimenter.openidc.tests.factories import UserFactory


class TestChangeFormattingMethod(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory.create()
        cls.current_date = timezone.now().date()
        cls.time_format = "%I:%M %p %Z"

    def setUp(self):
        self.first_timestamp = timezone.make_aware(
            datetime.datetime.combine(self.current_date, datetime.datetime.min.time())
        )

    def _create_timestamp(self, hours):
        return self.first_timestamp + timezone.timedelta(hours=hours)

    def _create_formatted_timestamp(self, timestamp):
        local_timestamp = timezone.localtime(timestamp)
        return local_timestamp.strftime(self.time_format)

    def test_get_default_formatted_change_object(self):
        experiment = NimbusExperimentFactory.create(
            slug="experiment-1",
            published_dto={"id": "experiment", "test": False},
        )
        timestamp_2 = self._create_timestamp(2)
        timestamp_3 = self._create_timestamp(4)

        generate_nimbus_changelog(experiment, self.user, "created", self.first_timestamp)

        new_value = NimbusExperiment.PublishStatus.IDLE
        old_value = NimbusExperiment.PublishStatus.REVIEW

        experiment.publish_status = old_value
        experiment.save()

        generate_nimbus_changelog(
            experiment, self.user, "publish_status change", timestamp_2
        )

        experiment.publish_status = new_value
        experiment.save()

        generate_nimbus_changelog(
            experiment, self.user, "status_next change", timestamp_3
        )

        changelogs = list(
            experiment.changes.order_by("-changed_on").prefetch_related("changed_by")
        )

        comparison_log = changelogs[0]
        field_name = "publish_status"
        field_diff = {"old_value": old_value, "new_value": new_value}
        change_timestamp = self._create_formatted_timestamp(comparison_log.changed_on)
        field_instance = NimbusExperiment._meta.get_field(field_name)
        field_display_name = (
            field_instance.verbose_name
            if hasattr(field_instance, "verbose_name")
            else field_name
        )

        change = get_formatted_change_object(
            field_name, field_diff, comparison_log, change_timestamp
        )

        expected_change = {
            "event": ChangeEventType.STATE.name,
            "event_message": (
                f"{self.user} changed value of {field_display_name} from "
                f"{old_value} to {new_value}"
            ),
            "changed_by": self.user,
            "timestamp": change_timestamp,
            "old_value": old_value,
            "new_value": new_value,
        }

        self.assertDictEqual(change, expected_change)

    def test_formatting_for_native_models_field(self):
        experiment = NimbusExperimentFactory.create(
            slug="experiment-1",
            published_dto={"id": "experiment", "test": False},
        )
        timestamp_2 = self._create_timestamp(2)

        country_ca = CountryFactory.create(code="CA")
        country_us = CountryFactory.create(code="US")

        generate_nimbus_changelog(experiment, self.user, "created", self.first_timestamp)

        old_value = []
        new_value = [country_us.pk, country_ca.pk]
        transformed_value = sorted([country_ca.name, country_us.name])

        experiment.countries.set(new_value)
        experiment.save()

        generate_nimbus_changelog(
            experiment, self.user, "countries were added", timestamp_2
        )

        changelogs = list(
            experiment.changes.order_by("-changed_on").prefetch_related("changed_by")
        )

        comparison_log = changelogs[0]
        field_name = "countries"
        field_diff = {"old_value": old_value, "new_value": new_value}
        change_timestamp = self._create_formatted_timestamp(comparison_log.changed_on)
        field_instance = NimbusExperiment._meta.get_field(field_name)
        field_display_name = (
            field_instance.verbose_name
            if hasattr(field_instance, "verbose_name")
            else field_name
        )

        change = get_formatted_change_object(
            field_name, field_diff, comparison_log, change_timestamp
        )

        expected_change = {
            "event": ChangeEventType.DETAILED.name,
            "event_message": f"{self.user} changed value of {field_display_name}",
            "changed_by": self.user,
            "timestamp": change_timestamp,
            "old_value": json.dumps(old_value, indent=2),
            "new_value": json.dumps(transformed_value, indent=2),
        }

        self.assertDictEqual(change, expected_change)

    def test_formatting_for_native_models_field_none_value(self):
        experiment = NimbusExperimentFactory.create(
            slug="experiment-1",
            published_dto={"id": "experiment", "test": False},
        )
        timestamp_2 = self._create_timestamp(2)

        country_ca = CountryFactory.create(code="CA")
        country_us = CountryFactory.create(code="US")

        generate_nimbus_changelog(experiment, self.user, "created", self.first_timestamp)
        new_value = [country_us.pk, country_ca.pk]
        transformed_value = sorted([country_ca.name, country_us.name])

        experiment.countries.set(new_value)
        experiment.save()

        generate_nimbus_changelog(
            experiment, self.user, "countries were added", timestamp_2
        )

        changelogs = list(
            experiment.changes.order_by("-changed_on").prefetch_related("changed_by")
        )

        comparison_log = changelogs[0]
        field_name = "countries"
        field_diff = {"old_value": None, "new_value": new_value}
        change_timestamp = self._create_formatted_timestamp(comparison_log.changed_on)
        field_instance = NimbusExperiment._meta.get_field(field_name)
        field_display_name = (
            field_instance.verbose_name
            if hasattr(field_instance, "verbose_name")
            else field_name
        )

        change = get_formatted_change_object(
            field_name, field_diff, comparison_log, change_timestamp
        )

        expected_change = {
            "event": ChangeEventType.DETAILED.name,
            "event_message": f"{self.user} changed value of {field_display_name}",
            "changed_by": self.user,
            "timestamp": change_timestamp,
            "old_value": json.dumps([], indent=2),
            "new_value": json.dumps(transformed_value, indent=2),
        }

        self.assertDictEqual(change, expected_change)

    def test_formatting_for_custom_models_field(self):
        experiment = NimbusExperimentFactory.create(
            slug="experiment-1",
            published_dto={"id": "experiment", "test": False},
        )
        timestamp_2 = self._create_timestamp(2)
        feature = NimbusFeatureConfigFactory(slug="feature")
        fields = feature._meta.fields

        # Convert the feature object to dictionary as it is stored as such in the
        # experiment_data of a NimbusChangeLog

        feature_dict = {}
        for field in fields:
            field_name = field.name
            field_value = getattr(feature, field_name)
            feature_dict[field_name] = field_value

        generate_nimbus_changelog(experiment, self.user, "created", self.first_timestamp)

        old_value = []
        new_value = [feature_dict]

        experiment.feature_configs.set([feature])
        experiment.save()

        generate_nimbus_changelog(
            experiment, self.user, "features were added", timestamp_2
        )

        changelogs = list(
            experiment.changes.order_by("-changed_on").prefetch_related("changed_by")
        )

        comparison_log = changelogs[0]
        field_name = "feature_configs"
        field_diff = {"old_value": old_value, "new_value": new_value}
        change_timestamp = self._create_formatted_timestamp(comparison_log.changed_on)
        field_instance = NimbusExperiment._meta.get_field(field_name)
        field_display_name = (
            field_instance.verbose_name
            if hasattr(field_instance, "verbose_name")
            else field_name
        )

        change = get_formatted_change_object(
            field_name, field_diff, comparison_log, change_timestamp
        )

        expected_change = {
            "event": ChangeEventType.DETAILED.name,
            "event_message": f"{self.user} changed value of {field_display_name}",
            "changed_by": self.user,
            "timestamp": change_timestamp,
            "old_value": json.dumps(old_value, indent=2),
            "new_value": json.dumps(new_value, indent=2),
        }

        self.assertDictEqual(change, expected_change)

    def test_formatting_for_array_fields(self):
        experiment = NimbusExperimentFactory.create(
            slug="experiment-1",
            published_dto={"id": "experiment", "test": False},
        )
        timestamp_2 = self._create_timestamp(2)

        generate_nimbus_changelog(experiment, self.user, "created", self.first_timestamp)

        old_value = []
        new_value = ["test-outcome"]

        experiment.primary_outcomes = new_value
        experiment.save()

        generate_nimbus_changelog(
            experiment, self.user, "primary outcomes were added", timestamp_2
        )

        changelogs = list(
            experiment.changes.order_by("-changed_on").prefetch_related("changed_by")
        )

        comparison_log = changelogs[0]
        field_name = "primary_outcomes"
        field_diff = {"old_value": old_value, "new_value": new_value}
        change_timestamp = self._create_formatted_timestamp(comparison_log.changed_on)
        field_instance = NimbusExperiment._meta.get_field(field_name)
        field_display_name = (
            field_instance.verbose_name
            if hasattr(field_instance, "verbose_name")
            else field_name
        )

        change = get_formatted_change_object(
            field_name, field_diff, comparison_log, change_timestamp
        )

        expected_change = {
            "event": ChangeEventType.DETAILED.name,
            "event_message": f"{self.user} changed value of {field_display_name}",
            "changed_by": self.user,
            "timestamp": change_timestamp,
            "old_value": json.dumps(old_value, indent=2),
            "new_value": json.dumps(new_value, indent=2),
        }

        self.assertDictEqual(change, expected_change)

    def test_formatting_for_JSON_fields(self):
        experiment = NimbusExperimentFactory.create(
            slug="experiment-1",
            published_dto={"id": "experiment", "test": False},
        )
        timestamp_2 = self._create_timestamp(2)

        old_value = {}
        new_value = {"v2": {"overall": {"enrollments": {"all": {}}}}}

        generate_nimbus_changelog(experiment, self.user, "created", self.first_timestamp)

        experiment.results_data = new_value
        experiment.save()

        generate_nimbus_changelog(
            experiment, self.user, "primary outcomes were added", timestamp_2
        )

        changelogs = list(
            experiment.changes.order_by("-changed_on").prefetch_related("changed_by")
        )

        comparison_log = changelogs[0]
        field_name = "results_data"
        field_diff = {"old_value": old_value, "new_value": new_value}
        change_timestamp = self._create_formatted_timestamp(comparison_log.changed_on)
        field_instance = NimbusExperiment._meta.get_field(field_name)
        field_display_name = (
            field_instance.verbose_name
            if hasattr(field_instance, "verbose_name")
            else field_name
        )

        change = get_formatted_change_object(
            field_name, field_diff, comparison_log, change_timestamp
        )

        expected_change = {
            "event": ChangeEventType.DETAILED.name,
            "event_message": f"{self.user} changed value of {field_display_name}",
            "changed_by": self.user,
            "timestamp": change_timestamp,
            "old_value": json.dumps(old_value, indent=2),
            "new_value": json.dumps(new_value, indent=2),
        }

        self.assertDictEqual(change, expected_change)

    def test_get_boolean_formatted_change_object(self):
        experiment = NimbusExperimentFactory.create(
            slug="experiment-1",
            published_dto={"id": "experiment", "test": False},
        )
        timestamp_2 = self._create_timestamp(2)

        generate_nimbus_changelog(experiment, self.user, "created", self.first_timestamp)

        old_value = False
        new_value = True

        experiment.is_archived = new_value
        experiment.save()

        generate_nimbus_changelog(
            experiment, self.user, "experiment was archived", timestamp_2
        )

        changelogs = list(
            experiment.changes.order_by("-changed_on").prefetch_related("changed_by")
        )

        comparison_log = changelogs[0]
        field_name = "is_archived"
        field_diff = {"old_value": old_value, "new_value": new_value}
        change_timestamp = self._create_formatted_timestamp(comparison_log.changed_on)
        field_instance = NimbusExperiment._meta.get_field(field_name)
        field_display_name = (
            field_instance.verbose_name
            if hasattr(field_instance, "verbose_name")
            else field_name
        )

        change = get_formatted_change_object(
            field_name, field_diff, comparison_log, change_timestamp
        )

        expected_change = {
            "event": ChangeEventType.BOOLEAN.name,
            "event_message": f"{self.user} set the {field_display_name} as {new_value}",
            "changed_by": self.user,
            "timestamp": change_timestamp,
            "old_value": old_value,
            "new_value": new_value,
        }

        self.assertDictEqual(change, expected_change)
