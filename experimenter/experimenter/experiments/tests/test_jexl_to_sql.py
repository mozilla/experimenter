from django.test import TestCase
from parameterized import parameterized

from experimenter.experiments.jexl_to_sql import (
    FENIX_APP,
    IOS_APP,
    KNOWN_UNTRANSLATABLE,
    ensure_bool_sql,
    jexl_to_sql,
)
from experimenter.targeting.constants import (
    FIRST_RUN_WINDOWS_1903_NEWER,
    FX95_DESKTOP_USERS,
    IOS_EXISTING_USERS,
    MOBILE_NEW_USER,
    MOBILE_RECENTLY_UPDATED,
    NO_ENTERPRISE_MAC_WINDOWS_ONLY,
    WIN11_ONLY,
)

_REVIEW_CHECKER_JSON = "CAST(JSON_VALUE(context, '$.isReviewCheckerEnabled') AS BOOL)"

_OS = "metrics.object.nimbus_targeting_context_os"
_BS = "metrics.object.nimbus_targeting_context_browser_settings"
_HP = "metrics.object.nimbus_targeting_context_home_page_settings"
_AI = "metrics.object.nimbus_targeting_context_addons_info"
_AD = "metrics.object.nimbus_targeting_context_attribution_data"
_PREF = "metrics.object.nimbus_targeting_environment_pref_values"
_USER_PREFS = "metrics.object.nimbus_targeting_environment_user_set_prefs"
_UMA = "metrics.object.nimbus_targeting_context_user_monthly_activity"
_FF = "metrics.quantity.nimbus_targeting_context_firefox_version"


