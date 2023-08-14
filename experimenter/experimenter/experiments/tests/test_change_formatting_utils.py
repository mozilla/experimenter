import json
import pprint

from django.test import TestCase
from django.utils import timezone

from experimenter.base.tests.factories import CountryFactory
from experimenter.experiments.changelog_utils import (
    generate_nimbus_changelog,
    get_formatted_change_object,
)
from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tests.factories import (
    NimbusExperimentFactory,
    NimbusFeatureConfigFactory,
)
from experimenter.openidc.tests.factories import UserFactory


class TestChangeFormattingMethod(TestCase):
    def test_get_default_formatted_change_object(self):
        experiment = NimbusExperimentFactory.create(
            slug="experiment-1",
            published_dto={"id": "experiment", "test": False},
        )
        user = UserFactory.create()
        time_format = "%I:%M:%S %p"
        current_date = timezone.now().date()

        timestamp_1 = timezone.make_aware(
            timezone.datetime.combine(current_date, timezone.datetime.min.time())
        )
        timestamp_1.strftime(time_format)

        timestamp_2 = timestamp_1 + timezone.timedelta(hours=2)
        timestamp_2.strftime(time_format)

        timestamp_3 = timestamp_2 + timezone.timedelta(hours=2)
        timestamp_3.strftime(time_format)

        generate_nimbus_changelog(experiment, user, "created", timestamp_1)

        new_value = NimbusExperiment.PublishStatus.IDLE
        old_value = NimbusExperiment.PublishStatus.REVIEW

        experiment.publish_status = old_value
        experiment.save()

        generate_nimbus_changelog(experiment, user, "publish_status change", timestamp_2)

        experiment.publish_status = new_value
        experiment.save()

        generate_nimbus_changelog(experiment, user, "status_next change", timestamp_3)

        changelogs = list(
            experiment.changes.order_by("-changed_on").prefetch_related("changed_by")
        )

        comparison_log = changelogs[0]
        field_name = "publish_status"
        field_diff = {"old_value": old_value, "new_value": new_value}
        timestamp = comparison_log.changed_on.strftime(time_format)
        field_instance = NimbusExperiment._meta.get_field(field_name)
        field_display_name = (
            field_instance.verbose_name
            if hasattr(field_instance, "verbose_name")
            else field_name
        )

        change = get_formatted_change_object(
            field_name, field_diff, comparison_log, timestamp
        )

        expected_change = {
            "event": "STATE",
            "event_message": (
                f"{user.get_full_name()} "
                f"changed value of {field_display_name} from "
                f"{old_value} to {new_value}"
            ),
            "changed_by": user.get_full_name(),
            "timestamp": timestamp,
            "old_value": old_value,
            "new_value": new_value,
        }

        self.assertDictEqual(change, expected_change)

    def test_formatting_for_native_models_field(self):
        experiment = NimbusExperimentFactory.create(
            slug="experiment-1",
            published_dto={"id": "experiment", "test": False},
        )
        user = UserFactory.create()
        time_format = "%I:%M:%S %p"
        current_date = timezone.now().date()
        country_ca = CountryFactory.create(code="CA")
        country_us = CountryFactory.create(code="US")

        timestamp_1 = timezone.make_aware(
            timezone.datetime.combine(current_date, timezone.datetime.min.time())
        )
        timestamp_1.strftime(time_format)

        timestamp_2 = timestamp_1 + timezone.timedelta(hours=2)
        timestamp_2.strftime(time_format)

        generate_nimbus_changelog(experiment, user, "created", timestamp_1)

        old_value = []
        new_value = [country_us.pk, country_ca.pk]
        transformed_value = sorted([country_ca.name, country_us.name])

        experiment.countries.set(new_value)
        experiment.save()

        generate_nimbus_changelog(experiment, user, "countries were added", timestamp_2)

        changelogs = list(
            experiment.changes.order_by("-changed_on").prefetch_related("changed_by")
        )

        comparison_log = changelogs[0]
        field_name = "countries"
        field_diff = {"old_value": old_value, "new_value": new_value}
        timestamp = comparison_log.changed_on.strftime(time_format)
        field_instance = NimbusExperiment._meta.get_field(field_name)
        field_display_name = (
            field_instance.verbose_name
            if hasattr(field_instance, "verbose_name")
            else field_name
        )

        change = get_formatted_change_object(
            field_name, field_diff, comparison_log, timestamp
        )

        expected_change = {
            "event": "DETAILED",
            "event_message": (
                f"{user.get_full_name()} " f"changed value of {field_display_name}"
            ),
            "changed_by": user.get_full_name(),
            "timestamp": timestamp,
            "old_value": json.dumps(pprint.pformat(old_value, width=40, indent=2)),
            "new_value": json.dumps(
                pprint.pformat(transformed_value, width=40, indent=2)
            ),
        }

        self.assertDictEqual(change, expected_change)

    def test_formatting_for_custom_models_field(self):
        experiment = NimbusExperimentFactory.create(
            slug="experiment-1",
            published_dto={"id": "experiment", "test": False},
        )
        user = UserFactory.create()
        time_format = "%I:%M:%S %p"
        current_date = timezone.now().date()
        feature = NimbusFeatureConfigFactory(slug="feature")
        fields = feature._meta.fields

        # Convert the feature object to dictionary as it is stored as such in the
        # experiment_data of a NimbusChangeLog

        feature_dict = {}
        for field in fields:
            field_name = field.name
            field_value = getattr(feature, field_name)
            feature_dict[field_name] = field_value

        timestamp_1 = timezone.make_aware(
            timezone.datetime.combine(current_date, timezone.datetime.min.time())
        )
        timestamp_1.strftime(time_format)

        timestamp_2 = timestamp_1 + timezone.timedelta(hours=2)
        timestamp_2.strftime(time_format)

        generate_nimbus_changelog(experiment, user, "created", timestamp_1)

        old_value = []
        new_value = [feature_dict]

        experiment.feature_configs.set([feature])
        experiment.save()

        generate_nimbus_changelog(experiment, user, "features were added", timestamp_2)

        changelogs = list(
            experiment.changes.order_by("-changed_on").prefetch_related("changed_by")
        )

        comparison_log = changelogs[0]
        field_name = "feature_configs"
        field_diff = {"old_value": old_value, "new_value": new_value}
        timestamp = comparison_log.changed_on.strftime(time_format)
        field_instance = NimbusExperiment._meta.get_field(field_name)
        field_display_name = (
            field_instance.verbose_name
            if hasattr(field_instance, "verbose_name")
            else field_name
        )

        change = get_formatted_change_object(
            field_name, field_diff, comparison_log, timestamp
        )

        expected_change = {
            "event": "DETAILED",
            "event_message": (
                f"{user.get_full_name()} " f"changed value of {field_display_name}"
            ),
            "changed_by": user.get_full_name(),
            "timestamp": timestamp,
            "old_value": [json.dumps(config, indent=4) for config in old_value],
            "new_value": [json.dumps(config, indent=4) for config in new_value],
        }

        self.assertDictEqual(change, expected_change)

    def test_formatting_for_array_fields(self):
        experiment = NimbusExperimentFactory.create(
            slug="experiment-1",
            published_dto={"id": "experiment", "test": False},
        )
        user = UserFactory.create()
        time_format = "%I:%M:%S %p"
        current_date = timezone.now().date()

        timestamp_1 = timezone.make_aware(
            timezone.datetime.combine(current_date, timezone.datetime.min.time())
        )
        timestamp_1.strftime(time_format)

        timestamp_2 = timestamp_1 + timezone.timedelta(hours=2)
        timestamp_2.strftime(time_format)

        generate_nimbus_changelog(experiment, user, "created", timestamp_1)

        old_value = []
        new_value = ["test-outcome"]

        experiment.primary_outcomes = new_value
        experiment.save()

        generate_nimbus_changelog(
            experiment, user, "primary outcomes were added", timestamp_2
        )

        changelogs = list(
            experiment.changes.order_by("-changed_on").prefetch_related("changed_by")
        )

        comparison_log = changelogs[0]
        field_name = "primary_outcomes"
        field_diff = {"old_value": old_value, "new_value": new_value}
        timestamp = comparison_log.changed_on.strftime(time_format)
        field_instance = NimbusExperiment._meta.get_field(field_name)
        field_display_name = (
            field_instance.verbose_name
            if hasattr(field_instance, "verbose_name")
            else field_name
        )

        change = get_formatted_change_object(
            field_name, field_diff, comparison_log, timestamp
        )

        expected_change = {
            "event": "DETAILED",
            "event_message": (
                f"{user.get_full_name()} " f"changed value of {field_display_name}"
            ),
            "changed_by": user.get_full_name(),
            "timestamp": timestamp,
            "old_value": json.dumps(pprint.pformat(old_value, width=40, indent=2)),
            "new_value": json.dumps(pprint.pformat(new_value, width=40, indent=2)),
        }

        self.assertDictEqual(change, expected_change)

    def test_formatting_for_JSON_fields(self):
        experiment = NimbusExperimentFactory.create(
            slug="experiment-1",
            published_dto={"id": "experiment", "test": False},
        )
        user = UserFactory.create()
        time_format = "%I:%M:%S %p"
        current_date = timezone.now().date()

        old_value = {}
        new_value = {"v2": {"overall": {"enrollments": {"all": {}}}}}

        timestamp_1 = timezone.make_aware(
            timezone.datetime.combine(current_date, timezone.datetime.min.time())
        )
        timestamp_1.strftime(time_format)

        timestamp_2 = timestamp_1 + timezone.timedelta(hours=2)
        timestamp_2.strftime(time_format)

        generate_nimbus_changelog(experiment, user, "created", timestamp_1)

        experiment.results_data = new_value
        experiment.save()

        generate_nimbus_changelog(
            experiment, user, "primary outcomes were added", timestamp_2
        )

        changelogs = list(
            experiment.changes.order_by("-changed_on").prefetch_related("changed_by")
        )

        comparison_log = changelogs[0]
        field_name = "results_data"
        field_diff = {"old_value": old_value, "new_value": new_value}
        timestamp = comparison_log.changed_on.strftime(time_format)
        field_instance = NimbusExperiment._meta.get_field(field_name)
        field_display_name = (
            field_instance.verbose_name
            if hasattr(field_instance, "verbose_name")
            else field_name
        )

        change = get_formatted_change_object(
            field_name, field_diff, comparison_log, timestamp
        )

        expected_change = {
            "event": "DETAILED",
            "event_message": (
                f"{user.get_full_name()} " f"changed value of {field_display_name}"
            ),
            "changed_by": user.get_full_name(),
            "timestamp": timestamp,
            "old_value": json.dumps(old_value, indent=4),
            "new_value": json.dumps(new_value, indent=4),
        }

        self.assertDictEqual(change, expected_change)

    def test_get_boolean_formatted_change_object(self):
        experiment = NimbusExperimentFactory.create(
            slug="experiment-1",
            published_dto={"id": "experiment", "test": False},
        )
        user = UserFactory.create()
        time_format = "%I:%M:%S %p"
        current_date = timezone.now().date()

        timestamp_1 = timezone.make_aware(
            timezone.datetime.combine(current_date, timezone.datetime.min.time())
        )
        timestamp_1.strftime(time_format)

        timestamp_2 = timestamp_1 + timezone.timedelta(hours=2)
        timestamp_2.strftime(time_format)

        generate_nimbus_changelog(experiment, user, "created", timestamp_1)

        old_value = False
        new_value = True

        experiment.is_archived = new_value
        experiment.save()

        generate_nimbus_changelog(
            experiment, user, "experiment was archived", timestamp_2
        )

        changelogs = list(
            experiment.changes.order_by("-changed_on").prefetch_related("changed_by")
        )

        comparison_log = changelogs[0]
        field_name = "is_archived"
        field_diff = {"old_value": old_value, "new_value": new_value}
        timestamp = comparison_log.changed_on.strftime(time_format)
        field_instance = NimbusExperiment._meta.get_field(field_name)
        field_display_name = (
            field_instance.verbose_name
            if hasattr(field_instance, "verbose_name")
            else field_name
        )

        change = get_formatted_change_object(
            field_name, field_diff, comparison_log, timestamp
        )

        expected_change = {
            "event": "BOOLEAN",
            "event_message": (
                f"{user.get_full_name()} "
                f"set the {field_display_name} "
                f"as {new_value}"
            ),
            "changed_by": user.get_full_name(),
            "timestamp": timestamp,
            "old_value": old_value,
            "new_value": new_value,
        }

        self.assertDictEqual(change, expected_change)
