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


def _ctx(key, cast=None):
    """Mirror of jexl_to_sql._ctx — every mobile attribute reads out of `context`."""
    expr = f"JSON_VALUE(context, '$.{key}')"
    return f"CAST({expr} AS {cast})" if cast else expr


_M_LOCALE = _ctx("locale")
_M_LANGUAGE = _ctx("language")
_M_REGION = f"COALESCE({_ctx('region')}, normalized_country_code)"
_M_APP_VERSION = _ctx("app_version")
_M_FIRST_RUN = _ctx("is_first_run", "BOOL")
_M_DAYS_INSTALL = _ctx("days_since_install", "INT64")
_M_DAYS_UPDATE = _ctx("days_since_update", "INT64")
_M_SDK = _ctx("android_sdk_version", "INT64")
_M_DEVICE_MANUF = _ctx("device_manufacturer")
_M_DEVICE_MODEL = _ctx("device_model")
_M_UTM_SOURCE = _ctx("install_referrer_response_utm_source")
_M_EVENT_QUERY = _ctx("event_query_values.days_opened_in_last_28", "INT64")
_M_DEFAULT_BROWSER = _ctx("is_default_browser", "BOOL")
_M_PHONE = _ctx("is_phone", "BOOL")

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
                "allowed_notification_origins",
                "allowedNotificationOrigins",
                "metrics.quantity.nimbus_targeting_context_allowed_notification_origins",
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

    def test_os_is_windows_derived_from_not_mac_not_linux(self):
        result = jexl_to_sql("os.isWindows")
        self.assertIsNotNone(result.sql)
        self.assertIn("isMac", result.sql)
        self.assertIn("isLinux", result.sql)
        self.assertIn("NOT", result.sql)
        self.assertEqual(result.warnings, [])

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

    def test_version_compare_gte(self):
        result = jexl_to_sql("version|versionCompare('120.!') >= 0")
        self.assertEqual(result.sql, f"{_FF} >= 120")
        self.assertEqual(result.warnings, [])

    def test_version_compare_reversed_operands(self):
        result = jexl_to_sql("0 <= version|versionCompare('120.!')")
        self.assertEqual(result.sql, f"{_FF} >= 120")
        self.assertEqual(result.warnings, [])

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
    _CAST_BOOL = _M_FIRST_RUN
    _CAST_DFLT = _M_DEFAULT_BROWSER
    _CAST_PHONE = _M_PHONE
    _UTM_SRC = "installReferrerResponseUtmSource"
    _UTM_SRC_SNAKE = "install_referrer_response_utm_source"
    _EQ_JEXL = "eventQueryValues.daysOpenedInLast28"
    _EQ_SNAKE = "event_query_values.days_opened_in_last_28"

    @parameterized.expand(
        [
            # Shared attributes — same on Fenix and iOS
            ("locale_fenix", "locale", FENIX_APP, _M_LOCALE),
            ("locale_ios", "locale", IOS_APP, _M_LOCALE),
            ("region_fenix", "region", FENIX_APP, _M_REGION),
            ("language_fenix", "language", FENIX_APP, _M_LANGUAGE),
            ("app_version_fenix", "appVersion", FENIX_APP, _M_APP_VERSION),
            ("app_version_snake", "app_version", FENIX_APP, _M_APP_VERSION),
            ("is_first_run_fenix", "isFirstRun", FENIX_APP, _M_FIRST_RUN),
            ("is_first_run_snake", "is_first_run", FENIX_APP, _M_FIRST_RUN),
            ("is_first_run_ios", "isFirstRun", IOS_APP, _M_FIRST_RUN),
            ("days_install_fenix", "daysSinceInstall", FENIX_APP, _M_DAYS_INSTALL),
            ("days_install_snake", "days_since_install", FENIX_APP, _M_DAYS_INSTALL),
            ("days_update_fenix", "daysSinceUpdate", FENIX_APP, _M_DAYS_UPDATE),
            ("event_query_fenix", _EQ_JEXL, FENIX_APP, _M_EVENT_QUERY),
            ("event_query_snake", _EQ_SNAKE, FENIX_APP, _M_EVENT_QUERY),
            # Fenix-specific attributes
            ("android_sdk", "androidSdkVersion", FENIX_APP, _M_SDK),
            ("android_sdk_snake", "android_sdk_version", FENIX_APP, _M_SDK),
            ("device_manufacturer", "deviceManufacturer", FENIX_APP, _M_DEVICE_MANUF),
            ("device_model", "deviceModel", FENIX_APP, _M_DEVICE_MODEL),
            ("utm_source", _UTM_SRC, FENIX_APP, _M_UTM_SOURCE),
            ("utm_source_snake", _UTM_SRC_SNAKE, FENIX_APP, _M_UTM_SOURCE),
            # iOS-specific attributes
            ("default_browser_ios", "isDefaultBrowser", IOS_APP, _M_DEFAULT_BROWSER),
            ("default_browser_snake", "is_default_browser", IOS_APP, _M_DEFAULT_BROWSER),
            ("is_phone_ios", "isPhone", IOS_APP, _M_PHONE),
            ("is_phone_snake", "is_phone", IOS_APP, _M_PHONE),
        ]
    )
    def test_attribute_translates_to_column(self, _name, jexl, app, expected_sql):
        result = jexl_to_sql(jexl, app=app)
        self.assertEqual(result.sql, expected_sql)
        self.assertEqual(result.warnings, [])

    @parameterized.expand(
        [
            (
                "locale_eq_fenix",
                "locale == 'en-US'",
                FENIX_APP,
                _M_LOCALE + " = 'en-US'",
            ),
            (
                "region_in_fenix",
                "region in ['US', 'CA']",
                FENIX_APP,
                f"({_M_REGION} IN ('US', 'CA'))",
            ),
            (
                "days_lt_fenix",
                "days_since_install < 7",
                FENIX_APP,
                _M_DAYS_INSTALL + " < 7",
            ),
            (
                "sdk_gte_fenix",
                "android_sdk_version >= 28",
                FENIX_APP,
                _M_SDK + " >= 28",
            ),
            (
                "is_phone_eq_ios",
                "isPhone == true",
                IOS_APP,
                _M_PHONE + " = TRUE",
            ),
            (
                "is_first_run_eq_string_true_fenix",
                "isFirstRun == 'true'",
                FENIX_APP,
                _M_FIRST_RUN + " = TRUE",
            ),
            (
                "is_first_run_eq_string_true_ios",
                "isFirstRun == 'true'",
                IOS_APP,
                _M_FIRST_RUN + " = TRUE",
            ),
            (
                "is_first_run_eq_string_false_fenix",
                "isFirstRun == 'false'",
                FENIX_APP,
                _M_FIRST_RUN + " = FALSE",
            ),
            (
                "string_true_eq_bool_col_reversed_fenix",
                "'true' == isFirstRun",
                FENIX_APP,
                "TRUE = " + _M_FIRST_RUN,
            ),
        ]
    )
    def test_comparison_translates(self, _name, jexl, app, expected_sql):
        result = jexl_to_sql(jexl, app=app)
        self.assertEqual(result.sql, expected_sql)
        self.assertEqual(result.warnings, [])

    def test_bool_column_not_string_coerced_in_and_fenix(self):
        result = jexl_to_sql("isFirstRun && daysSinceInstall < 7", app=FENIX_APP)
        self.assertEqual(result.sql, f"({_M_FIRST_RUN} AND {_M_DAYS_INSTALL} < 7)")
        self.assertEqual(result.warnings, [])

    def test_bool_column_not_string_coerced_in_and_ios(self):
        result = jexl_to_sql("isDefaultBrowser && region == 'US'", app=IOS_APP)
        self.assertEqual(result.sql, f"({_M_DEFAULT_BROWSER} AND {_M_REGION} = 'US')")
        self.assertEqual(result.warnings, [])

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

    def test_no_app_uses_desktop_map(self):
        result = jexl_to_sql("firefoxVersion >= 120")
        self.assertIsNotNone(result.sql)
        self.assertEqual(result.warnings, [])

    def test_addon_ids_in_fenix(self):
        # addonIds not yet in the Fenix BQ table (EXP-7326) — untranslatable.
        result = jexl_to_sql("'uBlock0@raymondhill.net' in addon_ids", app=FENIX_APP)
        self.assertIsNone(result.sql)
        self.assertIn("addon_ids", result.warnings)

    def test_addon_ids_not_in_fenix(self):
        # addonIds not yet in the Fenix BQ table (EXP-7326) — untranslatable.
        result = jexl_to_sql(
            "('uBlock0@raymondhill.net' in addon_ids) == false", app=FENIX_APP
        )
        self.assertIsNone(result.sql)
        self.assertIn("addon_ids", result.warnings)

    def test_real_config_fenix_first_run_region(self):
        result = jexl_to_sql("isFirstRun && region == 'US'", app=FENIX_APP)
        self.assertEqual(result.sql, f"({_M_FIRST_RUN} AND {_M_REGION} = 'US')")
        self.assertEqual(result.warnings, [])

    def test_real_config_ios_default_browser_phone(self):
        result = jexl_to_sql("isDefaultBrowser && isPhone", app=IOS_APP)
        self.assertEqual(
            result.sql,
            f"({_M_DEFAULT_BROWSER} AND {_M_PHONE})",
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

    def test_android_sdk_version_compare_fenix(self):
        result = jexl_to_sql(
            "android_sdk_version|versionCompare('33') >= 0", app=FENIX_APP
        )
        self.assertEqual(result.sql, _M_SDK + " >= 33")
        self.assertEqual(result.warnings, [])

    def test_android_sdk_version_compare_reversed_fenix(self):
        result = jexl_to_sql(
            "0 <= android_sdk_version|versionCompare('29')", app=FENIX_APP
        )
        self.assertEqual(result.sql, _M_SDK + " >= 29")
        self.assertEqual(result.warnings, [])

    def test_app_version_compare_fenix(self):
        result = jexl_to_sql("app_version|versionCompare('155.!') >= 0", app=FENIX_APP)
        self.assertEqual(
            result.sql,
            f"SAFE_CAST(SPLIT({_M_APP_VERSION}, '.')[SAFE_OFFSET(0)] AS INT64) >= 155",
        )
        self.assertEqual(result.warnings, [])

    def test_app_version_compare_ios(self):
        result = jexl_to_sql("app_version|versionCompare('156.1.0') >= 0", app=IOS_APP)
        self.assertEqual(
            result.sql,
            f"SAFE_CAST(SPLIT({_M_APP_VERSION}, '.')[SAFE_OFFSET(0)] AS INT64) >= 156",
        )
        self.assertEqual(result.warnings, [])

    def test_user_disabled_ai_fenix(self):
        result = jexl_to_sql("user_disabled_ai == false", app=FENIX_APP)
        self.assertEqual(
            result.sql, "CAST(JSON_VALUE(context, '$.user_disabled_ai') AS BOOL) = FALSE"
        )
        self.assertEqual(result.warnings, [])

    def test_user_disabled_ai_ios(self):
        result = jexl_to_sql("user_disabled_ai == false", app=IOS_APP)
        self.assertEqual(
            result.sql, "CAST(JSON_VALUE(context, '$.user_disabled_ai') AS BOOL) = FALSE"
        )
        self.assertEqual(result.warnings, [])

    def test_user_accepted_tou_fenix(self):
        result = jexl_to_sql("user_accepted_tou == true", app=FENIX_APP)
        self.assertEqual(
            result.sql,
            "CAST(JSON_VALUE(context, '$.user_accepted_tou') AS BOOL) = TRUE",
        )
        self.assertEqual(result.warnings, [])

    def test_tou_points_fenix(self):
        result = jexl_to_sql("tou_points == 1", app=FENIX_APP)
        self.assertEqual(
            result.sql, "CAST(JSON_VALUE(context, '$.tou_points') AS INT64) = 1"
        )
        self.assertEqual(result.warnings, [])

    def test_has_accepted_terms_of_use_ios(self):
        result = jexl_to_sql("has_accepted_terms_of_use == false", app=IOS_APP)
        self.assertEqual(
            result.sql,
            "CAST(JSON_VALUE(context, '$.has_accepted_terms_of_use') AS BOOL) = FALSE",
        )
        self.assertEqual(result.warnings, [])

    def test_tou_experience_points_ios(self):
        result = jexl_to_sql("tou_experience_points == 2", app=IOS_APP)
        self.assertEqual(
            result.sql,
            "CAST(JSON_VALUE(context, '$.tou_experience_points') AS INT64) = 2",
        )
        self.assertEqual(result.warnings, [])

    @parameterized.expand(
        [
            ("notifications", "are_notifications_enabled", FENIX_APP),
            ("marketing", "are_marketing_notifications_enabled", FENIX_APP),
            ("shortcuts", "no_shortcuts_or_stories_opt_outs", FENIX_APP),
            ("bottom_toolbar", "is_bottom_toolbar_user", IOS_APP),
            ("tips", "has_enabled_tips_notifications", IOS_APP),
            ("ai_available", "is_apple_intelligence_available", IOS_APP),
            ("ai_cannot_use", "cannot_use_apple_intelligence", IOS_APP),
        ]
    )
    def test_context_only_bool_attribute(self, _name, attr, app):
        result = jexl_to_sql(f"{attr} == true", app=app)
        self.assertEqual(result.sql, _ctx(attr, "BOOL") + " = TRUE")
        self.assertEqual(result.warnings, [])

    def test_review_checker_untranslatable_on_both_platforms(self):
        """The dedicated ping records it on neither platform. Mapping it would
        resolve to NULL and match nothing silently; warning is safer."""
        for app in (FENIX_APP, IOS_APP):
            result = jexl_to_sql("isReviewCheckerEnabled == true", app=app)
            self.assertIsNone(result.sql, app)
            self.assertIn("isReviewCheckerEnabled", result.warnings)

    def test_tou_attributes_stay_untranslatable_on_desktop(self):
        """Mobile-only context keys; Desktop records none of them."""
        for attr in ("user_accepted_tou", "tou_points", "has_accepted_terms_of_use"):
            result = jexl_to_sql(f"{attr} == true")
            self.assertIsNone(result.sql, attr)
            self.assertIn(attr, result.warnings)

    def test_tou_attributes_do_not_cross_platforms(self):
        """Fenix records user_accepted_tou/tou_points; iOS records the
        has_accepted_terms_of_use/tou_experience_points pair. Neither set
        exists on the other platform."""
        for attr, app in (
            ("user_accepted_tou", IOS_APP),
            ("tou_points", IOS_APP),
            ("has_accepted_terms_of_use", FENIX_APP),
            ("tou_experience_points", FENIX_APP),
        ):
            result = jexl_to_sql(f"{attr} == true", app=app)
            self.assertIsNone(result.sql, f"{attr} on {app}")
            self.assertIn(attr, result.warnings)

    def test_real_config_mobile_new_user_fenix(self):
        result = jexl_to_sql(MOBILE_NEW_USER.targeting, app=FENIX_APP)
        self.assertEqual(result.sql, _M_DAYS_INSTALL + " < 7")
        self.assertEqual(result.warnings, [])

    def test_real_config_mobile_recently_updated_fenix(self):
        result = jexl_to_sql(MOBILE_RECENTLY_UPDATED.targeting, app=FENIX_APP)
        self.assertEqual(result.sql, f"({_M_DAYS_UPDATE} < 7 AND {_M_DAYS_INSTALL} >= 7)")
        self.assertEqual(result.warnings, [])

    def test_real_config_ios_existing_users(self):
        result = jexl_to_sql(IOS_EXISTING_USERS.targeting, app=IOS_APP)
        self.assertEqual(result.sql, _M_DAYS_INSTALL + " >= 28")
        self.assertEqual(result.warnings, [])
