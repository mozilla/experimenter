from django.test import TestCase
from parameterized import parameterized

from experimenter.experiments.jexl_to_sql import (
    KNOWN_UNTRANSLATABLE,
    jexl_to_sql,
)
from experimenter.targeting.constants import (
    FIRST_RUN_WINDOWS_1903_NEWER,
    FX95_DESKTOP_USERS,
    NO_ENTERPRISE_MAC_WINDOWS_ONLY,
    WIN11_ONLY,
)

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
                "metrics.string.nimbus_targeting_context_locale IN ('en-US', 'en-CA')",
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
                "metrics.boolean.nimbus_targeting_context_is_fx_a_signed_in != NULL",
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

    def test_preference_value_dots_to_underscores(self):
        result = jexl_to_sql("'browser.urlbar.quicksuggest'|preferenceValue")
        self.assertIn(_PREF, result.sql)
        self.assertIn("browser__urlbar__quicksuggest", result.sql)
        self.assertEqual(result.warnings, [])

    def test_preference_is_user_set(self):
        result = jexl_to_sql("'browser.newtabpage.enabled'|preferenceIsUserSet")
        self.assertIn(_USER_PREFS, result.sql)
        self.assertIn("browser.newtabpage.enabled", result.sql)
        self.assertIn("IN UNNEST", result.sql)
        self.assertEqual(result.warnings, [])

    def test_length_user_monthly_activity(self):
        result = jexl_to_sql("userMonthlyActivity|length >= 1")
        self.assertIn(_UMA, result.sql)
        self.assertIn("JSON_ARRAY_LENGTH", result.sql)
        self.assertEqual(result.warnings, [])

    def test_length_on_translatable_subject(self):
        result = jexl_to_sql("locale|length >= 2")
        self.assertIn("JSON_ARRAY_LENGTH", result.sql)

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

    def test_addons_specific_addon_id(self):
        result = jexl_to_sql("addonsInfo.addons['uBlock0@raymondhill.net'] != null")
        self.assertIn(_AI, result.sql)
        self.assertIn("uBlock0@raymondhill.net", result.sql)
        self.assertIn("IN UNNEST", result.sql)
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
