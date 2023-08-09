import pytest
from django.test import TestCase
from django.utils import timezone

from experimenter.base.tests.factories import CountryFactory
from experimenter.experiments.changelog_utils import (
    generate_nimbus_changelog,
    get_formatted_change_object,
)
from experimenter.experiments.constants import NimbusConstants
from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tests.factories import NimbusExperimentFactory
from experimenter.openidc.tests.factories import UserFactory


@pytest.mark.parametrize(
    "event, value",
    [
        (NimbusConstants.ChangeEvent.TRIVIAL, "TRIVIAL"),
        (NimbusConstants.ChangeEvent.STATUS, "STATE"),
        (NimbusConstants.ChangeEvent.PUBLISH_STATUS, "STATE"),
        (NimbusConstants.ChangeEvent.IS_PAUSED, "BOOLEAN"),
        (NimbusConstants.ChangeEvent.IS_ARCHIVED, "BOOLEAN"),
        (NimbusConstants.ChangeEvent.POPULATION_PERCENTAGE, "DYNAMIC"),
        (NimbusConstants.ChangeEvent.RESULTS_DATA, "DETAILED"),
        (NimbusConstants.ChangeEvent.FEATURE_CONFIGS, "DETAILED"),
        (NimbusConstants.ChangeEvent.IS_ROLLOUT, "BOOLEAN"),
        (NimbusConstants.ChangeEvent.PUBLIC_DESCRIPTION, "GENERAL"),
        (NimbusConstants.ChangeEvent.PROPOSED_DURATION, "GENERAL"),
        (NimbusConstants.ChangeEvent.PROPOSED_ENROLLMENT, "GENERAL"),
        (NimbusConstants.ChangeEvent.TOTAL_ENROLLED_CLIENTS, "GENERAL"),
        (NimbusConstants.ChangeEvent.FIREFOX_MIN_VERSION, "GENERAL"),
        (NimbusConstants.ChangeEvent.FIREFOX_MAX_VERSION, "GENERAL"),
        (NimbusConstants.ChangeEvent.APPLICATION, "GENERAL"),
        (NimbusConstants.ChangeEvent.CHANNEL, "GENERAL"),
        (NimbusConstants.ChangeEvent.LOCALES, "LIST"),
        (NimbusConstants.ChangeEvent.COUNTRIES, "LIST"),
        (NimbusConstants.ChangeEvent.LANGUAGES, "LIST"),
        (NimbusConstants.ChangeEvent.PROJECTS, "LIST"),
        (NimbusConstants.ChangeEvent.PRIMARY_OUTCOMES, "LIST"),
        (NimbusConstants.ChangeEvent.SECONDARY_OUTCOMES, "LIST"),
        (NimbusConstants.ChangeEvent._START_DATE, "DATE_TIME"),
        (NimbusConstants.ChangeEvent._END_DATE, "DATE_TIME"),
        (NimbusConstants.ChangeEvent._ENROLLMENT_END_DATE, "DATE_TIME"),
        (NimbusConstants.ChangeEvent.PROPOSED_RELEASE_DATE, "DATE_TIME"),
        (NimbusConstants.ChangeEvent.REQUIRED_EXPERIMENTS, "LIST"),
        (NimbusConstants.ChangeEvent.EXCLUDED_EXPERIMENTS, "LIST"),
        (NimbusConstants.ChangeEvent.REFERENCE_BRANCH, "DETAILED"),
        (NimbusConstants.ChangeEvent.TARGETING_CONFIG_SLUG, "GENERAL"),
        (NimbusConstants.ChangeEvent.RISK_BRAND, "BOOLEAN"),
        (NimbusConstants.ChangeEvent.RISK_REVENUE, "BOOLEAN"),
        (NimbusConstants.ChangeEvent.RISK_PARTNER_RELATED, "BOOLEAN"),
        (NimbusConstants.ChangeEvent.CONCLUSION_RECOMMENDATION, "GENERAL"),
        (NimbusConstants.ChangeEvent.TAKEAWAYS_SUMMARY, "GENERAL"),
        (NimbusConstants.ChangeEvent.IS_FIRST_RUN, "BOOLEAN"),
        (NimbusConstants.ChangeEvent.IS_CLIENT_SCHEMA_DISABLED, "BOOLEAN"),
        (NimbusConstants.ChangeEvent.LOCALIZATIONS, "GENERAL"),
        (NimbusConstants.ChangeEvent.IS_LOCALIZED, "BOOLEAN"),
        (NimbusConstants.ChangeEvent.PREVENT_PREF_CONFLICTS, "BOOLEAN"),
        (NimbusConstants.ChangeEvent.HYPOTHESIS, "GENERAL"),
    ],
)
def test_enum_values(event, value):
    assert event.value == value


