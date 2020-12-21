import json

from django.conf import settings
from django.test import TestCase
from mozilla_nimbus_shared import check_schema

from experimenter.experiments.api.v6.serializers import (
    NimbusExperimentSerializer,
    NimbusProbeSetSerializer,
)
from experimenter.experiments.models import NimbusExperiment
from experimenter.experiments.tests.factories import (
    NimbusExperimentFactory,
    NimbusProbeSetFactory,
)
from experimenter.experiments.tests.factories.nimbus import NimbusBranchFactory


class TestNimbusExperimentSerializer(TestCase):
    maxDiff = None

    def test_serializer_outputs_expected_schema_with_feature(self):
        probe_set = NimbusProbeSetFactory.create()
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.COMPLETE,
            application=NimbusExperiment.Application.DESKTOP,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_80,
            targeting_config_slug=NimbusExperiment.TargetingConfig.ALL_ENGLISH,
            channel=NimbusExperiment.Channel.DESKTOP_NIGHTLY,
            probe_sets=[probe_set],
        )

        serializer = NimbusExperimentSerializer(experiment)
        all_experiment_data = serializer.data.copy()
        arguments_data = all_experiment_data.pop("arguments")
        for experiment_data in arguments_data, all_experiment_data:
            branches_data = [dict(b) for b in experiment_data.pop("branches")]

            self.assertEqual(
                experiment_data,
                {
                    "application": experiment.application,
                    "channel": experiment.channel,
                    "bucketConfig": {
                        "randomizationUnit": (
                            experiment.bucket_range.isolation_group.randomization_unit
                        ),
                        "namespace": experiment.bucket_range.isolation_group.namespace,
                        "start": experiment.bucket_range.start,
                        "count": experiment.bucket_range.count,
                        "total": experiment.bucket_range.isolation_group.total,
                    },
                    # DRF manually replaces the isoformat suffix so we have to do the same
                    "endDate": experiment.end_date.isoformat().replace("+00:00", "Z"),
                    "id": experiment.slug,
                    "isEnrollmentPaused": False,
                    "proposedDuration": experiment.proposed_duration,
                    "proposedEnrollment": experiment.proposed_enrollment,
                    "referenceBranch": experiment.reference_branch.slug,
                    "schemaVersion": settings.NIMBUS_SCHEMA_VERSION,
                    "slug": experiment.slug,
                    # DRF manually replaces the isoformat suffix so we have to do the same
                    "startDate": experiment.start_date.isoformat().replace("+00:00", "Z"),
                    "targeting": (
                        'browserSettings.update.channel == "nightly" '
                        "&& version|versionCompare('80.!') >= 0 "
                        "&& localeLanguageCode == 'en' "
                        "&& 'app.shield.optoutstudies.enabled'|preferenceValue"
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
                            "value": json.loads(branch.feature_value),
                        },
                    },
                    branches_data,
                )

        check_schema("experiments/NimbusExperiment", serializer.data)

    def test_serializers_with_feature_value_None(self):
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.ACCEPTED,
            branches=[],
        )
        experiment.reference_branch = NimbusBranchFactory(
            experiment=experiment, feature_value=None
        )
        experiment.save()
        serializer = NimbusExperimentSerializer(experiment)
        self.assertIsNone(serializer.data["branches"][0]["feature"]["value"])
        check_schema("experiments/NimbusExperiment", serializer.data)

    def test_sets_application_channel_for_fenix_experiment(self):
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.ACCEPTED,
            application=NimbusExperiment.Application.FENIX,
            channel=NimbusExperiment.Channel.FENIX_NIGHTLY,
        )
        serializer = NimbusExperimentSerializer(experiment)
        self.assertEqual(
            serializer.data["application"], NimbusExperiment.Channel.FENIX_NIGHTLY
        )
        self.assertEqual(
            serializer.data["channel"], NimbusExperiment.Channel.FENIX_NIGHTLY
        )
        check_schema("experiments/NimbusExperiment", serializer.data)

    def test_serializer_outputs_expected_schema_without_feature(self):
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.ACCEPTED,
            feature_config=None,
        )
        serializer = NimbusExperimentSerializer(experiment)
        experiment_data = serializer.data.copy()
        branches_data = [dict(b) for b in experiment_data.pop("branches")]
        self.assertEqual(len(branches_data), 2)
        for branch in experiment.branches.all():
            self.assertIn(
                {"slug": branch.slug, "ratio": branch.ratio},
                branches_data,
            )

        check_schema("experiments/NimbusExperiment", serializer.data)

    # TODO: disabled until EXP-786 is closed
    # def test_serializer_outputs_targeting_for_experiment_without_channels(self):
    #     experiment = NimbusExperimentFactory.create_with_status(
    #         NimbusExperiment.Status.ACCEPTED,
    #         firefox_min_version=NimbusExperiment.Version.FIREFOX_80,
    #         targeting_config_slug=NimbusExperiment.TargetingConfig.ALL_ENGLISH,
    #         application=NimbusExperiment.Application.DESKTOP,
    #         channel=None,
    #     )

    #     serializer = NimbusExperimentSerializer(experiment)
    #     self.assertEqual(
    #         serializer.data["targeting"],
    #         (
    #             "version|versionCompare('80.!') >= 0 "
    #             "&& localeLanguageCode == 'en' "
    #             "&& 'app.shield.optoutstudies.enabled'|preferenceValue"
    #         ),
    #     )
    #     check_schema("experiments/NimbusExperiment", serializer.data)

    def test_serializer_outputs_targeting_for_experiment_without_firefox_min_version(
        self,
    ):
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.ACCEPTED,
            firefox_min_version=None,
            targeting_config_slug=NimbusExperiment.TargetingConfig.ALL_ENGLISH,
            channel=NimbusExperiment.Channel.DESKTOP_NIGHTLY,
        )

        serializer = NimbusExperimentSerializer(experiment)
        self.assertEqual(
            serializer.data["targeting"],
            (
                'browserSettings.update.channel == "nightly" '
                "&& localeLanguageCode == 'en' "
                "&& 'app.shield.optoutstudies.enabled'|preferenceValue"
            ),
        )
        check_schema("experiments/NimbusExperiment", serializer.data)


class TestNimbusProbeSetSerializer(TestCase):
    def test_outputs_expected_schema(self):
        probeset = NimbusProbeSetFactory()

        probeset_data = dict(NimbusProbeSetSerializer(probeset).data)
        probes_data = [dict(p) for p in probeset_data.pop("probes")]

        self.assertEqual(
            probeset_data,
            {
                "name": probeset.name,
                "slug": probeset.slug,
            },
        )
        self.assertEqual(len(probes_data), probeset.probes.count())
        for probe in probeset.probes.all():
            self.assertIn(
                {
                    "name": probe.name,
                    "kind": probe.kind,
                    "event_category": probe.event_category,
                    "event_method": probe.event_method,
                    "event_object": probe.event_object,
                    "event_value": probe.event_value,
                },
                probes_data,
            )
