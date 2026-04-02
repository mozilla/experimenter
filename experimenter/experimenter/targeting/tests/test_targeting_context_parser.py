from unittest.mock import patch

from django.test import TestCase
from parameterized.parameterized import parameterized

from experimenter.experiments.constants import NimbusConstants
from experimenter.targeting.targeting_context_parser import TargetingContextFields
from experimenter.targeting.tests import mock_targeting_manifests


@mock_targeting_manifests
class TestTargetingContextFields(TestCase):
    def setUp(self):
        super().setUp()
        TargetingContextFields.clear_cache()

    @parameterized.expand(
        [
            (
                NimbusConstants.Application.DESKTOP,
                [
                    "activeExperiments",
                    "activeRollouts",
                    "addonsInfo",
                    "addressesSaved",
                    "archBits",
                    "attributionData",
                    "browserSettings",
                    "buildId",
                    "currentDate",
                    "defaultPDFHandler",
                    "distributionId",
                    "doesAppNeedPin",
                    "enrollmentsMap",
                    "firefoxVersion",
                    "hasActiveEnterprisePolicies",
                    "homePageSettings",
                    "isDefaultHandler",
                    "isDefaultBrowser",
                    "isFirstStartup",
                    "isFxAEnabled",
                    "isFxASignedIn",
                    "isMSIX",
                    "locale",
                    "memoryMB",
                    "os",
                    "primaryResolution",
                    "profileAgeCreated",
                    "region",
                    "totalBookmarksCount",
                    "userMonthlyActivity",
                    "userPrefersReducedMotion",
                    "usesFirefoxSync",
                    "version",
                ],
            ),
            (
                NimbusConstants.Application.FENIX,
                [
                    "is_first_run",
                    "events",
                    "install_referrer_response_utm_source",
                    "install_referrer_response_utm_medium",
                    "install_referrer_response_utm_campaign",
                    "install_referrer_response_utm_term",
                    "install_referrer_response_utm_content",
                    "android_sdk_version",
                    "app_version",
                    "locale",
                    "days_since_install",
                    "days_since_update",
                    "language",
                    "region",
                    "device_manufacturer",
                    "device_model",
                    "user_accepted_tou",
                    "no_shortcuts_or_stories_opt_outs",
                    "addon_ids",
                    "tou_points",
                ],
            ),
            (
                NimbusConstants.Application.IOS,
                [
                    "is_first_run",
                    "isFirstRun",
                    "is_phone",
                    "events",
                    "app_version",
                    "region",
                    "language",
                    "locale",
                    "days_since_install",
                    "days_since_update",
                    "is_default_browser",
                    "is_bottom_toolbar_user",
                    "has_enabled_tips_notifications",
                    "has_accepted_terms_of_use",
                    "is_apple_intelligence_available",
                    "cannot_use_apple_intelligence",
                    "tou_experience_points",
                ],
            ),
        ]
    )
    def test_load_unversioned_targeting_fields(self, app, expected_fields):
        targeting_fields = TargetingContextFields.for_application(app)

        self.assertEqual(len(targeting_fields), len(expected_fields))

        for field in expected_fields:
            self.assertIn(field, targeting_fields)

    def test_load_versioned_targeting_fields(self):
        targeting_fields = TargetingContextFields.for_application(
            NimbusConstants.Application.FENIX, "v100.0.0"
        )
        expected_fields = [
            "is_first_run",
            "events",
            "install_referrer_response_utm_source",
            "install_referrer_response_utm_medium",
            "install_referrer_response_utm_campaign",
            "install_referrer_response_utm_term",
            "install_referrer_response_utm_content",
            "is_review_checker_enabled",
            "android_sdk_version",
            "app_version",
            "locale",
            "days_since_install",
            "days_since_update",
            "language",
            "region",
            "device_manufacturer",
            "device_model",
        ]

        self.assertEqual(len(targeting_fields), len(expected_fields))

        for field in expected_fields:
            self.assertIn(field, targeting_fields)

    def test_attempt_load_targeting_fields_for_unknown_application(self):
        self.assertRaises(
            ValueError, TargetingContextFields.for_application, "unknown_app"
        )

    def test_targeting_fields_cached(self):
        mock_fields = ["field_one", "field_two"]

        with patch.object(
            TargetingContextFields,
            "_load_targeting_fields",
            return_value=mock_fields,
        ) as mock_loader:
            targeting_fields_1 = TargetingContextFields.for_application(
                NimbusConstants.Application.DESKTOP
            )
            targeting_fields_2 = TargetingContextFields.for_application(
                NimbusConstants.Application.DESKTOP
            )

            self.assertIs(targeting_fields_1, targeting_fields_2)
            mock_loader.assert_called_once_with(NimbusConstants.Application.DESKTOP, None)

    def test_clear_cache_specific_application_only(self):
        TargetingContextFields._desktop_targeting_fields = ["desktop"]
        TargetingContextFields._fenix_targeting_fields = ["fenix"]
        TargetingContextFields._ios_targeting_fields = ["ios"]

        TargetingContextFields.clear_cache(NimbusConstants.Application.DESKTOP)

        self.assertIsNone(TargetingContextFields._desktop_targeting_fields)
        self.assertEqual(TargetingContextFields._fenix_targeting_fields, ["fenix"])
        self.assertEqual(TargetingContextFields._ios_targeting_fields, ["ios"])