class TestJEXLToSQL(TestCase):
    # --- Column mappings: (jexl_expression, expected_sql) ---

    @parameterized.expand(
        [
            ("locale", "locale", "metrics.string.nimbus_targeting_context_locale"),
            ("region", "region", "metrics.string.nimbus_targeting_context_region"),
            (
                "is_first_startup",
                "isFirstStartup",
                "metrics.boolean.nimbus_targeting_context_is_first_startup",
            ),
            (
                "is_default_browser",
                "isDefaultBrowser",
                "metrics.boolean.nimbus_targeting_context_is_default_browser",
            ),
            (
                "is_fx_a_signed_in",
                "isFxASignedIn",
                "metrics.boolean.nimbus_targeting_context_is_fx_a_signed_in",
            ),
            (
                "firefox_version",
                "firefoxVersion",
                "metrics.quantity.nimbus_targeting_context_firefox_version",
            ),
            (
                "memory_mb",
                "memoryMb",
                "metrics.quantity.nimbus_targeting_context_memory_mb",
            ),
            (
                "memory_MB_alias",
                "memoryMB",
                "metrics.quantity.nimbus_targeting_context_memory_mb",
            ),
            (
                "os_is_mac",
                "os.isMac",
                f"CAST(JSON_VALUE({_OS}, '$.isMac') AS BOOL)",
            ),
            (
                "os_is_linux",
                "os.isLinux",
                f"CAST(JSON_VALUE({_OS}, '$.isLinux') AS BOOL)",
            ),
            (
                "homepage_is_default",
                "homePageSettings.isDefault",
                f"CAST(JSON_VALUE({_HP}, '$.isDefault') AS BOOL)",
            ),
            (
                "homepage_is_custom_url",
                "homePageSettings.isCustomUrl",
                f"CAST(JSON_VALUE({_HP}, '$.isCustomUrl') AS BOOL)",
            ),
            (
                "addons_has_installed",
                "addonsInfo.hasInstalledAddons",
                f"CAST(JSON_VALUE({_AI}, '$.hasInstalledAddons') AS BOOL)",
            ),
            (
                "attribution_medium",
                "attributionData.medium",
                f"JSON_VALUE({_AD}, '$.medium')",
            ),
            (
                "browser_channel",
                "browserSettings.update.channel",
                f"JSON_VALUE({_BS}, '$.update.channel')",
            ),
        ]
    )
    def test_attribute_translates_to_column(self, _name, jexl, expected_sql):
        result = jexl_to_sql(jexl)
        self.assertEqual(result.sql, expected_sql)
        self.assertEqual(result.warnings, [])

    # --- Comparisons: (jexl, expected_sql) ---

    @parameterized.expand(
        [
            (
                "locale_eq",
                'locale == "en-US"',
                "metrics.string.nimbus_targeting_context_locale = 'en-US'",
            ),
            (
                "locale_in_array",
                'locale in ["en-US", "en-CA"]',
                "(metrics.string.nimbus_targeting_context_locale IN ('en-US', 'en-CA'))",
            ),
            (
                "firefox_version_gte",
                "firefoxVersion >= 120",
                f"{_FF} >= 120",
            ),
            (
                "bool_true",
                "isFirstStartup == true",
                "metrics.boolean.nimbus_targeting_context_is_first_startup = TRUE",
            ),
            (
                "bool_false",
                "isFirstStartup == false",
                "metrics.boolean.nimbus_targeting_context_is_first_startup = FALSE",
            ),
            (
                "null_check",
                "isFxASignedIn != null",
                "metrics.boolean.nimbus_targeting_context_is_fx_a_signed_in IS NOT NULL",
            ),
            (
                "pref_value_eq_bool_false",
                "'browser.shell.checkDefaultBrowser'|preferenceValue == false",
                f"JSON_VALUE({_PREF}, '$.browser__shell__checkDefaultBrowser') = 'false'",
            ),
            (
                "pref_value_eq_bool_true",
                "'app.normandy.enabled'|preferenceValue == true",
                f"JSON_VALUE({_PREF}, '$.app__normandy__enabled') = 'true'",
            ),
            (
                "pref_value_eq_bool_reversed",
                "false == 'browser.shell.checkDefaultBrowser'|preferenceValue",
                f"'false' = JSON_VALUE({_PREF}, '$.browser__shell__checkDefaultBrowser')",
            ),
            (
                "pref_value_neq_bool_false",
                # null != false is true in JEXL — unset prefs (NULL) must pass
                "'app.shield.optoutstudies.enabled'|preferenceValue != false",
                (
                    f"(JSON_VALUE({_PREF}, '$.app__shield__optoutstudies__enabled')"
                    f" IS NULL OR JSON_VALUE({_PREF},"
                    f" '$.app__shield__optoutstudies__enabled') != 'false')"
                ),
            ),
            (
                "pref_value_neq_bool_true",
                "'some.pref'|preferenceValue != true",
                (
                    f"(JSON_VALUE({_PREF}, '$.some__pref') IS NULL"
                    f" OR JSON_VALUE({_PREF}, '$.some__pref') != 'true')"
                ),
            ),
            (
                "pref_value_neq_bool_reversed",
                "false != 'app.normandy.enabled'|preferenceValue",
                (
                    f"(JSON_VALUE({_PREF}, '$.app__normandy__enabled') IS NULL"
                    f" OR 'false' != JSON_VALUE({_PREF}, '$.app__normandy__enabled'))"
                ),
            ),
        ]
    )
    def test_comparison_produces_correct_sql(self, _name, jexl, expected_sql):
        result = jexl_to_sql(jexl)
        self.assertEqual(result.sql, expected_sql)
        self.assertEqual(result.warnings, [])

    # --- Untranslatable: expressions that produce warnings, no sql ---

    _VC = "|versionCompare"

    @parameterized.expand(
        [
            (
                "known_untranslatable",
                "attachedFxAOAuthClients",
                "attachedFxAOAuthClients",
            ),
            ("mobile_attr", "days_since_install < 7", "days_since_install"),
            ("unknown_attr", "someUnknownAttribute", "someUnknownAttribute"),
            (
                "newtab_addon_version",
                "newtabAddonVersion|versionCompare('145.0') >= 0",
                "newtabAddonVersion",
            ),
            (
                "default_profile_subfield",
                "defaultProfile.profileAgeCreated > 0",
                "defaultProfile.profileAgeCreated",
            ),
        ]
    )
    def test_untranslatable_returns_none_and_warning(self, _name, jexl, expected_warning):
        result = jexl_to_sql(jexl)
        self.assertIsNone(result.sql)
        self.assertIn(expected_warning, result.warnings)

    # --- Transforms that warn ---

    @parameterized.expand(
        [
            ("date_unknown_attr", "someDate|date", "|date"),
            (
                "length_untranslatable_subject",
                "attachedFxAOAuthClients|length >= 1",
                "attachedFxAOAuthClients",
            ),
            ("preference_value_variable", "someVar|preferenceValue", "|preferenceValue"),
            (
                "preference_is_user_set_variable",
                "someVar|preferenceIsUserSet",
                "|preferenceIsUserSet",
            ),
            ("unknown_transform", "locale|someUnknownTransform", "|someUnknownTransform"),
            ("version_compare_non_zero", "version|versionCompare('95.!') >= 1", _VC),
            (
                "version_compare_unparseable",
                "version|versionCompare('invalid') >= 0",
                _VC,
            ),
            ("version_compare_standalone", "version|versionCompare('95.!')", _VC),
            ("version_compare_no_args", "version|versionCompare >= 0", _VC),
            ("version_compare_arithmetic_op", "version|versionCompare('95.!') + 0", _VC),
            ("version_compare_reversed_in", "0 in version|versionCompare('95.!')", _VC),
        ]
    )
    def test_transform_warns(self, _name, jexl, expected_warning):
        result = jexl_to_sql(jexl)
        self.assertIn(expected_warning, result.warnings)

    # --- Edge cases ---

    def test_empty_expression_returns_none(self):
        result = jexl_to_sql("")
        self.assertIsNone(result.sql)
        self.assertEqual(result.warnings, [])

    def test_true_expression_returns_none(self):
        result = jexl_to_sql("true")
        self.assertIsNone(result.sql)
        self.assertEqual(result.warnings, [])

    def test_warnings_are_deduplicated(self):
        result = jexl_to_sql("attachedFxAOAuthClients && attachedFxAOAuthClients")
        self.assertEqual(result.warnings.count("attachedFxAOAuthClients"), 1)

    def test_all_known_untranslatable_produce_warnings(self):
        for attribute in KNOWN_UNTRANSLATABLE:
            result = jexl_to_sql(attribute)
            self.assertIn(attribute, result.warnings, f"Expected warning for {attribute}")

    def test_partial_translation_still_returns_sql(self):
        result = jexl_to_sql("isFirstStartup && attachedFxAOAuthClients")
        self.assertIsNotNone(result.sql)
        self.assertIn("is_first_startup", result.sql)
        self.assertIn("attachedFxAOAuthClients", result.warnings)

    def test_invalid_jexl_returns_parse_error_warning(self):
        result = jexl_to_sql("((( invalid ??? jexl")
        self.assertIsNone(result.sql)
        self.assertIn("__parse_error__", result.warnings)

    def test_conditional_expression_returns_none(self):
        result = jexl_to_sql("isFirstStartup ? true : false")
        self.assertIsNone(result.sql)

    def test_unknown_binary_op_returns_none(self):
        result = jexl_to_sql("locale intersect ['en-US']")
        self.assertIsNone(result.sql)

    def test_array_all_untranslatable_returns_none(self):
        result = jexl_to_sql("locale in [attachedFxAOAuthClients]")
        self.assertIsNone(result.sql)

    def test_string_with_single_quote_escaped(self):
        result = jexl_to_sql('locale == "it-IT"')
        self.assertIn("'it-IT'", result.sql)

    # --- NOT operator ---

    def test_not_boolean_column(self):
        result = jexl_to_sql("!isDefaultBrowser")
        self.assertEqual(
            result.sql,
            "NOT (metrics.boolean.nimbus_targeting_context_is_default_browser)",
        )

    def test_not_string_column_uses_is_null(self):
        result = jexl_to_sql("!distributionId")
        self.assertIn("IS NULL", result.sql)
        self.assertIn("= ''", result.sql)

    def test_not_preference_value_uses_is_null(self):
        result = jexl_to_sql("!('trailhead.firstrun.didSeeAboutWelcome'|preferenceValue)")
        self.assertIn("IS NULL", result.sql)
        self.assertIn("= ''", result.sql)

    def test_not_preference_is_user_set(self):
        result = jexl_to_sql("!('browser.startup.homepage'|preferenceIsUserSet)")
        self.assertIn("NOT", result.sql)
        self.assertIn(_USER_PREFS, result.sql)

    # --- os.isWindows derived ---

    def test_os_is_windows_derived_from_not_mac_not_linux(self):
        result = jexl_to_sql("os.isWindows")
        self.assertIsNotNone(result.sql)
        self.assertIn("isMac", result.sql)
        self.assertIn("isLinux", result.sql)
        self.assertIn("NOT", result.sql)
        self.assertEqual(result.warnings, [])

    # --- Transforms ---

    def test_bool_arithmetic_casts_to_int64(self):
        # JEXL pattern `(bool && 1 || 0) + (bool && 1 || 0)` sums booleans.
        # BigQuery can't add BOOLs — each must be CAST to INT64.
        result = jexl_to_sql("(isDefaultBrowser && 1 || 0) + (isFxASignedIn && 1 || 0)")
        self.assertIsNotNone(result.sql)
        self.assertIn("CAST(", result.sql)
        self.assertIn("AS INT64)", result.sql)

    def test_coerce_to_bool_numeric_truthy(self):
        # JEXL pattern `bool && 1 || 0` uses literal 1/0 as ternary values.
        # _coerce_to_bool("1") must not produce `1 != ''` (INT64 vs STRING).
        result = jexl_to_sql("isDefaultBrowser && 1 || 0")
        self.assertIsNotNone(result.sql)
        self.assertNotIn("1 != ''", result.sql)
        self.assertNotIn("0 != ''", result.sql)

    def test_ensure_bool_sql_passes_through_bool_expression(self):
        sql = "metrics.boolean.nimbus_targeting_context_is_default_browser"
        self.assertEqual(ensure_bool_sql(sql), sql)

    def test_ensure_bool_sql_coerces_json_value_string(self):
        # Bare preferenceValue → STRING; ensure_bool_sql makes it BOOL-safe.
        _pref = "metrics.object.nimbus_targeting_environment_pref_values"
        sql = f"JSON_VALUE({_pref}, '$.pref')"
        result = ensure_bool_sql(sql)
        self.assertIn("IS NOT NULL", result)
        self.assertIn("!= ''", result)
        self.assertIn("!= 'false'", result)

    def test_preference_value_dots_to_underscores(self):
        result = jexl_to_sql("'browser.urlbar.quicksuggest'|preferenceValue")
        self.assertIn(_PREF, result.sql)
        self.assertIn("browser__urlbar__quicksuggest", result.sql)
        self.assertEqual(result.warnings, [])

    def test_preference_value_compared_with_integer_casts_to_float(self):
        # JSON_VALUE returns STRING; comparing with an integer requires SAFE_CAST.
        result = jexl_to_sql("'termsofuse.acceptedVersion'|preferenceValue >= 4")
        self.assertIsNotNone(result.sql)
        self.assertIn("SAFE_CAST(", result.sql)
        self.assertIn("AS FLOAT64)", result.sql)
        self.assertIn(">= 4", result.sql)

    def test_preference_value_multiplied_by_integer_casts_to_float(self):
        # The pattern `pref|preferenceValue * 1` converts a string pref to a number.
        result = jexl_to_sql("'termsofuse.acceptedDate'|preferenceValue * 1")
        self.assertIsNotNone(result.sql)
        self.assertIn("SAFE_CAST(", result.sql)
        self.assertIn("AS FLOAT64)", result.sql)

    def test_integer_compared_with_preference_value_casts_to_float(self):
        # Reversed operand order: numeric literal on the left.
        result = jexl_to_sql("4 <= 'termsofuse.acceptedVersion'|preferenceValue")
        self.assertIsNotNone(result.sql)
        self.assertIn("SAFE_CAST(", result.sql)
        self.assertIn("AS FLOAT64)", result.sql)

    def test_preference_is_user_set(self):
        result = jexl_to_sql("'browser.newtabpage.enabled'|preferenceIsUserSet")
        self.assertIn(_USER_PREFS, result.sql)
        self.assertIn("browser.newtabpage.enabled", result.sql)
        self.assertIn("IN UNNEST", result.sql)
        self.assertEqual(result.warnings, [])

    def test_length_user_monthly_activity(self):
        result = jexl_to_sql("userMonthlyActivity|length >= 1")
        self.assertIn(_UMA, result.sql)
        self.assertIn("ARRAY_LENGTH(JSON_QUERY_ARRAY", result.sql)
        self.assertEqual(result.warnings, [])

    def test_length_on_translatable_subject(self):
        result = jexl_to_sql("locale|length >= 2")
        self.assertIn("ARRAY_LENGTH(JSON_QUERY_ARRAY", result.sql)

    def test_date_profile_age(self):
        result = jexl_to_sql(
            "(currentDate|date - profileAgeCreated|date) / 86400000 >= 28"
        )
        self.assertIn("profile_age_created", result.sql)
        self.assertIn("UNIX_MILLIS", result.sql)
        self.assertEqual(result.warnings, [])

    # --- versionCompare ---

    def test_version_compare_gte(self):
        result = jexl_to_sql("version|versionCompare('120.!') >= 0")
        self.assertEqual(result.sql, f"{_FF} >= 120")
        self.assertEqual(result.warnings, [])

    def test_version_compare_reversed_operands(self):
        result = jexl_to_sql("0 <= version|versionCompare('120.!')")
        self.assertEqual(result.sql, f"{_FF} >= 120")
        self.assertEqual(result.warnings, [])

    # --- addonsInfo ---

    def test_addons_specific_addon_id_installed(self):
        # addon != null means installed → (id IN UNNEST(addons))
        result = jexl_to_sql("addonsInfo.addons['uBlock0@raymondhill.net'] != null")
        self.assertEqual(
            result.sql,
            f"('uBlock0@raymondhill.net' IN UNNEST(JSON_VALUE_ARRAY({_AI}, '$.addons')))",
        )
        self.assertEqual(result.warnings, [])

    def test_addons_specific_addon_id_not_installed(self):
        # addon == null means NOT installed → NOT (id IN UNNEST(addons))
        addon_id = "{20fc2e06-e3e4-4b2b-812b-ab431220cada}"
        result = jexl_to_sql(f"addonsInfo.addons['{addon_id}'] == null")
        self.assertEqual(
            result.sql,
            f"NOT (('{addon_id}' IN UNNEST(JSON_VALUE_ARRAY({_AI}, '$.addons'))))",
        )
        self.assertEqual(result.warnings, [])

    def test_filter_expression_non_addons_warns(self):
        result = jexl_to_sql("enrollments[.slug == 'test']")
        self.assertIsNone(result.sql)
        self.assertTrue(len(result.warnings) > 0)

    def test_filter_expression_with_non_string_literal_warns(self):
        result = jexl_to_sql("addonsInfo.addons[0]")
        self.assertIsNone(result.sql)
        self.assertTrue(len(result.warnings) > 0)

    def test_real_config_first_run_win1903(self):
        _key = "trailhead__firstrun__didSeeAboutWelcome"
        _wbn = f"SAFE_CAST(JSON_VALUE({_OS}, '$.windowsBuildNumber') AS INT64)"
        expected = (
            f"((metrics.boolean.nimbus_targeting_context_is_first_startup"
            f" AND (JSON_VALUE({_PREF}, '$.{_key}') IS NULL"
            f" OR JSON_VALUE({_PREF}, '$.{_key}') = ''))"
            f" AND {_wbn} >= 18362)"
        )
        result = jexl_to_sql(FIRST_RUN_WINDOWS_1903_NEWER.targeting)
        self.assertEqual(result.sql, expected)
        self.assertEqual(result.warnings, [])

    def test_real_config_no_enterprise_mac_windows(self):
        _not_mac = f"NOT CAST(JSON_VALUE({_OS}, '$.isMac') AS BOOL)"
        _not_linux = f"NOT CAST(JSON_VALUE({_OS}, '$.isLinux') AS BOOL)"
        _is_mac = f"CAST(JSON_VALUE({_OS}, '$.isMac') AS BOOL)"
        _no_ent = (
            "NOT (metrics.boolean"
            ".nimbus_targeting_context_has_active_enterprise_policies)"
        )
        expected = f"({_no_ent} AND (({_not_mac} AND {_not_linux}) OR {_is_mac}))"
        result = jexl_to_sql(NO_ENTERPRISE_MAC_WINDOWS_ONLY.targeting)
        self.assertEqual(result.sql, expected)
        self.assertEqual(result.warnings, [])

    def test_real_config_windows_11(self):
        _not_mac = f"NOT CAST(JSON_VALUE({_OS}, '$.isMac') AS BOOL)"
        _not_linux = f"NOT CAST(JSON_VALUE({_OS}, '$.isLinux') AS BOOL)"
        _winver = f"SAFE_CAST(JSON_VALUE({_OS}, '$.windowsVersion') AS FLOAT64)"
        _winbld = f"SAFE_CAST(JSON_VALUE({_OS}, '$.windowsBuildNumber') AS INT64)"
        expected = (
            f"((({_not_mac} AND {_not_linux})"
            f" AND {_winver} >= 10)"
            f" AND {_winbld} >= 22000)"
        )
        result = jexl_to_sql(WIN11_ONLY.targeting)
        self.assertEqual(result.sql, expected)
        self.assertEqual(result.warnings, [])

    def test_real_config_profile_age_28_days(self):
        _age = "metrics.quantity.nimbus_targeting_context_profile_age_created"
        expected = f"((UNIX_MILLIS(CURRENT_TIMESTAMP()) - {_age}) / 86400000) >= 28"
        result = jexl_to_sql(
            "(currentDate|date - profileAgeCreated|date) / 86400000 >= 28"
        )
        self.assertEqual(result.sql, expected)
        self.assertEqual(result.warnings, [])

    def test_real_config_version_range(self):
        expected = f"({_FF} >= 95 AND {_FF} < 96)"
        result = jexl_to_sql(FX95_DESKTOP_USERS.targeting)
        self.assertEqual(result.sql, expected)
        self.assertEqual(result.warnings, [])

    def test_transform_with_complex_subject_warns(self):
        result = jexl_to_sql("(firefoxVersion + 1)|someTransform")
        self.assertIsNone(result.sql)
        self.assertIn("|someTransform", result.warnings)


