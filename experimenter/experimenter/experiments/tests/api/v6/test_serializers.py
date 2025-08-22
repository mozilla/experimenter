import datetime
import json
from typing import Any

from django.conf import settings
from django.test import TestCase
from mozilla_nimbus_schemas.experiments import (
    DesktopAllVersionsNimbusExperiment,
    SdkNimbusExperiment,
)
from parameterized import parameterized

from experimenter.base.tests.factories import LocaleFactory
from experimenter.experiments.api.v6.serializers import NimbusExperimentSerializer
from experimenter.experiments.models import NimbusBranchFeatureValue, NimbusExperiment
from experimenter.experiments.tests.factories import (
    TEST_LOCALIZATIONS,
    NimbusBranchFactory,
    NimbusExperimentFactory,
    NimbusFeatureConfigFactory,
)


class TestNimbusExperimentSerializer(TestCase):
    maxDiff = None

    @classmethod
    def _validate_experiment_schema(
        cls,
        application: NimbusExperiment.Application,
        experiment_data: dict[str, Any],
    ):
        if NimbusExperiment.Application.is_sdk(application):
            schema = SdkNimbusExperiment
        else:
            schema = DesktopAllVersionsNimbusExperiment

        schema.model_validate(experiment_data)

    def test_expected_schema_with_desktop(self):
        locale_en_us = LocaleFactory.create(code="en-US")
        application = NimbusExperiment.Application.DESKTOP
        feature1 = NimbusFeatureConfigFactory.create(application=application)
        feature2 = NimbusFeatureConfigFactory.create(application=application)
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
            application=application,
            firefox_min_version=NimbusExperiment.MIN_REQUIRED_VERSION,
            feature_configs=[feature1, feature2],
            channel=NimbusExperiment.Channel.NIGHTLY,
            channels=[],
            primary_outcomes=["foo", "bar", "baz"],
            secondary_outcomes=["quux", "xyzzy"],
            locales=[locale_en_us],
            _enrollment_end_date=datetime.date(2022, 1, 5),
            is_firefox_labs_opt_in=False,
        )
        serializer = NimbusExperimentSerializer(experiment)
        experiment_data = serializer.data.copy()
        bucket_data = dict(experiment_data.pop("bucketConfig"))
        branches_data = [dict(b) for b in experiment_data.pop("branches")]
        feature_ids_data = experiment_data.pop("featureIds")

        self.assertIsNotNone(experiment.start_date)
        self.assertIsNotNone(experiment.actual_enrollment_end_date)
        self.assertIsNotNone(experiment.end_date)

        min_required_version = NimbusExperiment.MIN_REQUIRED_VERSION
        expected_experiment_data = self._experiment_data_without_branches_and_featureIds(
            experiment, min_required_version
        )
        self.assertDictEqual(experiment_data, expected_experiment_data)

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
                    "feature": {
                        "featureId": "this-is-included-for-desktop-pre-95-support",
                        "enabled": False,
                        "value": {},
                    },
                    "features": [
                        {
                            "featureId": fv.feature_config.slug,
                            "enabled": True,
                            "value": json.loads(fv.value),
                        }
                        for fv in branch.feature_values.all()
                    ],
                    "firefoxLabsTitle": branch.firefox_labs_title,
                },
                branches_data,
            )

        DesktopAllVersionsNimbusExperiment.model_validate(serializer.data)

    def test_expected_schema_with_desktop_with_non_default_fxlabs_fields(self):
        locale_en_us = LocaleFactory.create(code="en-US")
        application = NimbusExperiment.Application.DESKTOP
        feature1 = NimbusFeatureConfigFactory.create(application=application)
        feature2 = NimbusFeatureConfigFactory.create(application=application)
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
            application=application,
            firefox_min_version=NimbusExperiment.MIN_REQUIRED_VERSION,
            feature_configs=[feature1, feature2],
            channel=NimbusExperiment.Channel.NIGHTLY,
            channels=[],
            primary_outcomes=["foo", "bar", "baz"],
            secondary_outcomes=["quux", "xyzzy"],
            segments=["segment1", "segment2"],
            locales=[locale_en_us],
            _enrollment_end_date=datetime.date(2022, 1, 5),
            is_firefox_labs_opt_in=True,
            firefox_labs_title="test-fx-labs-title",
            firefox_labs_description="test-fx-labs-description",
            firefox_labs_description_links=json.dumps(
                {
                    "foo": "https://example.com",
                }
            ),
            firefox_labs_group="group",
            requires_restart=True,
        )
        serializer = NimbusExperimentSerializer(experiment)
        experiment_data = serializer.data.copy()
        min_required_version = NimbusExperiment.MIN_REQUIRED_VERSION

        expected_experiment_data = self._experiment_data_without_branches_and_featureIds(
            experiment, min_required_version
        )
        expected_experiment_data.update(
            {
                "isFirefoxLabsOptIn": True,
                "firefoxLabsTitle": "test-fx-labs-title",
                "firefoxLabsDescription": "test-fx-labs-description",
                "firefoxLabsDescriptionLinks": {
                    "foo": "https://example.com",
                },
                "firefoxLabsGroup": "group",
                "requiresRestart": True,
            }
        )

        # popping these since this test is not asserting on these
        experiment_data.pop("bucketConfig")
        experiment_data.pop("branches")
        experiment_data.pop("featureIds")

        self.assertDictEqual(experiment_data, expected_experiment_data)

    def test_enrollment_end_date_none_while_live_enrolling(self):
        locale_en_us = LocaleFactory.create(code="en-US")
        application = NimbusExperiment.Application.DESKTOP
        feature1 = NimbusFeatureConfigFactory.create(application=application)
        feature2 = NimbusFeatureConfigFactory.create(application=application)
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LIVE_APPROVE_APPROVE,
            application=application,
            firefox_min_version=NimbusExperiment.MIN_REQUIRED_VERSION,
            feature_configs=[feature1, feature2],
            channel=NimbusExperiment.Channel.NIGHTLY,
            primary_outcomes=["foo", "bar", "baz"],
            secondary_outcomes=["quux", "xyzzy"],
            locales=[locale_en_us],
        )
        serializer = NimbusExperimentSerializer(experiment)
        experiment_data = serializer.data.copy()

        self.assertIsNotNone(experiment.start_date)
        self.assertIsNone(experiment.actual_enrollment_end_date)
        self.assertIsNone(experiment.end_date)

        self.assertEqual(
            experiment_data.get("enrollmentEndDate"),
            experiment.actual_enrollment_end_date,
        )

    def test_list_includes_single_and_multi_feature_schemas(self):
        feature1 = NimbusFeatureConfigFactory.create()
        feature2 = NimbusFeatureConfigFactory.create()
        single_feature_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[feature1],
        )
        multi_feature_experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
            feature_configs=[feature1, feature2],
        )

        serializer = NimbusExperimentSerializer(NimbusExperiment.objects.all(), many=True)
        experiments_data = {e["slug"]: e for e in serializer.data.copy()}

        self.assertIn(
            "feature", experiments_data[single_feature_experiment.slug]["branches"][0]
        )
        self.assertIn(
            "features", experiments_data[single_feature_experiment.slug]["branches"][0]
        )
        self.assertIn(
            "feature", experiments_data[multi_feature_experiment.slug]["branches"][0]
        )
        self.assertIn(
            "features", experiments_data[multi_feature_experiment.slug]["branches"][0]
        )

    @parameterized.expand(list(NimbusExperiment.Application))
    def test_serializers_with_missing_feature_value(self, application):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE,
            application=application,
        )
        experiment.delete_branches()
        experiment.reference_branch = NimbusBranchFactory(
            experiment=experiment, feature_values=[]
        )
        experiment.save()
        serializer = NimbusExperimentSerializer(experiment)
        self.assertEqual(serializer.data["branches"][0]["features"], [])
        self._validate_experiment_schema(application, serializer.data)

    def test_serializers_with_empty_feature_value(self):
        application = NimbusExperiment.Application.DESKTOP
        feature_config = NimbusFeatureConfigFactory.create(application=application)
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE,
            application=application,
            feature_configs=[feature_config],
        )
        experiment.delete_branches()
        experiment.reference_branch = NimbusBranchFactory(
            experiment=experiment, feature_values=[]
        )
        experiment.save()
        NimbusBranchFeatureValue.objects.create(
            branch=experiment.reference_branch, feature_config=feature_config, value=""
        )
        serializer = NimbusExperimentSerializer(experiment)
        self.assertEqual(serializer.data["branches"][0]["features"][0]["value"], {})
        DesktopAllVersionsNimbusExperiment.model_validate(serializer.data)

    def test_serializer_with_branch_invalid_feature_value(self):
        application = NimbusExperiment.Application.DESKTOP
        feature_config = NimbusFeatureConfigFactory.create(application=application)
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.CREATED,
            application=application,
            feature_configs=[feature_config],
        )
        feature_value = experiment.reference_branch.feature_values.get()
        feature_value.value = "this is not json"
        feature_value.save()
        serializer = NimbusExperimentSerializer(experiment)
        branch_slug = serializer.data["referenceBranch"]
        branch = next(x for x in serializer.data["branches"] if x["slug"] == branch_slug)
        self.assertEqual(branch["features"][0]["value"], {})

    @parameterized.expand(
        [
            (application, channel, channel_app_id)
            for application in NimbusExperiment.Application
            for (channel, channel_app_id) in NimbusExperiment.APPLICATION_CONFIGS[
                application
            ].channel_app_id.items()
        ]
    )
    def test_sets_app_id_name_channel_for_application(
        self,
        application,
        channel,
        channel_app_id,
    ):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE,
            application=application,
            channel=channel,
        )

        serializer = NimbusExperimentSerializer(experiment)
        self.assertEqual(serializer.data["application"], channel_app_id)
        self.assertEqual(serializer.data["channel"], channel)
        self.assertEqual(
            serializer.data["appName"],
            NimbusExperiment.APPLICATION_CONFIGS[application].app_name,
        )
        self.assertEqual(serializer.data["appId"], channel_app_id)
        self._validate_experiment_schema(application, serializer.data)

    def test_serializer_outputs_targeting(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
            targeting_config_slug=NimbusExperiment.TargetingConfig.FIRST_RUN,
            channel=NimbusExperiment.Channel.NO_CHANNEL,
        )
        serializer = NimbusExperimentSerializer(experiment)
        self.assertEqual(serializer.data["targeting"], experiment.targeting)
        DesktopAllVersionsNimbusExperiment.model_validate(serializer.data)

    def test_serializer_outputs_empty_targeting(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.LAUNCH_APPROVE,
            publish_status=NimbusExperiment.PublishStatus.APPROVED,
            application=NimbusExperiment.Application.FENIX,
            firefox_min_version=NimbusExperiment.Version.FIREFOX_94,
        )

        serializer = NimbusExperimentSerializer(experiment)
        self.assertEqual(serializer.data["targeting"], "true")
        SdkNimbusExperiment.model_validate(serializer.data)

    def test_localized_desktop(self):
        locale_en_us = LocaleFactory.create(code="en-US")
        locale_en_ca = LocaleFactory.create(code="en-CA")
        locale_fr = LocaleFactory.create(code="fr")
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
            channel=NimbusExperiment.Channel.NIGHTLY,
            primary_outcomes=["foo", "bar", "baz"],
            secondary_outcomes=["qux", "quux"],
            is_localized=True,
            localizations=TEST_LOCALIZATIONS,
            locales=[locale_en_us, locale_en_ca, locale_fr],
        )

        serializer = NimbusExperimentSerializer(experiment)

        self.assertIn("localizations", serializer.data)
        self.assertEqual(serializer.data["localizations"], json.loads(TEST_LOCALIZATIONS))
        DesktopAllVersionsNimbusExperiment.model_validate(serializer.data)

    def test_multiple_locales(self):
        locale_en_us = LocaleFactory.create(code="en-US")
        locale_en_ca = LocaleFactory.create(code="en-CA")
        locale_fr = LocaleFactory.create(code="fr")
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
            locales=[locale_en_us, locale_en_ca, locale_fr],
        )

        serializer = NimbusExperimentSerializer(experiment)

        self.assertIn("locales", serializer.data)
        self.assertEqual(set(serializer.data["locales"]), {"en-US", "en-CA", "fr"})

    def test_all_locales(self):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
        )

        serializer = NimbusExperimentSerializer(experiment)

        self.assertIn("locales", serializer.data)
        self.assertIsNone(serializer.data["locales"])

    @parameterized.expand(
        [
            ("invalid json", None),
            (json.dumps({}), {}),
        ]
    )
    def test_localized_localizations_json(self, l10n_json, expected):
        experiment = NimbusExperimentFactory.create_with_lifecycle(
            NimbusExperimentFactory.Lifecycles.ENDING_APPROVE_APPROVE,
            application=NimbusExperiment.Application.DESKTOP,
            is_localized=True,
            localizations=l10n_json,
        )

        serializer = NimbusExperimentSerializer(experiment)

        self.assertIn("localizations", serializer.data)
        if expected is None:
            self.assertIsNone(serializer.data["localizations"])
        else:
            self.assertEqual(serializer.data["localizations"], expected)

    def _experiment_data_without_branches_and_featureIds(
        self, experiment_data, min_required_version
    ) -> dict[str, Any]:
        return {
            "arguments": {},
            "application": "firefox-desktop",
            "appName": "firefox_desktop",
            "appId": "firefox-desktop",
            "channel": "nightly",
            # DRF manually replaces the isoformat suffix so we have to do the same
            "startDate": experiment_data.start_date.isoformat().replace("+00:00", "Z"),
            "enrollmentEndDate": (
                experiment_data.actual_enrollment_end_date.isoformat().replace(
                    "+00:00", "Z"
                )
            ),
            "endDate": experiment_data.end_date.isoformat().replace("+00:00", "Z"),
            "id": experiment_data.slug,
            "isEnrollmentPaused": True,
            "isRollout": False,
            "proposedDuration": experiment_data.proposed_duration,
            "proposedEnrollment": experiment_data.proposed_enrollment,
            "referenceBranch": experiment_data.reference_branch.slug,
            "schemaVersion": settings.NIMBUS_SCHEMA_VERSION,
            "slug": experiment_data.slug,
            "targeting": (
                f'(browserSettings.update.channel == "nightly") '
                f"&& (version|versionCompare('{min_required_version}') >= 0) "
                f"&& (locale in ['en-US'])"
            ),
            "userFacingDescription": experiment_data.public_description,
            "userFacingName": experiment_data.name,
            "probeSets": [],
            "outcomes": [
                {"priority": "primary", "slug": "foo"},
                {"priority": "primary", "slug": "bar"},
                {"priority": "primary", "slug": "baz"},
                {"priority": "secondary", "slug": "quux"},
                {"priority": "secondary", "slug": "xyzzy"},
            ],
            "featureValidationOptOut": experiment_data.is_client_schema_disabled,
            "localizations": None,
            "locales": ["en-US"],
            "publishedDate": experiment_data.published_date,
            "isFirefoxLabsOptIn": False,
            "firefoxLabsTitle": None,
            "firefoxLabsDescription": None,
            "firefoxLabsDescriptionLinks": None,
            "firefoxLabsGroup": None,
            "requiresRestart": False,
        }
