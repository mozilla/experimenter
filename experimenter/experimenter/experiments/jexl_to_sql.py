import dataclasses
import re
from typing import Optional

from pyjexl.parser import (
    ArrayLiteral,
    BinaryExpression,
    FilterExpression,
    Identifier,
    Literal,
    Transform,
    UnaryExpression,
)

from experimenter.experiments.jexl_utils import JEXLParser

_OS = "metrics.object.nimbus_targeting_context_os"
_BS = "metrics.object.nimbus_targeting_context_browser_settings"
_HP = "metrics.object.nimbus_targeting_context_home_page_settings"
_AD = "metrics.object.nimbus_targeting_context_attribution_data"
_AI = "metrics.object.nimbus_targeting_context_addons_info"

# Schema confirmed from: mozdata.firefox_desktop.nimbus_targeting_context
JEXL_TO_BQ_COLUMN = {
    "locale": "metrics.string.nimbus_targeting_context_locale",
    "region": "metrics.string.nimbus_targeting_context_region",
    "distributionId": "metrics.string.nimbus_targeting_context_distribution_id",
    "currentDate": "metrics.string.nimbus_targeting_context_current_date",
    "version": "metrics.string.nimbus_targeting_context_version",
    "firefoxVersion": "metrics.quantity.nimbus_targeting_context_firefox_version",
    "buildId": "metrics.quantity.nimbus_targeting_context_build_id",
    "archBits": "metrics.quantity.nimbus_targeting_context_arch_bits",
    "memoryMb": "metrics.quantity.nimbus_targeting_context_memory_mb",
    "memoryMB": "metrics.quantity.nimbus_targeting_context_memory_mb",
    "totalBookmarksCount": (
        "metrics.quantity.nimbus_targeting_context_total_bookmarks_count"
    ),
    "addressesSaved": "metrics.quantity.nimbus_targeting_context_addresses_saved",
    "profileGroupProfileCount": (
        "metrics.quantity.nimbus_targeting_context_profile_group_profile_count"
    ),
    "profileAgeCreated": (
        "metrics.quantity.nimbus_targeting_context_profile_age_created"
    ),
    "isFirstStartup": "metrics.boolean.nimbus_targeting_context_is_first_startup",
    "isDefaultBrowser": ("metrics.boolean.nimbus_targeting_context_is_default_browser"),
    "isFxAEnabled": "metrics.boolean.nimbus_targeting_context_is_fx_a_enabled",
    "isFxASignedIn": "metrics.boolean.nimbus_targeting_context_is_fx_a_signed_in",
    "isMSIX": "metrics.boolean.nimbus_targeting_context_is_msix",
    "doesAppNeedPin": "metrics.boolean.nimbus_targeting_context_does_app_need_pin",
    "hasActiveEnterprisePolicies": (
        "metrics.boolean.nimbus_targeting_context_has_active_enterprise_policies"
    ),
    "hasPinnedTabs": "metrics.boolean.nimbus_targeting_context_has_pinned_tabs",
    "userPrefersReducedMotion": (
        "metrics.boolean.nimbus_targeting_context_user_prefers_reduced_motion"
    ),
    "usesFirefoxSync": "metrics.boolean.nimbus_targeting_context_uses_firefox_sync",
    "launchOnLoginAllowedByPolicy": (
        "metrics.boolean.nimbus_targeting_context_launch_on_login_allowed_by_policy"
    ),
    "launchOnLoginEnabled": (
        "metrics.boolean.nimbus_targeting_context_launch_on_login_enabled"
    ),
    "userMonthlyActivity": (
        "metrics.object.nimbus_targeting_context_user_monthly_activity"
    ),
    # isWindows is not stored — derived from absence of isMac and isLinux
    "os.isWindows": (
        f"(NOT CAST(JSON_VALUE({_OS}, '$.isMac') AS BOOL)"
        f" AND NOT CAST(JSON_VALUE({_OS}, '$.isLinux') AS BOOL))"
    ),
    "os.isMac": f"CAST(JSON_VALUE({_OS}, '$.isMac') AS BOOL)",
    "os.isLinux": f"CAST(JSON_VALUE({_OS}, '$.isLinux') AS BOOL)",
    "os.windowsBuildNumber": (
        f"SAFE_CAST(JSON_VALUE({_OS}, '$.windowsBuildNumber') AS INT64)"
    ),
    "os.windowsVersion": (f"SAFE_CAST(JSON_VALUE({_OS}, '$.windowsVersion') AS FLOAT64)"),
    "browserSettings.update.channel": (f"JSON_VALUE({_BS}, '$.update.channel')"),
    "browserSettings.update.autoDownload": (
        f"CAST(JSON_VALUE({_BS}, '$.update.autoDownload') AS BOOL)"
    ),
    "browserSettings.update.enabled": (
        f"CAST(JSON_VALUE({_BS}, '$.update.enabled') AS BOOL)"
    ),
    "homePageSettings.isDefault": (f"CAST(JSON_VALUE({_HP}, '$.isDefault') AS BOOL)"),
    "homePageSettings.isCustomUrl": (f"CAST(JSON_VALUE({_HP}, '$.isCustomUrl') AS BOOL)"),
    "homePageSettings.isLocked": f"CAST(JSON_VALUE({_HP}, '$.isLocked') AS BOOL)",
    "homePageSettings.isWebExt": f"CAST(JSON_VALUE({_HP}, '$.isWebExt') AS BOOL)",
    "addonsInfo.hasInstalledAddons": (
        f"CAST(JSON_VALUE({_AI}, '$.hasInstalledAddons') AS BOOL)"
    ),
    "primaryResolution.width": (
        "SAFE_CAST(JSON_VALUE("
        "metrics.object.nimbus_targeting_context_primary_resolution"
        ", '$.width') AS INT64)"
    ),
    "primaryResolution.height": (
        "SAFE_CAST(JSON_VALUE("
        "metrics.object.nimbus_targeting_context_primary_resolution"
        ", '$.height') AS INT64)"
    ),
    "attributionData.medium": f"JSON_VALUE({_AD}, '$.medium')",
    "attributionData.source": f"JSON_VALUE({_AD}, '$.source')",
    "attributionData.campaign": f"JSON_VALUE({_AD}, '$.campaign')",
    "attributionData.content": f"JSON_VALUE({_AD}, '$.content')",
    "attributionData.ua": f"JSON_VALUE({_AD}, '$.ua')",
    "attributionData.dltoken": f"JSON_VALUE({_AD}, '$.dltoken')",
}

