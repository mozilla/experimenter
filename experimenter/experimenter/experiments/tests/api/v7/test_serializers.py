import datetime
import json

from django.conf import settings
from django.test import TestCase

from experimenter.base.tests.factories import LocaleFactory
from experimenter.experiments.api.v7.serializers import NimbusExperimentSerializer
from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tests.factories import (
    NimbusExperimentFactory,
    NimbusFeatureConfigFactory,
)


class TestNimbusExperimentSerializer(TestCase):
    maxDiff = None

    def test_serializer_outputs_expected_schema(self):
        locale_en_us = LocaleFactory.create(code="en-US")
        application = NimbusExperiment.Application.DESKTOP
        feature1 = NimbusFeatureConfigFactory.create(application=application)
        feature2 = NimbusFeatureConfigFactory.create(application=application)
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
            application=application,
            firefox_min_version=NimbusExperiment.MIN_REQUIRED_VERSION,
            feature_configs=[feature1, feature2],
            targeting_config_slug=NimbusExperiment.TargetingConfig.NO_TARGETING,
            channel=NimbusExperiment.Channel.NIGHTLY,
            primary_outcomes=["foo", "bar", "baz"],
            secondary_outcomes=["quux", "xyzzy"],
            locales=[locale_en_us],
            _enrollment_end_date=datetime.date(2022, 1, 5),
        )
        serializer = NimbusExperimentSerializer(experiment)
        experiment_data = serializer.data.copy()
        bucket_data = dict(experiment_data.pop("bucketConfig"))
        branches_data = [dict(b) for b in experiment_data.pop("branches")]
        feature_ids_data = experiment_data.pop("featureIds")

        assert experiment.start_date
        assert experiment.actual_enrollment_end_date
        assert experiment.end_date

        min_required_version = NimbusExperiment.MIN_REQUIRED_VERSION

        self.assertDictEqual(
            experiment_data,
            {
                "arguments": {},
                "application": "firefox-desktop",
                "appName": "firefox_desktop",
                "appId": "firefox-desktop",
                "channel": "nightly",
                # DRF manually replaces the isoformat suffix so we have to do the same
                "startDate": experiment.start_date.isoformat().replace("+00:00", "Z"),
                "enrollmentEndDate": (
                    experiment.actual_enrollment_end_date.isoformat().replace(
                        "+00:00", "Z"
                    )
                ),
                "endDate": experiment.end_date.isoformat().replace("+00:00", "Z"),
                "id": experiment.slug,
                "isEnrollmentPaused": True,
                "isRollout": False,
                "proposedDuration": experiment.proposed_duration,
                "proposedEnrollment": experiment.proposed_enrollment,
                "referenceBranch": experiment.reference_branch.slug,
                "schemaVersion": settings.NIMBUS_SCHEMA_VERSION,
                "slug": experiment.slug,
                "targeting": (
                    f'(browserSettings.update.channel == "nightly") '
                    f"&& (version|versionCompare('{min_required_version}') >= 0) "
                    f"&& (locale in ['en-US'])"
                ),
                "userFacingDescription": experiment.public_description,
                "userFacingName": experiment.name,
                "probeSets": [],
                "outcomes": [
                    {"priority": "primary", "slug": "foo"},
                    {"priority": "primary", "slug": "bar"},
                    {"priority": "primary", "slug": "baz"},
                    {"priority": "secondary", "slug": "quux"},
                    {"priority": "secondary", "slug": "xyzzy"},
                ],
                "featureValidationOptOut": experiment.is_client_schema_disabled,
                "locales": ["en-US"],
                "publishedDate": experiment.published_date,
            },
        )

        self.assertEqual(set(feature_ids_data), {feature1.slug, feature2.slug})

        self.assertEqual(
            bucket_data,
            {
                "randomizationUnit": (
                    experiment.bucket_range.isolation_group.randomization_unit
                ),
                "namespace": experiment.bucket_range.isolation_group.namespace,
                "start": experiment.bucket_range.start,
                "count": experiment.bucket_range.count,
                "total": experiment.bucket_range.isolation_group.total,
            },
        )

        self.assertEqual(len(branches_data), 2)
        for branch in experiment.branches.all():
            self.assertIn(
                {
                    "slug": branch.slug,
                    "ratio": branch.ratio,
                    "description": branch.description,
                    "features": [
                        {
                            "featureId": fv.feature_config.slug,
                            "value": json.loads(fv.value),
                        }
                        for fv in branch.feature_values.all()
                    ],
                    "screenshots": [s.image.url for s in branch.screenshots.all()],
                },
                branches_data,
            )
