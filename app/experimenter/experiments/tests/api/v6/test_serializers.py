import json

from django.conf import settings
from django.test import TestCase
from mozilla_nimbus_shared import check_schema
from parameterized import parameterized

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
            firefox_min_version=NimbusExperiment.Version.FIREFOX_83,
            targeting_config_slug=NimbusExperiment.TargetingConfig.ALL_ENGLISH,
            channel=NimbusExperiment.Channel.NIGHTLY,
            probe_sets=[probe_set],
        )

        serializer = NimbusExperimentSerializer(experiment)
        experiment_data = serializer.data.copy()
        bucket_data = dict(experiment_data.pop("bucketConfig"))
        branches_data = [dict(b) for b in experiment_data.pop("branches")]

        self.assertDictEqual(
            experiment_data,
            {
                "arguments": {},
                "application": "firefox-desktop",
                "appName": "firefox_desktop",
                "appId": "firefox-desktop",
                "channel": "nightly",
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
                    'browserSettings.update.channel == "nightly" && '
                    "version|versionCompare('83.!') >= 0 && localeLanguageCode == "
                    "'en' && 'app.shield.optoutstudies.enabled'|preferenceValue"
                ),
                "userFacingDescription": experiment.public_description,
                "userFacingName": experiment.name,
                "probeSets": [probe_set.slug],
                "featureIds": [experiment.feature_config.slug],
            },
        )
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

    @parameterized.expand(
        [
            [
                NimbusExperiment.Application.FENIX,
                NimbusExperiment.Channel.NIGHTLY,
                "org.mozilla.fenix",
                "org.mozilla.fenix",
                "fenix",
            ],
            [
                NimbusExperiment.Application.FENIX,
                NimbusExperiment.Channel.BETA,
                "org.mozilla.firefox.beta",
                "org.mozilla.firefox.beta",
                "fenix",
            ],
            [
                NimbusExperiment.Application.FENIX,
                NimbusExperiment.Channel.RELEASE,
                "org.mozilla.firefox",
                "org.mozilla.firefox",
                "fenix",
            ],
            [
                NimbusExperiment.Application.FENIX,
                NimbusExperiment.Channel.UNBRANDED,
                "",
                "",
                "fenix",
            ],
            [
                NimbusExperiment.Application.FENIX,
                NimbusExperiment.Channel.NO_CHANNEL,
                "",
                "",
                "fenix",
            ],
            [
                NimbusExperiment.Application.DESKTOP,
                NimbusExperiment.Channel.NIGHTLY,
                "firefox-desktop",
                "firefox-desktop",
                "firefox_desktop",
            ],
            [
                NimbusExperiment.Application.DESKTOP,
                NimbusExperiment.Channel.BETA,
                "firefox-desktop",
                "firefox-desktop",
                "firefox_desktop",
            ],
            [
                NimbusExperiment.Application.DESKTOP,
                NimbusExperiment.Channel.RELEASE,
                "firefox-desktop",
                "firefox-desktop",
                "firefox_desktop",
            ],
            [
                NimbusExperiment.Application.DESKTOP,
                NimbusExperiment.Channel.UNBRANDED,
                "firefox-desktop",
                "firefox-desktop",
                "firefox_desktop",
            ],
            [
                NimbusExperiment.Application.DESKTOP,
                NimbusExperiment.Channel.NO_CHANNEL,
                "firefox-desktop",
                "firefox-desktop",
                "firefox_desktop",
            ],
        ]
    )
    def test_sets_app_id_name_channel_for_application(
        self,
        application,
        channel,
        expected_application,
        expected_appId,
        expected_appName,
    ):
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.ACCEPTED,
            application=application,
            channel=channel,
        )
        serializer = NimbusExperimentSerializer(experiment)
        self.assertEqual(serializer.data["application"], expected_application)
        self.assertEqual(serializer.data["channel"], channel)
        self.assertEqual(serializer.data["appName"], expected_appName)
        self.assertEqual(serializer.data["appId"], expected_appId)
        check_schema("experiments/NimbusExperiment", serializer.data)

    def test_serializer_outputs_expected_schema_without_feature(self):
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.ACCEPTED,
            application=NimbusExperiment.Application.DESKTOP,
            feature_config=None,
        )
        serializer = NimbusExperimentSerializer(experiment)
        experiment_data = serializer.data.copy()
        self.assertEqual(experiment_data["featureIds"], [])
        branches_data = [dict(b) for b in experiment_data.pop("branches")]
        self.assertEqual(len(branches_data), 2)
        for branch in experiment.branches.all():
            self.assertIn(
                {"slug": branch.slug, "ratio": branch.ratio},
                branches_data,
            )

        check_schema("experiments/NimbusExperiment", serializer.data)

    def test_serializer_outputs_targeting(self):
        experiment = NimbusExperimentFactory.create_with_status(
            NimbusExperiment.Status.ACCEPTED,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_83,
            targeting_config_slug=NimbusExperiment.TargetingConfig.ALL_ENGLISH,
            application=NimbusExperiment.Application.DESKTOP,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
        )
        serializer = NimbusExperimentSerializer(experiment)
        self.assertEqual(serializer.data["targeting"], experiment.targeting)


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