_PREF_VALUES_COL = "metrics.object.nimbus_targeting_environment_pref_values"
_USER_SET_PREFS_COL = "metrics.object.nimbus_targeting_environment_user_set_prefs"
_USER_MONTHLY_ACTIVITY_COL = (
    "metrics.object.nimbus_targeting_context_user_monthly_activity"
)

# App identifiers used to select the right mobile column map in jexl_to_sql().
FENIX_APP = "fenix"
IOS_APP = "ios"

# Mobile BQ tables store all context as a JSON blob column. BOOL columns are wrapped in
# CAST(col AS BOOL) so that _is_boolean_sql() detects them correctly and _coerce_to_bool()
# does not try to compare a BOOL column against '' or 'false'.
# Schema confirmed from live BQ queries against both tables.

# Columns present as typed top-level fields in BOTH Fenix and iOS tables.
_SHARED_MOBILE_COLUMNS = {
    "locale": "locale",
    "region": "region",
    "language": "language",
    "appVersion": "appVersion",
    "app_version": "appVersion",
    "isFirstRun": "CAST(isFirstRun AS BOOL)",
    "is_first_run": "CAST(isFirstRun AS BOOL)",
    "daysSinceInstall": "daysSinceInstall",
    "days_since_install": "daysSinceInstall",
    "daysSinceUpdate": "daysSinceUpdate",
    "days_since_update": "daysSinceUpdate",
    "eventQueryValues.daysOpenedInLast28": "eventQuery_daysOpenedInLast28",
    "event_query_values.days_opened_in_last_28": "eventQuery_daysOpenedInLast28",
    "userDisabledAi": "CAST(userDisabledAi AS BOOL)",
    "user_disabled_ai": "CAST(userDisabledAi AS BOOL)",
}