class TestJEXLToSQLMobile(TestCase):
    # --- Column mappings ---

    _CAST_BOOL = "CAST(isFirstRun AS BOOL)"
    _CAST_DFLT = "CAST(isDefaultBrowser AS BOOL)"
    _CAST_PHONE = "CAST(isPhone AS BOOL)"
    _CAST_RC_IOS = "CAST(isReviewCheckerEnabled AS BOOL)"
    _UTM_SRC = "installReferrerResponseUtmSource"
    _UTM_SRC_SNAKE = "install_referrer_response_utm_source"
    _EQ_DAYS = "eventQuery_daysOpenedInLast28"
    _EQ_JEXL = "eventQueryValues.daysOpenedInLast28"
    _EQ_SNAKE = "event_query_values.days_opened_in_last_28"

    @parameterized.expand(
        [
            # Shared columns — same on Fenix and iOS
            ("locale_fenix", "locale", FENIX_APP, "locale"),
            ("locale_ios", "locale", IOS_APP, "locale"),
            ("region_fenix", "region", FENIX_APP, "region"),
            ("language_fenix", "language", FENIX_APP, "language"),
            ("app_version_fenix", "appVersion", FENIX_APP, "appVersion"),
            ("app_version_snake", "app_version", FENIX_APP, "appVersion"),
            ("is_first_run_fenix", "isFirstRun", FENIX_APP, _CAST_BOOL),
            ("is_first_run_snake", "is_first_run", FENIX_APP, _CAST_BOOL),
            ("is_first_run_ios", "isFirstRun", IOS_APP, _CAST_BOOL),
            ("days_install_fenix", "daysSinceInstall", FENIX_APP, "daysSinceInstall"),
            ("days_install_snake", "days_since_install", FENIX_APP, "daysSinceInstall"),
            ("days_update_fenix", "daysSinceUpdate", FENIX_APP, "daysSinceUpdate"),
            ("event_query_fenix", _EQ_JEXL, FENIX_APP, _EQ_DAYS),
            ("event_query_snake", _EQ_SNAKE, FENIX_APP, _EQ_DAYS),
            # Fenix-specific columns
            ("android_sdk", "androidSdkVersion", FENIX_APP, "androidSdkVersion"),
            ("android_sdk_snake", "android_sdk_version", FENIX_APP, "androidSdkVersion"),
            ("device_manufacturer", "deviceManufacturer", FENIX_APP, "deviceManufacturer"),
            ("device_model", "deviceModel", FENIX_APP, "deviceModel"),
            ("utm_source", _UTM_SRC, FENIX_APP, _UTM_SRC),
            ("utm_source_snake", _UTM_SRC_SNAKE, FENIX_APP, _UTM_SRC),
            # Fenix JSON-only (not a typed column; uses JSON_VALUE)
            ("rc_fenix", "isReviewCheckerEnabled", FENIX_APP, _REVIEW_CHECKER_JSON),
            ("rc_snake_fenix", "is_review_checker_enabled", FENIX_APP, _REVIEW_CHECKER_JSON),
            # iOS-specific columns
            ("default_browser_ios", "isDefaultBrowser", IOS_APP, _CAST_DFLT),
            ("default_browser_snake", "is_default_browser", IOS_APP, _CAST_DFLT),
            ("is_phone_ios", "isPhone", IOS_APP, _CAST_PHONE),
            ("is_phone_snake", "is_phone", IOS_APP, _CAST_PHONE),
            ("rc_ios", "isReviewCheckerEnabled", IOS_APP, _CAST_RC_IOS),
        ]
    )
    def test_attribute_translates_to_column(self, _name, jexl, app, expected_sql):
        result = jexl_to_sql(jexl, app=app)
        self.assertEqual(result.sql, expected_sql)
        self.assertEqual(result.warnings, [])

    # --- Comparisons ---

    @parameterized.expand(
        [
            ("locale_eq_fenix", "locale == 'en-US'", FENIX_APP, "locale = 'en-US'"),
            (
                "region_in_fenix",
                "region in ['US', 'CA']",
                FENIX_APP,
                "(region IN ('US', 'CA'))",
            ),
            ("days_lt_fenix", "days_since_install < 7", FENIX_APP, "daysSinceInstall < 7"),
            (
                "sdk_gte_fenix",
                "android_sdk_version >= 28",
                FENIX_APP,
                "androidSdkVersion >= 28",
            ),
            ("is_phone_eq_ios", "isPhone == true", IOS_APP, "CAST(isPhone AS BOOL) = TRUE"),
        ]
    )
    def test_comparison_translates(self, _name, jexl, app, expected_sql):
        result = jexl_to_sql(jexl, app=app)
        self.assertEqual(result.sql, expected_sql)
        self.assertEqual(result.warnings, [])

    # --- Boolean columns are not string-coerced in && / || ---

    def test_bool_column_not_string_coerced_in_and_fenix(self):
        result = jexl_to_sql("isFirstRun && daysSinceInstall < 7", app=FENIX_APP)
        self.assertEqual(
            result.sql, "(CAST(isFirstRun AS BOOL) AND daysSinceInstall < 7)"
        )
        self.assertEqual(result.warnings, [])

    def test_bool_column_not_string_coerced_in_and_ios(self):
        result = jexl_to_sql("isDefaultBrowser && region == 'US'", app=IOS_APP)
        self.assertEqual(result.sql, "(CAST(isDefaultBrowser AS BOOL) AND region = 'US')")
        self.assertEqual(result.warnings, [])

    # --- Desktop attributes warn on mobile ---

    _PREF_JEXL = "'browser.urlbar.suggest.searches'|preferenceValue"

    @parameterized.expand(
        [
            ("ff_version_fenix", "firefoxVersion >= 120", FENIX_APP, "firefoxVersion"),
            ("fxa_signed_in_ios", "isFxASignedIn", IOS_APP, "isFxASignedIn"),
            ("pref_value_fenix", _PREF_JEXL, FENIX_APP, "|preferenceValue"),
        ]
    )
    def test_desktop_attr_warns_on_mobile(self, _name, jexl, app, expected_warning):
        result = jexl_to_sql(jexl, app=app)
        self.assertIsNone(result.sql)
        self.assertIn(expected_warning, result.warnings)

    # --- No app falls back to Desktop map ---

    def test_no_app_uses_desktop_map(self):
        result = jexl_to_sql("firefoxVersion >= 120")
        self.assertIsNotNone(result.sql)
        self.assertEqual(result.warnings, [])

    def test_addon_ids_in_fenix(self):
        result = jexl_to_sql("'uBlock0@raymondhill.net' in addon_ids", app=FENIX_APP)
        self.assertEqual(
            result.sql,
            "('uBlock0@raymondhill.net' IN UNNEST(JSON_VALUE_ARRAY(addonIds)))",
        )
        self.assertEqual(result.warnings, [])

    def test_addon_ids_not_in_fenix(self):
        result = jexl_to_sql(
            "('uBlock0@raymondhill.net' in addon_ids) == false", app=FENIX_APP
        )
        self.assertEqual(
            result.sql,
            "('uBlock0@raymondhill.net' IN UNNEST(JSON_VALUE_ARRAY(addonIds))) = FALSE",
        )
        self.assertEqual(result.warnings, [])

    def test_real_config_fenix_first_run_region(self):
        result = jexl_to_sql("isFirstRun && region == 'US'", app=FENIX_APP)
        self.assertEqual(result.sql, "(CAST(isFirstRun AS BOOL) AND region = 'US')")
        self.assertEqual(result.warnings, [])

    def test_real_config_ios_default_browser_phone(self):
        result = jexl_to_sql("isDefaultBrowser && isPhone", app=IOS_APP)
        self.assertEqual(
            result.sql,
            "(CAST(isDefaultBrowser AS BOOL) AND CAST(isPhone AS BOOL))",
        )
        self.assertEqual(result.warnings, [])

    def test_preference_is_user_set_warns_on_mobile(self):
        result = jexl_to_sql("'browser.search.region'|preferenceIsUserSet", app=FENIX_APP)
        self.assertIsNone(result.sql)
        self.assertIn("|preferenceIsUserSet", result.warnings)

    def test_version_compare_warns_on_mobile(self):
        result = jexl_to_sql("version|versionCompare('120.!') >= 0", app=FENIX_APP)
        self.assertIsNone(result.sql)
        self.assertIn("|versionCompare", result.warnings)

    # --- Real targeting config strings ---

    def test_real_config_mobile_new_user_fenix(self):
        result = jexl_to_sql(MOBILE_NEW_USER.targeting, app=FENIX_APP)
        self.assertEqual(result.sql, "daysSinceInstall < 7")
        self.assertEqual(result.warnings, [])

    def test_real_config_mobile_recently_updated_fenix(self):
        result = jexl_to_sql(MOBILE_RECENTLY_UPDATED.targeting, app=FENIX_APP)
        self.assertEqual(result.sql, "(daysSinceUpdate < 7 AND daysSinceInstall >= 7)")
        self.assertEqual(result.warnings, [])

    def test_real_config_ios_existing_users(self):
        result = jexl_to_sql(IOS_EXISTING_USERS.targeting, app=IOS_APP)
        self.assertEqual(result.sql, "daysSinceInstall >= 28")
        self.assertEqual(result.warnings, [])