@pytest.mark.parametrize(
    "event, display_name",
    [
        (NimbusConstants.ChangeEvent.TRIVIAL, "Trivial Change"),
        (NimbusConstants.ChangeEvent.STATUS, "Status"),
        (NimbusConstants.ChangeEvent.PUBLISH_STATUS, "Publish status"),
        (NimbusConstants.ChangeEvent.IS_PAUSED, "Pause enrollment flag"),
        (NimbusConstants.ChangeEvent.IS_ARCHIVED, "Archive experiment flag"),
        (NimbusConstants.ChangeEvent.POPULATION_PERCENTAGE, "Population percentage"),
        (NimbusConstants.ChangeEvent.RESULTS_DATA, "Results"),
        (
            NimbusConstants.ChangeEvent.FEATURE_CONFIGS,
            "Experiment's feature configuration",
        ),
        (NimbusConstants.ChangeEvent.IS_ROLLOUT, "isRollout flag"),
        (NimbusConstants.ChangeEvent.PUBLIC_DESCRIPTION, "Experiment's description"),
        (
            NimbusConstants.ChangeEvent.PROPOSED_DURATION,
            "Experiment's expected duration",
        ),
        (
            NimbusConstants.ChangeEvent.PROPOSED_ENROLLMENT,
            "Expected number of enrolled clients",
        ),
        (
            NimbusConstants.ChangeEvent.TOTAL_ENROLLED_CLIENTS,
            "Total number of enrolled clients",
        ),
        (NimbusConstants.ChangeEvent.FIREFOX_MIN_VERSION, "Minimum firefox version"),
        (NimbusConstants.ChangeEvent.FIREFOX_MAX_VERSION, "Maximum firefox version"),
        (NimbusConstants.ChangeEvent.APPLICATION, "Application type"),
        (NimbusConstants.ChangeEvent.CHANNEL, "Channel type"),
        (NimbusConstants.ChangeEvent.LOCALES, "Supported locales"),
        (NimbusConstants.ChangeEvent.COUNTRIES, "Supported countries"),
        (NimbusConstants.ChangeEvent.LANGUAGES, "Supported languages"),
        (NimbusConstants.ChangeEvent.PROJECTS, "Supported projects"),
        (
            NimbusConstants.ChangeEvent.PRIMARY_OUTCOMES,
            "Experiment's primary outcomes",
        ),
        (
            NimbusConstants.ChangeEvent.SECONDARY_OUTCOMES,
            "Experiment's secondary outcomes",
        ),
        (NimbusConstants.ChangeEvent._START_DATE, "Experiment's start date"),
        (NimbusConstants.ChangeEvent._END_DATE, "Experiment's end date"),
        (
            NimbusConstants.ChangeEvent._ENROLLMENT_END_DATE,
            "Last date for Enrollment",
        ),
        (
            NimbusConstants.ChangeEvent.PROPOSED_RELEASE_DATE,
            "Expected experiment release date",
        ),
        (
            NimbusConstants.ChangeEvent.REQUIRED_EXPERIMENTS,
            "List of required experiments",
        ),
        (
            NimbusConstants.ChangeEvent.EXCLUDED_EXPERIMENTS,
            "List of excluded experiments",
        ),
        (
            NimbusConstants.ChangeEvent.REFERENCE_BRANCH,
            "Experiment's reference branch",
        ),
        (NimbusConstants.ChangeEvent.TARGETING_CONFIG_SLUG, "Experiment's targeting"),
        (NimbusConstants.ChangeEvent.RISK_BRAND, "Is a brand risk flag"),
        (NimbusConstants.ChangeEvent.RISK_REVENUE, "Is a revenue risk flag"),
        (NimbusConstants.ChangeEvent.RISK_PARTNER_RELATED, "Is a Brand risk flag"),
        (
            NimbusConstants.ChangeEvent.CONCLUSION_RECOMMENDATION,
            "Experiment's conclusion",
        ),
        (NimbusConstants.ChangeEvent.TAKEAWAYS_SUMMARY, "Experiment's takeaways"),
        (NimbusConstants.ChangeEvent.IS_FIRST_RUN, "Is first run flag"),
        (
            NimbusConstants.ChangeEvent.IS_CLIENT_SCHEMA_DISABLED,
            "Is client schema disabled flag",
        ),
        (NimbusConstants.ChangeEvent.LOCALIZATIONS, "Experiment's localizations"),
        (NimbusConstants.ChangeEvent.IS_LOCALIZED, "Is experiment localized flag"),
        (
            NimbusConstants.ChangeEvent.PREVENT_PREF_CONFLICTS,
            "Prevent preference conflicts flag",
        ),
        (NimbusConstants.ChangeEvent.HYPOTHESIS, "Experiment's hypothesis"),
    ],
)
def test_display_name(event, display_name):
    assert event.display_name == display_name