# Fenix (Android) — moz-fx-data-shared-prod.fenix.nimbus_recorded_targeting_context
JEXL_TO_BQ_COLUMN_FENIX = {
    **_SHARED_MOBILE_COLUMNS,
    # Fenix-specific typed columns
    "androidSdkVersion": "androidSdkVersion",
    "android_sdk_version": "androidSdkVersion",
    "deviceManufacturer": "deviceManufacturer",
    "device_manufacturer": "deviceManufacturer",
    "deviceModel": "deviceModel",
    "device_model": "deviceModel",
    "installReferrerResponseUtmSource": "installReferrerResponseUtmSource",
    "install_referrer_response_utm_source": "installReferrerResponseUtmSource",
    "installReferrerResponseUtmCampaign": "installReferrerResponseUtmCampaign",
    "install_referrer_response_utm_campaign": "installReferrerResponseUtmCampaign",
    "installReferrerResponseUtmMedium": "installReferrerResponseUtmMedium",
    "install_referrer_response_utm_medium": "installReferrerResponseUtmMedium",
    "installReferrerResponseUtmContent": "installReferrerResponseUtmContent",
    "install_referrer_response_utm_content": "installReferrerResponseUtmContent",
    "installReferrerResponseUtmTerm": "installReferrerResponseUtmTerm",
    "install_referrer_response_utm_term": "installReferrerResponseUtmTerm",
    "addonIds": "UNNEST(JSON_VALUE_ARRAY(addonIds))",
    "addon_ids": "UNNEST(JSON_VALUE_ARRAY(addonIds))",
    "userAcceptedTou": "CAST(userAcceptedTou AS BOOL)",
    "user_accepted_tou": "CAST(userAcceptedTou AS BOOL)",
    "noShortcutsOrStoriesOptOuts": "CAST(noShortcutsOrStoriesOptOuts AS BOOL)",
    "no_shortcuts_or_stories_opt_outs": "CAST(noShortcutsOrStoriesOptOuts AS BOOL)",
    "touPoints": "touPoints",
    "tou_points": "touPoints",
    "areNotificationsEnabled": "CAST(areNotificationsEnabled AS BOOL)",
    "are_notifications_enabled": "CAST(areNotificationsEnabled AS BOOL)",
    "areMarketingNotificationsEnabled": "CAST(areMarketingNotificationsEnabled AS BOOL)",
    "are_marketing_notifications_enabled": (
        "CAST(areMarketingNotificationsEnabled AS BOOL)"
    ),
    # JSON-only: in context blob but not a typed column on Fenix (iOS has it).
    # Context keys are camelCase — confirmed from live data.
    "isReviewCheckerEnabled": (
        "CAST(JSON_VALUE(context, '$.isReviewCheckerEnabled') AS BOOL)"
    ),
    "is_review_checker_enabled": (
        "CAST(JSON_VALUE(context, '$.isReviewCheckerEnabled') AS BOOL)"
    ),
}

# iOS (Firefox for iOS)
# moz-fx-data-shared-prod.org_mozilla_ios_firefox.nimbus_recorded_targeting_context
JEXL_TO_BQ_COLUMN_IOS = {
    **_SHARED_MOBILE_COLUMNS,
    # iOS-specific typed columns
    "isDefaultBrowser": "CAST(isDefaultBrowser AS BOOL)",
    "is_default_browser": "CAST(isDefaultBrowser AS BOOL)",
    "isPhone": "CAST(isPhone AS BOOL)",
    "is_phone": "CAST(isPhone AS BOOL)",
    "isReviewCheckerEnabled": "CAST(isReviewCheckerEnabled AS BOOL)",
    "is_review_checker_enabled": "CAST(isReviewCheckerEnabled AS BOOL)",
    "isBottomToolbarUser": "CAST(isBottomToolbarUser AS BOOL)",
    "is_bottom_toolbar_user": "CAST(isBottomToolbarUser AS BOOL)",
    "hasEnabledTipsNotifications": "CAST(hasEnabledTipsNotifications AS BOOL)",
    "has_enabled_tips_notifications": "CAST(hasEnabledTipsNotifications AS BOOL)",
    "hasAcceptedTermsOfUse": "CAST(hasAcceptedTermsOfUse AS BOOL)",
    "has_accepted_terms_of_use": "CAST(hasAcceptedTermsOfUse AS BOOL)",
    "isAppleIntelligenceAvailable": "CAST(isAppleIntelligenceAvailable AS BOOL)",
    "is_apple_intelligence_available": "CAST(isAppleIntelligenceAvailable AS BOOL)",
    "cannotUseAppleIntelligence": "CAST(cannotUseAppleIntelligence AS BOOL)",
    "cannot_use_apple_intelligence": "CAST(cannotUseAppleIntelligence AS BOOL)",
    "touExperiencePoints": "touExperiencePoints",
    "tou_experience_points": "touExperiencePoints",
}

