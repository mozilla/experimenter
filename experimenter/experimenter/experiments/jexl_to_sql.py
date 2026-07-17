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
    # Mobile-only attributes
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

_VERSION_PATTERN = re.compile(r"^(\d+)")


@dataclasses.dataclass
class JEXLToSQLResult:
    sql: Optional[str]
    warnings: list[str]


def jexl_to_sql(jexl_expression: str) -> JEXLToSQLResult:
    """
    Translate a JEXL targeting expression into a BigQuery SQL WHERE clause.

    Returns sql=None with a warnings list when nothing can be translated.
    Returns partial sql with warnings when only some clauses translate.
    """
    if not jexl_expression or jexl_expression == "true":
        return JEXLToSQLResult(sql=None, warnings=[])

    warnings: list[str] = []
    try:
        ast = JEXLParser().parse(jexl_expression)
        sql = _node_to_sql(ast, warnings)
    except Exception:
        return JEXLToSQLResult(sql=None, warnings=["__parse_error__"])

    return JEXLToSQLResult(sql=sql or None, warnings=warnings)


def _node_to_sql(node, warnings: list[str]) -> Optional[str]:
    if isinstance(node, BinaryExpression):
        return _binary_to_sql(node, warnings)
    if isinstance(node, UnaryExpression):
        return _unary_to_sql(node, warnings)
    if isinstance(node, Identifier):
        return _identifier_to_sql(node, warnings)
    if isinstance(node, Literal):
        return _literal_to_sql(node)
    if isinstance(node, ArrayLiteral):
        return _array_to_sql(node, warnings)
    if isinstance(node, Transform):
        return _transform_to_sql(node, warnings)
    if isinstance(node, FilterExpression):
        subject_path = _identifier_path(node.subject)
        # addonsInfo.addons['addon-id'] — check addon ID membership in BQ array
        if subject_path == "addonsInfo.addons" and isinstance(node.expression, Literal):
            addon_id = node.expression.value
            if isinstance(addon_id, str):
                return f"'{addon_id}' IN UNNEST(JSON_VALUE_ARRAY({_AI}, '$.addons'))"
        _add_warning(warnings, subject_path or _identifier_path(node.subject))
        return None
    return None


def _binary_to_sql(node: BinaryExpression, warnings: list[str]) -> Optional[str]:
    op = node.operator.symbol

    if _is_version_compare_node(node.left) and isinstance(node.right, Literal):
        return _version_compare_binary_to_sql(node, warnings)
    if _is_version_compare_node(node.right) and isinstance(node.left, Literal):
        return _version_compare_binary_to_sql_reversed(node, warnings)

    if op in ("&&", "||"):
        left = _node_to_sql(node.left, warnings)
        right = _node_to_sql(node.right, warnings)
        if left and right:
            sql_op = "AND" if op == "&&" else "OR"
            return f"({left} {sql_op} {right})"
        return left or right

    left = _node_to_sql(node.left, warnings)
    right = _node_to_sql(node.right, warnings)
    if left is None or right is None:
        return None

    if op == "in":
        return f"{left} IN {right}"

    comparison_ops = {
        "==": "=",
        "!=": "!=",
        "<": "<",
        "<=": "<=",
        ">": ">",
        ">=": ">=",
    }
    arithmetic_ops = {"+": "+", "-": "-", "*": "*", "/": "/", "%": "%"}

    if op in comparison_ops:
        return f"{left} {comparison_ops[op]} {right}"
    if op in arithmetic_ops:
        return f"({left} {arithmetic_ops[op]} {right})"
    return None


def _unary_to_sql(node: UnaryExpression, warnings: list[str]) -> Optional[str]:
    if node.operator.symbol == "!":
        inner = _node_to_sql(node.right, warnings)
        if inner:
            if _is_boolean_sql(inner):
                return f"NOT ({inner})"
            # NOT (string) is invalid in BigQuery — JEXL falsy means null or empty
            return f"({inner} IS NULL OR {inner} = '')"
    return None  # pragma: no cover — pyjexl only produces UnaryExpression for "!"