class TestChangeEventUtils(TestCase):
    def test_find_invalid_enum_by_key(self):
        self.assertEqual(
            NimbusConstants.ChangeEvent.find_enum_by_key("INVALID_KEY"),
            NimbusConstants.ChangeEvent.TRIVIAL,
        )


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

        experiment.publish_status = NimbusExperiment.PublishStatus.REVIEW
        experiment.save()

        generate_nimbus_changelog(experiment, user, "publish_status change", timestamp_2)

        experiment.publish_status = NimbusExperiment.PublishStatus.IDLE
        experiment.save()

        generate_nimbus_changelog(experiment, user, "status_next change", timestamp_3)

        changelogs = list(
            experiment.changes.order_by("-changed_on").prefetch_related("changed_by")
        )

        comparison_log = changelogs[0]
        field_name = "publish_status"
        field_diff = {"old_value": "Review", "new_value": "Idle"}
        timestamp = comparison_log.changed_on.strftime(time_format)

        change = get_formatted_change_object(
            field_name, field_diff, comparison_log, timestamp
        )

        expected_change = {
            "event": NimbusConstants.ChangeEvent.PUBLISH_STATUS.value,
            "event_message": (
                f"{user.get_full_name()} "
                f"changed value of Publish status from "
                f"Review to Idle"
            ),
            "changed_by": user.get_full_name(),
            "timestamp": timestamp,
        }

        self.assertDictEqual(change, expected_change)

    def test_get_detailed_formatted_change_object(self):
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

        experiment.countries.set([country_ca, country_us])
        experiment.save()

        generate_nimbus_changelog(experiment, user, "countries were added", timestamp_2)

        changelogs = list(
            experiment.changes.order_by("-changed_on").prefetch_related("changed_by")
        )

        comparison_log = changelogs[0]
        field_name = "countries"
        field_diff = {"old_value": [], "new_value": [country_ca, country_us]}
        timestamp = comparison_log.changed_on.strftime(time_format)

        change = get_formatted_change_object(
            field_name, field_diff, comparison_log, timestamp
        )

        expected_change = {
            "event": NimbusConstants.ChangeEvent.COUNTRIES.value,
            "event_message": (
                f"{user.get_full_name()} "
                f"changed value of {NimbusConstants.ChangeEvent.COUNTRIES.display_name}"
            ),
            "changed_by": user.get_full_name(),
            "timestamp": timestamp,
            "old_value": [],
            "new_value": [country_ca, country_us],
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

        experiment.is_archived = True
        experiment.save()

        generate_nimbus_changelog(
            experiment, user, "experiment was archived", timestamp_2
        )

        changelogs = list(
            experiment.changes.order_by("-changed_on").prefetch_related("changed_by")
        )

        comparison_log = changelogs[0]
        field_name = "is_archived"
        field_diff = {"old_value": False, "new_value": True}
        timestamp = comparison_log.changed_on.strftime(time_format)

        change = get_formatted_change_object(
            field_name, field_diff, comparison_log, timestamp
        )

        expected_change = {
            "event": NimbusConstants.ChangeEvent.IS_ARCHIVED.value,
            "event_message": (
                f"{user.get_full_name()} "
                f"set the {NimbusConstants.ChangeEvent.IS_ARCHIVED.display_name} "
                f"as True"
            ),
            "changed_by": user.get_full_name(),
            "timestamp": timestamp,
        }

        self.assertDictEqual(change, expected_change)