# Attributes with no corresponding column in nimbus_targeting_context.
KNOWN_UNTRANSLATABLE = {
    "attachedFxAOAuthClients",  # privacy-sensitive, will never be recorded
    "isFirstRun",  # Desktop uses isFirstStartup; also mobile-only
    "is_first_run",
    "isNonStubFirstRun",
    "enrollments",
    "enrollmentsMap",
    "activeExperiments",  # circular
    "activeRollouts",  # circular
    "newtabSettings",
    "searchEngines",
    "addonsInfo",  # parent blocked; specific sub-fields mapped above
    "isBackgroundTaskMode",
    "newtabAddonVersion",  # addon version not stored in nimbus_targeting_context
    "defaultProfile",  # background task context only
    "defaultPDFHandler",  # default PDF handler, not directly queryable
    "isDefaultHandler",  # file-type handler object, not directly queryable
    "localeLanguageCode",  # derived from locale, not recorded separately
    "homePageSettings",  # parent blocked; simple sub-fields mapped above
    # Mobile-only attributes — untranslatable on Desktop.
    # Those in JEXL_TO_BQ_COLUMN_FENIX / JEXL_TO_BQ_COLUMN_IOS are handled
    # by the mobile column maps when app="fenix" or app="ios".
    # Those absent from the mobile maps are not recorded in the BQ context blob.
    "days_since_install",
    "days_since_update",
    "is_default_browser",
    "is_phone",
    "is_bottom_toolbar_user",
    "is_apple_intelligence_available",
    "cannot_use_apple_intelligence",
    "has_accepted_terms_of_use",
    "has_enabled_tips_notifications",
    "user_accepted_tou",
    "tou_points",
    "tou_experience_points",
    "addon_ids",
    "no_shortcuts_or_stories_opt_outs",
    "android_sdk_version",
    "install_referrer_response_utm_source",
    # Standalone sub-fields accessed without parent (default PDF handler context)
    "pdf",
    "knownBrowser",
    "registered",
}

# Maps Experimenter application app_name to the jexl_to_sql app parameter.
# "firefox_desktop" and all other app names map to None (desktop column map).
APP_NAME_TO_JEXL_APP: dict[str, str] = {
    "fenix": FENIX_APP,
    "firefox_ios": IOS_APP,
}

# Maps jexl_to_sql app parameter to the corresponding column map.
_APP_COLUMN_MAP: dict[str, dict] = {
    FENIX_APP: JEXL_TO_BQ_COLUMN_FENIX,
    IOS_APP: JEXL_TO_BQ_COLUMN_IOS,
}

_VERSION_PATTERN = re.compile(r"^(\d+)")


@dataclasses.dataclass
class JEXLToSQLResult:
    sql: Optional[str]
    warnings: list[str]


def jexl_to_sql(jexl_expression: str, app: Optional[str] = None) -> JEXLToSQLResult:
    """
    Translate a JEXL targeting expression into a BigQuery SQL WHERE clause.

    Pass app="fenix" or app="ios" to use the mobile column mappings.
    Returns sql=None with a warnings list when nothing can be translated.
    Returns partial sql with warnings when only some clauses translate.
    """
    column_map = _APP_COLUMN_MAP.get(app, JEXL_TO_BQ_COLUMN)

    if not jexl_expression or jexl_expression == "true":
        return JEXLToSQLResult(sql=None, warnings=[])

    warnings: list[str] = []
    try:
        ast = JEXLParser().parse(jexl_expression)
        sql = _node_to_sql(ast, warnings, column_map)
    except Exception:
        return JEXLToSQLResult(sql=None, warnings=["__parse_error__"])

    return JEXLToSQLResult(sql=sql or None, warnings=warnings)


