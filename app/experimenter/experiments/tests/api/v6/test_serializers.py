from django.test import TestCase

from experimenter.experiments.api.v6.serializers import NimbusExperimentSerializer
from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tests.factories import (
    NimbusExperimentFactory,
    NimbusProbeSetFactory,
)


class TestNimbusExperimentSerializer(TestCase):
    maxDiff = None

    def test_serializer_outputs_expected_schema_for_draft(self):
        probe_set = NimbusProbeSetFactory.create()
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.DRAFT,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_80,
            targeting_config_slug=NimbusExperiment.TargetingConfig.ALL_ENGLISH,
            channels=[
                NimbusExperiment.Channel.DESKTOP_NIGHTLY,
                NimbusExperiment.Channel.DESKTOP_BETA,
                NimbusExperiment.Channel.DESKTOP_RELEASE,
            ],
            probe_sets=[probe_set],
        )

        serializer = NimbusExperimentSerializer(experiment)
        experiment_data = serializer.data.copy()
        branches_data = experiment_data.pop("branches")
        self.assertDictEqual(
            experiment_data,
            {
                "application": experiment.application,
                "bucketConfig": None,
                "endDate": None,
                "id": experiment.slug,
                "isEnrollmentPaused": False,
                "proposedDuration": experiment.proposed_duration,
                "proposedEnrollment": experiment.proposed_enrollment,
                "referenceBranch": experiment.control_branch.slug,
                "slug": experiment.slug,
                "startDate": None,
                "targeting": (
                    'channel in ["Nightly", "Beta", "Release"] && '
                    "version|versionCompare('80.!') >= .! && localeLanguageCode == 'en'"
                ),
                "userFacingDescription": experiment.public_description,
                "userFacingName": experiment.name,
                "probeSets": [probe_set.slug],
            },
        )
        self.assertEqual(len(branches_data), 2)
        for branch in experiment.branches.all():
            self.assertIn(
                {
                    "slug": branch.slug,
                    "ratio": branch.ratio,
                    "feature": {
                        "featureId": experiment.feature_config.slug,
                        "enabled": branch.feature_enabled,
                        "value": branch.feature_value,
                    },
                },
                [dict(b) for b in branches_data],
            )

    def test_serializer_outputs_expected_schema_for_accepted(self):
        probe_set = NimbusProbeSetFactory.create()
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.ACCEPTED,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_80,
            targeting_config_slug=NimbusExperiment.TargetingConfig.ALL_ENGLISH,
            channels=[
                NimbusExperiment.Channel.DESKTOP_NIGHTLY,
                NimbusExperiment.Channel.DESKTOP_BETA,
                NimbusExperiment.Channel.DESKTOP_RELEASE,
            ],
            probe_sets=[probe_set],
        )

        serializer = NimbusExperimentSerializer(experiment)
        experiment_data = serializer.data.copy()
        branches_data = experiment_data.pop("branches")
        self.assertDictEqual(
            experiment_data,
            {
                "application": experiment.application,
                "bucketConfig": {
                    "randomizationUnit": (
                        experiment.bucket_range.isolation_group.randomization_unit
                    ),
                    "namespace": experiment.bucket_range.isolation_group.namespace,
                    "start": experiment.bucket_range.start,
                    "count": experiment.bucket_range.count,
                    "total": experiment.bucket_range.isolation_group.total,
                },
                "endDate": None,
                "id": experiment.slug,
                "isEnrollmentPaused": False,
                "proposedDuration": experiment.proposed_duration,
                "proposedEnrollment": experiment.proposed_enrollment,
                "referenceBranch": experiment.control_branch.slug,
                "slug": experiment.slug,
                "startDate": None,
                "targeting": (
                    'channel in ["Nightly", "Beta", "Release"] && '
                    "version|versionCompare('80.!') >= .! && localeLanguageCode == 'en'"
                ),
                "userFacingDescription": experiment.public_description,
                "userFacingName": experiment.name,
                "probeSets": [probe_set.slug],
            },
        )
        self.assertEqual(len(branches_data), 2)
        for branch in experiment.branches.all():
            self.assertIn(
                {
                    "slug": branch.slug,
                    "ratio": branch.ratio,
                    "feature": {
                        "featureId": experiment.feature_config.slug,
                        "enabled": branch.feature_enabled,
                        "value": branch.feature_value,
                    },
                },
                [dict(b) for b in branches_data],
            )

    def test_serializer_outputs_targeting_for_experiment_without_channels(self):
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.DRAFT,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_80,
            targeting_config_slug=NimbusExperiment.TargetingConfig.ALL_ENGLISH,
            channels=[],
        )

        serializer = NimbusExperimentSerializer(experiment)
        self.assertEqual(
            serializer.data["targeting"],
            "version|versionCompare('80.!') >= .! && localeLanguageCode == 'en'",
        )

    def test_serializer_outputs_targeting_for_experiment_without_firefox_min_version(
        self,
    ):
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.DRAFT,
            firefox_min_version=None,
            targeting_config_slug=NimbusExperiment.TargetingConfig.ALL_ENGLISH,
            channels=[
                NimbusExperiment.Channel.DESKTOP_NIGHTLY,
                NimbusExperiment.Channel.DESKTOP_BETA,
                NimbusExperiment.Channel.DESKTOP_RELEASE,
            ],
        )

        serializer = NimbusExperimentSerializer(experiment)
        self.assertEqual(
            serializer.data["targeting"],
            'channel in ["Nightly", "Beta", "Release"] && localeLanguageCode == \'en\'',
        )