def _identifier_to_sql(node: Identifier, warnings: list[str]) -> Optional[str]:
    path = _identifier_path(node)

    if path == "null":
        return "NULL"

    # Explicit mappings take priority over parent being in KNOWN_UNTRANSLATABLE
    if path in JEXL_TO_BQ_COLUMN:
        return JEXL_TO_BQ_COLUMN[path]

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


def _array_to_sql(node: ArrayLiteral, warnings: list[str]) -> Optional[str]:
    items = [_node_to_sql(item, warnings) for item in node.value]
    items = [i for i in items if i is not None]
    if not items:
        return None
    return f"({', '.join(items)})"


def _transform_to_sql(node: Transform, warnings: list[str]) -> Optional[str]:
    subject_path = _identifier_path(node.subject)

    # If the subject itself is untranslatable, warn about it rather than the transform
    if subject_path and _is_untranslatable(subject_path):
        _add_warning(warnings, subject_path)
        return None

    if node.name == "date":
        # profileAgeCreated is stored as epoch ms — return column directly for arithmetic
        if subject_path == "profileAgeCreated":
            return JEXL_TO_BQ_COLUMN["profileAgeCreated"]
        if subject_path == "currentDate":
            return "UNIX_MILLIS(CURRENT_TIMESTAMP())"
        _add_warning(warnings, "|date")
        return None

    if node.name == "length":
        if subject_path == "userMonthlyActivity":
            return f"JSON_ARRAY_LENGTH({_USER_MONTHLY_ACTIVITY_COL})"
        subject_sql = _node_to_sql(node.subject, warnings)
        if subject_sql:
            return f"JSON_ARRAY_LENGTH({subject_sql})"
        _add_warning(warnings, "|length")
        return None

    if node.name == "preferenceValue":
        # Pref names stored with dots replaced by __ in BigQuery
        pref_name = _literal_value(node.subject)
        if pref_name:
            bq_key = pref_name.replace(".", "__")
            return f"JSON_VALUE({_PREF_VALUES_COL}, '$.{bq_key}')"
        _add_warning(warnings, "|preferenceValue")
        return None

    if node.name == "preferenceIsUserSet":
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
    node: BinaryExpression, warnings: list[str]
) -> Optional[str]:
    """version|versionCompare('X.!') <op> 0 → firefox_version <op> X"""
    return _version_compare_binary_to_sql_with(
        transform=node.left,
        op_symbol=node.operator.symbol,
        comparand_value=node.right.value,
        warnings=warnings,
    )


def _version_compare_binary_to_sql_reversed(
    node: BinaryExpression, warnings: list[str]
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
    )


def _version_compare_binary_to_sql_with(
    transform, op_symbol: str, comparand_value, warnings: list[str]
) -> Optional[str]:
    if comparand_value != 0:
        _add_warning(warnings, "|versionCompare")
        return None

    subject_path = _identifier_path(transform.subject)
    if subject_path != "version":
        _add_warning(warnings, subject_path or "|versionCompare")
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

    return f"{JEXL_TO_BQ_COLUMN['firefoxVersion']} {sql_op} {major}"


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


def _is_untranslatable(path: str) -> bool:
    if path in KNOWN_UNTRANSLATABLE:
        return True
    parts = path.split(".")
    return any(".".join(parts[:i]) in KNOWN_UNTRANSLATABLE for i in range(1, len(parts)))


def _is_boolean_sql(sql: str) -> bool:
    sql_upper = sql.upper()
    return (
        sql.startswith("metrics.boolean.")
        or sql_upper.endswith(("AS BOOL)", "AS BOOLEAN)"))
        or " IN UNNEST(" in sql_upper
    )


def _add_warning(warnings: list[str], attribute: str):
    if attribute and attribute not in warnings:
        warnings.append(attribute)