def _node_to_sql(node, warnings: list[str], column_map: dict[str, str]) -> Optional[str]:
    if isinstance(node, BinaryExpression):
        return _binary_to_sql(node, warnings, column_map)
    if isinstance(node, UnaryExpression):
        return _unary_to_sql(node, warnings, column_map)
    if isinstance(node, Identifier):
        return _identifier_to_sql(node, warnings, column_map)
    if isinstance(node, Literal):
        return _literal_to_sql(node)
    if isinstance(node, ArrayLiteral):
        return _array_to_sql(node, warnings, column_map)
    if isinstance(node, Transform):
        return _transform_to_sql(node, warnings, column_map)
    if isinstance(node, FilterExpression):
        subject_path = _identifier_path(node.subject)
        # addonsInfo.addons['addon-id'] — check addon ID membership in BQ array
        if subject_path == "addonsInfo.addons" and isinstance(node.expression, Literal):
            addon_id = node.expression.value
            if isinstance(addon_id, str):
                # Wrap in parens so result can be used in comparisons: (...) != NULL
                return f"('{addon_id}' IN UNNEST(JSON_VALUE_ARRAY({_AI}, '$.addons')))"
        _add_warning(warnings, subject_path or _identifier_path(node.subject))
        return None
    return None


def _binary_to_sql(
    node: BinaryExpression, warnings: list[str], column_map: dict[str, str]
) -> Optional[str]:
    op = node.operator.symbol

    if _is_version_compare_node(node.left) and isinstance(node.right, Literal):
        return _version_compare_binary_to_sql(node, warnings, column_map)
    if _is_version_compare_node(node.right) and isinstance(node.left, Literal):
        return _version_compare_binary_to_sql_reversed(node, warnings, column_map)

    if op in ("&&", "||"):
        left = _node_to_sql(node.left, warnings, column_map)
        right = _node_to_sql(node.right, warnings, column_map)
        if left and right:
            sql_op = "AND" if op == "&&" else "OR"
            # BigQuery requires BOOL operands for AND/OR.
            # Pref value strings and JSON_VALUE results are STRING — coerce to BOOL.
            left = _coerce_to_bool(left)
            right = _coerce_to_bool(right)
            return f"({left} {sql_op} {right})"
        return left or right

    left = _node_to_sql(node.left, warnings, column_map)
    right = _node_to_sql(node.right, warnings, column_map)
    if left is None or right is None:
        return None

    if op == "in":
        # Wrap in parens so the result can be safely used in outer comparisons
        # e.g. (region IN ('US', 'CA')) != TRUE — without parens BQ errors
        return f"({left} IN {right})"

    comparison_ops = {
        "==": "=",
        "!=": "!=",
        "<": "<",
        "<=": "<=",
        ">": ">",
        ">=": ">=",
    }
    arithmetic_ops = {"+": "+", "-": "-", "*": "*", "/": "/", "%": "%"}

    # JSON_VALUE (from preferenceValue) returns STRING. When used in numeric
    # comparisons or arithmetic, cast to FLOAT64 so BigQuery accepts it.
    # e.g. 'pref'|preferenceValue >= 4  →  SAFE_CAST(JSON_VALUE(...) AS FLOAT64) >= 4
    # e.g. 'pref'|preferenceValue * 1   →  SAFE_CAST(JSON_VALUE(...) AS FLOAT64) * 1
    def _is_numeric_literal(sql):
        try:
            float(sql)
            return True
        except (ValueError, TypeError):
            return False

    if _is_json_string_expr(left) and _is_numeric_literal(right):
        left = f"SAFE_CAST({left} AS FLOAT64)"
    elif _is_json_string_expr(right) and _is_numeric_literal(left):
        right = f"SAFE_CAST({right} AS FLOAT64)"

    if op in comparison_ops:
        sql_op = comparison_ops[op]
        # JEXL uses == null / != null; BigQuery requires IS NULL / IS NOT NULL.
        # FilterExpression results (IN UNNEST) represent "found/not found":
        #   filter == null  →  NOT (filter)   [addon/pref not present]
        #   filter != null  →  filter          [addon/pref present]
        # For all other expressions use IS NULL / IS NOT NULL.
        if right == "NULL" or left == "NULL":
            expr = left if right == "NULL" else right
            is_filter_result = " IN UNNEST(" in expr.upper()
            if sql_op == "=":
                return f"NOT ({expr})" if is_filter_result else f"{expr} IS NULL"
            if sql_op == "!=":
                return expr if is_filter_result else f"{expr} IS NOT NULL"
        # JSON_VALUE returns STRING; comparing to a BOOL literal is invalid.
        # 'pref'|preferenceValue == false → JSON_VALUE(...) = 'false'.
        if right in ("TRUE", "FALSE") and _is_json_string_expr(left):
            right = f"'{right.lower()}'"
        elif left in ("TRUE", "FALSE") and _is_json_string_expr(right):
            left = f"'{left.lower()}'"
        # In JEXL, pref|preferenceValue returns null when the pref is not explicitly set.
        # null != 'false' is true in JEXL — unset prefs should pass a != false check.
        # JSON_VALUE returns NULL for unset prefs; NULL != 'false' is NULL in SQL (falsy),
        # which would incorrectly exclude users on the browser default.
        # Fix: (col IS NULL OR col != 'false') matches JEXL semantics.
        _bool_strs = ("'false'", "'true'")
        if sql_op == "!=" and right in _bool_strs and _is_json_string_expr(left):
            return f"({left} IS NULL OR {left} != {right})"
        if sql_op == "!=" and left in _bool_strs and _is_json_string_expr(right):
            return f"({right} IS NULL OR {left} != {right})"
        return f"{left} {sql_op} {right}"
    if op in arithmetic_ops:
        # BigQuery has no BOOL arithmetic — cast BOOL operands to INT64.
        # Avoid double-casting if already CAST(...AS INT64).
        if _is_boolean_sql(left) and not left.upper().endswith("AS INT64)"):
            left = f"CAST({left} AS INT64)"
        if _is_boolean_sql(right) and not right.upper().endswith("AS INT64)"):
            right = f"CAST({right} AS INT64)"
        return f"({left} {arithmetic_ops[op]} {right})"
    return None


def _unary_to_sql(
    node: UnaryExpression, warnings: list[str], column_map: dict[str, str]
) -> Optional[str]:
    if node.operator.symbol == "!":
        inner = _node_to_sql(node.right, warnings, column_map)
        if inner:
            if _is_boolean_sql(inner):
                return f"NOT ({inner})"
            # NOT (string) is invalid in BigQuery — JEXL falsy means null or empty
            return f"({inner} IS NULL OR {inner} = '')"
    return None  # pragma: no cover — pyjexl only produces UnaryExpression for "!"


def _identifier_to_sql(
    node: Identifier, warnings: list[str], column_map: dict[str, str]
) -> Optional[str]:
    path = _identifier_path(node)

    if path == "null":
        return "NULL"

    # column_map takes priority — covers both direct columns and JSON_VALUE expressions.
    # KNOWN_UNTRANSLATABLE is a secondary hint for Desktop paths we know will never map.
    if path in column_map:
        return column_map[path]

    if _is_untranslatable(path):
        _add_warning(warnings, path)
        return None

    _add_warning(warnings, path)
    return None


def _literal_to_sql(node: Literal) -> str:
    value = node.value
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, str):
        escaped = value.replace("'", "\\'")
        return f"'{escaped}'"
    return str(value)


def _array_to_sql(
    node: ArrayLiteral, warnings: list[str], column_map: dict[str, str]
) -> Optional[str]:
    items = [_node_to_sql(item, warnings, column_map) for item in node.value]
    items = [i for i in items if i is not None]
    if not items:
        return None
    return f"({', '.join(items)})"


def _transform_to_sql(
    node: Transform, warnings: list[str], column_map: dict[str, str]
) -> Optional[str]:
    subject_path = _identifier_path(node.subject)

    # If the subject itself is untranslatable, warn about it rather than the transform
    if (
        subject_path
        and subject_path not in column_map
        and _is_untranslatable(subject_path)
    ):
        _add_warning(warnings, subject_path)
        return None

    if node.name == "date":
        # profileAgeCreated is epoch ms — return column directly for arithmetic
        if subject_path == "profileAgeCreated" and "profileAgeCreated" in column_map:
            return column_map["profileAgeCreated"]
        if subject_path == "currentDate":
            return "UNIX_MILLIS(CURRENT_TIMESTAMP())"
        _add_warning(warnings, "|date")
        return None

    if node.name == "length":
        # BigQuery has no JSON_ARRAY_LENGTH for STRING columns — metrics.object.*
        # columns are JSON strings, so use ARRAY_LENGTH(JSON_QUERY_ARRAY(...)).
        subject_sql = _node_to_sql(node.subject, warnings, column_map)
        if subject_sql:
            return f"ARRAY_LENGTH(JSON_QUERY_ARRAY({subject_sql}))"
        _add_warning(warnings, "|length")
        return None

    if node.name == "preferenceValue":
        # Desktop-only: pref data lives in a Glean metrics column that does not exist
        # in mobile BQ tables. Warn and bail when running against a mobile column map.
        if column_map is not JEXL_TO_BQ_COLUMN:
            _add_warning(warnings, "|preferenceValue")
            return None
        # Pref names stored with dots replaced by __ in BigQuery.
        pref_name = _literal_value(node.subject)
        if pref_name:
            bq_key = pref_name.replace(".", "__")
            return f"JSON_VALUE({_PREF_VALUES_COL}, '$.{bq_key}')"
        _add_warning(warnings, "|preferenceValue")
        return None

    if node.name == "preferenceIsUserSet":
        # Desktop-only: same reasoning as preferenceValue above.
        if column_map is not JEXL_TO_BQ_COLUMN:
            _add_warning(warnings, "|preferenceIsUserSet")
            return None
        # user_set_prefs is a JSON array of pref names (using original dot notation)
        pref_name = _literal_value(node.subject)
        if pref_name:
            return f"'{pref_name}' IN UNNEST(JSON_VALUE_ARRAY({_USER_SET_PREFS_COL}))"
        _add_warning(warnings, "|preferenceIsUserSet")
        return None

    if node.name == "versionCompare":
        _add_warning(warnings, "|versionCompare")
        return None

    _add_warning(warnings, f"|{node.name}")
    return None


def _is_version_compare_node(node) -> bool:
    return isinstance(node, Transform) and node.name == "versionCompare"


def _extract_major_version(version_str: str) -> Optional[int]:
    m = _VERSION_PATTERN.match(str(version_str).strip("'\""))
    return int(m.group(1)) if m else None


def _version_compare_binary_to_sql(
    node: BinaryExpression, warnings: list[str], column_map: dict[str, str]
) -> Optional[str]:
    """version|versionCompare('X.!') <op> 0 → firefox_version <op> X"""
    return _version_compare_binary_to_sql_with(
        transform=node.left,
        op_symbol=node.operator.symbol,
        comparand_value=node.right.value,
        warnings=warnings,
        column_map=column_map,
    )


def _version_compare_binary_to_sql_reversed(
    node: BinaryExpression, warnings: list[str], column_map: dict[str, str]
) -> Optional[str]:
    # 0 <= version|versionCompare('X') → flip operands and operator, reuse same logic
    reverse_op = {
        ">=": "<=",
        ">": "<",
        "<=": ">=",
        "<": ">",
        "==": "=",
        "!=": "!=",
    }
    flipped_op = reverse_op.get(node.operator.symbol)
    if not flipped_op:
        _add_warning(warnings, "|versionCompare")
        return None

    # node.right is the versionCompare transform, node.left is the literal (e.g. 0)
    # Swap so the transform is on the left and the literal on the right
    return _version_compare_binary_to_sql_with(
        transform=node.right,
        op_symbol=flipped_op,
        comparand_value=node.left.value,
        warnings=warnings,
        column_map=column_map,
    )


def _version_compare_binary_to_sql_with(
    transform,
    op_symbol: str,
    comparand_value,
    warnings: list[str],
    column_map: dict[str, str],
) -> Optional[str]:
    if comparand_value != 0:
        _add_warning(warnings, "|versionCompare")
        return None

    subject_path = _identifier_path(transform.subject)
    if subject_path != "version":
        _add_warning(warnings, subject_path or "|versionCompare")
        return None

    version_col = column_map.get("firefoxVersion")
    if version_col is None:
        _add_warning(warnings, "|versionCompare")
        return None

    if not transform.args:
        _add_warning(warnings, "|versionCompare")
        return None

    version_arg = transform.args[0]
    version_str = version_arg.value if isinstance(version_arg, Literal) else None
    major = _extract_major_version(version_str) if version_str else None

    if major is None:
        _add_warning(warnings, "|versionCompare")
        return None

    op_map = {">=": ">=", ">": ">", "<=": "<=", "<": "<", "==": "=", "!=": "!="}
    sql_op = op_map.get(op_symbol)
    if sql_op is None:
        _add_warning(warnings, "|versionCompare")
        return None

    return f"{version_col} {sql_op} {major}"


def _identifier_path(node) -> str:
    if node is None:
        return ""
    if isinstance(node, Identifier):
        subject = _identifier_path(node.subject)
        return f"{subject}.{node.value}" if subject else node.value
    if isinstance(node, Literal):
        return str(node.value)
    return ""


def _literal_value(node) -> Optional[str]:
    if isinstance(node, Literal) and isinstance(node.value, str):
        return node.value
    return None


def ensure_bool_sql(sql: str) -> str:
    """Coerce a SQL expression to BOOL if it is a STRING (e.g. from preferenceValue).

    Used when the expression must be a BOOL, e.g. as the argument to COUNTIF.
    """
    if _is_boolean_sql(sql):
        return sql
    return _coerce_to_bool(sql)


def _is_json_string_expr(sql: str) -> bool:
    """Returns True if the SQL expression produces a STRING value.

    Used to detect when a boolean literal (TRUE/FALSE) would cause a type mismatch
    in a comparison — e.g. JSON_VALUE(...) = FALSE should become = 'false'.
    """
    return sql.startswith(("JSON_VALUE(", "metrics.string."))


def _is_untranslatable(path: str) -> bool:
    if path in KNOWN_UNTRANSLATABLE:
        return True
    parts = path.split(".")
    return any(".".join(parts[:i]) in KNOWN_UNTRANSLATABLE for i in range(1, len(parts)))


def _coerce_to_bool(sql: str) -> str:
    """Wrap a STRING SQL expression as BOOL for use in AND/OR.

    JSON_VALUE always returns STRING. When a pref value is used as a bare
    boolean in JEXL (truthy = non-null, non-empty, non-'false'), convert it
    to a BQ BOOL comparison so AND/OR don't error on STRING types.

    Numeric literals (e.g. from JEXL patterns like `bool && 1 || 0`) are
    converted to TRUE/FALSE so they don't produce INT64 != STRING comparisons.
    """
    if _is_boolean_sql(sql):
        return sql
    # Numeric literal: non-zero is truthy in JEXL, zero is falsy.
    try:
        return "TRUE" if float(sql) != 0 else "FALSE"
    except (ValueError, TypeError):
        pass
    # For STRING expressions: treat null/empty/'false' as falsy, anything else truthy
    return f"({sql} IS NOT NULL AND {sql} != '' AND {sql} != 'false')"


def _is_boolean_sql(sql: str) -> bool:
    sql_upper = sql.upper()
    return (
        sql_upper in ("TRUE", "FALSE")
        or sql.startswith("metrics.boolean.")
        or sql_upper.endswith(("AS BOOL)", "AS BOOLEAN)"))
        or " IN UNNEST(" in sql_upper
        or " IN (" in sql_upper  # X IN (list) returns BOOL
        or " IS NULL" in sql_upper
        or " IS NOT NULL" in sql_upper
        or sql_upper.startswith("NOT (")
        or " AND " in sql_upper
        or " OR " in sql_upper
        or " = " in sql
        or " != " in sql
        or " >= " in sql
        or " <= " in sql
        or " > " in sql
        or " < " in sql
    )


def _add_warning(warnings: list[str], attribute: str):
    if attribute and attribute not in warnings:
        warnings.append(attribute)
