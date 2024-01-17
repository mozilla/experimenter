from dataclasses import dataclass

from django.db import models

from experimenter.experiments.constants import Application, NimbusConstants

# The identifiers in the exressions of the targeting field can be found
# here: https://searchfox.org/mozilla-central/source/browser/components/newtab/lib/ASRouterTargeting.jsm#526
# and here:
# https://searchfox.org/mozilla-central/source/toolkit/components/nimbus/lib/ExperimentManager.sys.mjs#94`


@dataclass
class NimbusTargetingConfig:
    name: str
    slug: str
    description: str
    targeting: str
    desktop_telemetry: str
    sticky_required: bool
    is_first_run_required: bool
    application_choice_names: list[str]

    targeting_configs = []

    def __post_init__(self):
        self.targeting_configs.append(self)


HAS_PIN = "!doesAppNeedPin"
NEED_DEFAULT = "!isDefaultBrowser"
PROFILE28DAYS = "(currentDate|date - profileAgeCreated|date) / 86400000 >= 28"
PROFILELESSTHAN28DAYS = "(currentDate|date - profileAgeCreated|date) / 86400000 < 28"
PROFILEMORETHAN7DAYS = "(currentDate|date - profileAgeCreated|date) / 86400000 > 7"
NEW_PROFILE = "(currentDate|date - profileAgeCreated|date) / 3600000 <= 24"
WIN1903 = "os.windowsBuildNumber >= 18362"
CORE_ACTIVE_USERS_TARGETING = "'{event}'|eventCountNonZero('Days', 28, 0) >= 21"
RECENTLY_LOGGED_IN_USERS_TARGETING = "'{event}'|eventCountNonZero('Weeks', 12, 0) >= 1"

NO_TARGETING = NimbusTargetingConfig(
    name="No Targeting",
    slug="no_targeting",
    description="All users",
    targeting="",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=[a.name for a in Application],
)

ATTRIBUTION_MEDIUM_EMAIL = NimbusTargetingConfig(
    name="Attribution Medium Email",
    slug="attribution_medium_email",
    description="Firefox installed with email attribution",
    targeting="attributionData.medium == 'email'",
    desktop_telemetry="environment.settings.attribution.medium = 'email'",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

ATTRIBUTION_MEDIUM_PAIDSEARCH = NimbusTargetingConfig(
    name="Attribution Medium Paidsearch",
    slug="attribution_medium_paidsearch",
    description="Firefox installed with paidsearch attribution",
    targeting="attributionData.medium == 'paidsearch'",
    desktop_telemetry="environment.settings.attribution.medium = 'paidsearch'",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

NEW_PROFILE_CREATED = NimbusTargetingConfig(
    name="New profile created",
    slug="new_profile_created",
    description="Profile with creation date within 24 hours",
    targeting=NEW_PROFILE,
    desktop_telemetry="environment.profile.creation_date",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

NOT_NEW_PROFILE_CREATED = NimbusTargetingConfig(
    name="Not new profile created",
    slug="not_new_profile_created",
    description="Profile with creation date over 24 hours",
    targeting=f"!({NEW_PROFILE_CREATED.targeting})",
    desktop_telemetry=f"NOT ({NEW_PROFILE_CREATED.desktop_telemetry})",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

FIRST_RUN = NimbusTargetingConfig(
    name="First start-up users",
    slug="first_run",
    description=("First start-up users (e.g. for about:welcome)"),
    targeting="({is_first_startup} && {not_see_aw})".format(
        is_first_startup="isFirstStartup",
        not_see_aw="!('trailhead.firstrun.didSeeAboutWelcome'|preferenceValue)",
    ),
    desktop_telemetry=("payload.info.profile_subsession_counter = 1"),
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

FIRST_RUN_NEW_PROFILE = NimbusTargetingConfig(
    name="First start-up new users",
    slug="first_run_new_profile",
    description="First start-up users (e.g. for about:welcome) with a new profile",
    targeting=f"{FIRST_RUN.targeting} && {NEW_PROFILE_CREATED.targeting}",
    desktop_telemetry=f"{FIRST_RUN.desktop_telemetry} AND "
    f"{NEW_PROFILE_CREATED.desktop_telemetry}",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

FIRST_RUN_NEW_PROFILE_ATTRIBUTION_MEDIUM_PAIDSEARCH = NimbusTargetingConfig(
    name="First start-up new users with paidsearch attribution",
    slug="first_run_new_profile_attribution_medium_paidsearch",
    description="First start-up new users installed with paidsearch attribution",
    targeting=f"{FIRST_RUN_NEW_PROFILE.targeting} && "
    f"{ATTRIBUTION_MEDIUM_PAIDSEARCH.targeting}",
    desktop_telemetry=f"{FIRST_RUN_NEW_PROFILE.desktop_telemetry} AND "
    f"{ATTRIBUTION_MEDIUM_PAIDSEARCH.desktop_telemetry}",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

FIRST_RUN_CHROME_ATTRIBUTION = NimbusTargetingConfig(
    name="First start-up users from Chrome",
    slug="first_run_chrome",
    description=(
        "First start-up users (e.g. for about:welcome) who download Firefox "
        "from Chrome"
    ),
    targeting=f"{FIRST_RUN.targeting} && attributionData.ua == 'chrome'",
    desktop_telemetry=(
        "{first_run} AND environment.settings.attribution.ua = 'chrome'"
    ).format(first_run=FIRST_RUN.desktop_telemetry),
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

FIRST_RUN_WINDOWS_1903_NEWER = NimbusTargetingConfig(
    name="First start-up users on Windows 10 1903 (build 18362) or newer",
    slug="first_run_win1903",
    description="First start-up users (e.g. for about:welcome) on Windows 1903+",
    targeting=f"{FIRST_RUN.targeting} && os.windowsBuildNumber >= 18362",
    desktop_telemetry=(
        "{first_run} AND environment.system.os.windows_build_number >= 18362"
    ).format(first_run=FIRST_RUN.desktop_telemetry),
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

FIRST_RUN_NEW_PROFILE_WINDOWS_1903_NEWER = NimbusTargetingConfig(
    name=(
        "First start-up users with a new profile, "
        "on Windows 10 1903 (build 18362) or newer"
    ),
    slug="first_run_new_profile_win1903",
    description=(
        "First start-up users (e.g. for about:welcome), with a "
        "new profile, on Windows 1903+"
    ),
    targeting=(
        f"{FIRST_RUN.targeting} && os.windowsBuildNumber >= 18362 && {NEW_PROFILE}"
    ),
    desktop_telemetry=(
        "{first_run} AND environment.system.os.windows_build_number >= 18362 "
        "AND {new_profile}"
    ).format(first_run=FIRST_RUN.desktop_telemetry, new_profile=NEW_PROFILE),
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

FIRST_RUN_NEW_PROFILE_WINDOWS_11_NEED_DEFAULT_NEED_PIN = NimbusTargetingConfig(
    name=(
        "First start-up users with a new profile, "
        "on Windows 11 (build 22621) or newer, needing pin and default"
    ),
    slug="first_run_new_profile_win11",
    description=(
        "First start-up users (e.g. for about:welcome), with a "
        "new profile, on Windows 22621+, needing pin and default"
    ),
    targeting=(
        f"{FIRST_RUN.targeting} && doesAppNeedPin && os.windowsBuildNumber >= 22621 && "
        f"{NEW_PROFILE} && {NEED_DEFAULT}"
    ),
    desktop_telemetry=(
        "{first_run} AND environment.system.os.windows_build_number >= 22621 "
        "AND {new_profile} AND !isDefaultBrowser AND doesAppNeedPin"
    ).format(first_run=FIRST_RUN.desktop_telemetry, new_profile=NEW_PROFILE),
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

FIRST_RUN_NEW_PROFILE_NEED_DEFAULT_WINDOWS_1903 = NimbusTargetingConfig(
    name=(
        "First start-up users on Windows 10 1903 (build 18362) or newer, with a "
        "new profile, needing default"
    ),
    slug="first_run_new_profile_need_default",
    description=(
        "First start-up users (e.g. for about:welcome) on Windows 1903+, "
        "with a new profile, needing default"
    ),
    targeting=(
        f"{FIRST_RUN.targeting} && os.windowsBuildNumber >= 18362 && {NEW_PROFILE} && "
        f"{NEED_DEFAULT}"
    ),
    desktop_telemetry=(
        "{first_run} AND environment.system.os.windows_build_number >= 18362 AND "
        "!isDefaultBrowser AND {new_profile}"
    ).format(first_run=FIRST_RUN.desktop_telemetry, new_profile=NEW_PROFILE),
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

FIRST_RUN_NEW_PROFILE_NEED_DEFAULT_WINDOWS_1903_PREFER_MOTION = NimbusTargetingConfig(
    name=(
        "First start-up users on Windows 10 1903 needing default and no prefer "
        "reduced motion"
    ),
    slug="first_run_new_profile_need_default_prefers_motion",
    description=(
        "First start-up users (e.g. for about:welcome) on Windows 1903+, "
        "with a new profile, needing default, preferring motion"
    ),
    targeting=(
        "{first_run} && !userPrefersReducedMotion".format(
            first_run=FIRST_RUN_NEW_PROFILE_NEED_DEFAULT_WINDOWS_1903.targeting,
        )
    ),
    desktop_telemetry=(
        "{first_run} AND !userPrefersReducedMotion".format(
            first_run=FIRST_RUN_NEW_PROFILE_NEED_DEFAULT_WINDOWS_1903.desktop_telemetry,
        )
    ).format(first_run=FIRST_RUN.desktop_telemetry),
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

FIRST_RUN_NEW_PROFILE_NEED_DEFAULT_NEED_PIN_WINDOWS_1903 = NimbusTargetingConfig(
    name=(
        "First start-up users on Windows 10 1903 (build 18362) or newer, with a "
        "new profile, needing default & pin"
    ),
    slug="first_run_need_default_need_pin",
    description=(
        "First start-up users (e.g. for about:welcome) on Windows 1903+, "
        "with a new profile, needing default & pin"
    ),
    targeting=(
        f"{FIRST_RUN_NEW_PROFILE_NEED_DEFAULT_WINDOWS_1903.targeting} && doesAppNeedPin"
    ),
    desktop_telemetry=(
        "{first_run} AND doesAppNeedPin".format(
            first_run=FIRST_RUN_NEW_PROFILE_NEED_DEFAULT_WINDOWS_1903.desktop_telemetry,
        )
    ),
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

FIRST_RUN_NEW_PROFILE_HAS_PIN_NEED_DEFAULT_WINDOWS_1903 = NimbusTargetingConfig(
    name=(
        "First start-up users on Windows 10 1903 (build 18362) or newer, with a "
        "new profile, needing default w/ pin"
    ),
    slug="first_run_new_profile_need_default_has_pin",
    description=(
        "First start-up users (e.g. for about:welcome) on Windows 1903+, "
        "with a new profile, needing default w/ pin"
    ),
    targeting=(
        f"{FIRST_RUN_NEW_PROFILE_NEED_DEFAULT_WINDOWS_1903.targeting} && {HAS_PIN}"
    ),
    desktop_telemetry=(
        "{first_run} AND {has_pin}".format(
            first_run=FIRST_RUN_NEW_PROFILE_NEED_DEFAULT_WINDOWS_1903.desktop_telemetry,
            has_pin=HAS_PIN,
        )
    ),
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

FIRST_RUN_NEW_PROFILE_WINDOWS_1903_EXCLUDE_RTAMO = NimbusTargetingConfig(
    name=(
        "First start-up users on Windows 10 1903 (build 18362) or newer, with a "
        "new profile, needing default w/ pin, excluding users coming from RTAMO"
    ),
    slug="first_run_new_profile_exclude_rtamo",
    description=(
        "First start-up users (e.g. for about:welcome) on Windows 1903+, "
        "with a new profile, needing default w/ pin, excluding RTAMO"
    ),
    targeting=(
        "{first_run} && {has_pin} && {attribution}".format(
            first_run=FIRST_RUN_NEW_PROFILE_NEED_DEFAULT_WINDOWS_1903.targeting,
            has_pin=HAS_PIN,
            attribution="attributionData.source != 'addons.mozilla.org'",
        )
    ),
    desktop_telemetry=(
        "{first_run} AND {has_pin} AND {attribution}".format(
            first_run=FIRST_RUN_NEW_PROFILE_NEED_DEFAULT_WINDOWS_1903.desktop_telemetry,
            has_pin=HAS_PIN,
            attribution="attributionData.source != 'addons.mozilla.org'",
        )
    ),
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

FIRST_RUN_NEW_PROFILE_WINDOWS_1903_PAIDSEARCH = NimbusTargetingConfig(
    name=(
        "First start-up users on Windows 10 1903 (build 18362) or newer, with a "
        "new profile, needing default, with paidsearch attribution"
    ),
    slug="first_run_new_profile_paidsearch",
    description=(
        "First start-up users (e.g. for about:welcome) on Windows 1903+, "
        "with a new profile, needing default, with paidsearch attribution"
    ),
    targeting=(
        "{first_run} && {attribution}".format(
            first_run=FIRST_RUN_NEW_PROFILE_NEED_DEFAULT_WINDOWS_1903.targeting,
            attribution=ATTRIBUTION_MEDIUM_PAIDSEARCH.targeting,
        )
    ),
    desktop_telemetry=(
        "{first_run} AND {attribution}".format(
            first_run=FIRST_RUN_NEW_PROFILE_NEED_DEFAULT_WINDOWS_1903.desktop_telemetry,
            attribution=ATTRIBUTION_MEDIUM_PAIDSEARCH.targeting,
        )
    ),
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

NOT_TCP_STUDY = NimbusTargetingConfig(
    name="Exclude users in the TCP revenue study",
    slug="not_tcp_study",
    description="Exclude users with certain search codes set",
    targeting=(
        "!'browser.search.param.google_channel_us'|preferenceValue('')|regExpMatch"
        "('^[ntc]us5$') && !'browser.search.param.google_channel_row'|preferenceValue('')"
        "|regExpMatch('^[ntc]row5$')"
    ),
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

NOT_TCP_STUDY_FIRST_RUN = NimbusTargetingConfig(
    name="First start-up users excluding TCP revenue study",
    slug="not_tcp_study_first_run",
    description="First start-up users excluding certain search codes",
    targeting=f"{FIRST_RUN.targeting} && {NOT_TCP_STUDY.targeting}",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

WINDOWS_WITH_USERCHOICE = NimbusTargetingConfig(
    name="Users on Windows with UserChoice support",
    slug="windows_userchoice",
    description=(
        "Users on Windows with UserChoice support (version 1809+/build ID 17763+)"
    ),
    targeting="os.windowsBuildNumber >= 17763",
    desktop_telemetry="environment.system.os.windows_build_number >= 17763",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

WINDOWS_WITH_USERCHOICE_FIRST_RUN = NimbusTargetingConfig(
    name="First start-up users on Windows with UserChoice support",
    slug="windows_userchoice_first_run",
    description=(
        "First start-up users (e.g. for about:welcome) on Windows with "
        "UserChoice support (version 1809+/build ID 17763+)"
    ),
    targeting=f"{FIRST_RUN.targeting} && {WINDOWS_WITH_USERCHOICE.targeting}",
    desktop_telemetry=("{first_run} AND {user_choice}").format(
        first_run=FIRST_RUN.desktop_telemetry,
        user_choice=WINDOWS_WITH_USERCHOICE.desktop_telemetry,
    ),
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

FX95_DESKTOP_USERS = NimbusTargetingConfig(
    name="Desktop Users on Fx95",
    slug="fx95_desktop_users",
    description=("Firefox 95 Desktop users"),
    targeting=(
        "(version|versionCompare('95.!') >= 0) && (version|versionCompare('96.!') < 0)"
    ),
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

MOBILE_NEW_USER = NimbusTargetingConfig(
    name="New Users on Mobile",
    slug="mobile_new_users",
    description=("New users on mobile who installed the app less than a week ago"),
    targeting="days_since_install < 7",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(
        Application.FENIX.name,
        Application.IOS.name,
        Application.FOCUS_ANDROID.name,
        Application.FOCUS_IOS.name,
        Application.KLAR_ANDROID.name,
        Application.KLAR_IOS.name,
    ),
)
MOBILE_FIRST_RUN_USER = NimbusTargetingConfig(
    name="First run Users on Mobile",
    slug="mobile_first_run",
    description="First-run users on Fenix and Firefox for iOS",
    targeting="isFirstRun == 'true'",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=True,
    application_choice_names=(
        Application.FENIX.name,
        Application.IOS.name,
    ),
)

MOBILE_RECENTLY_UPDATED = NimbusTargetingConfig(
    name="Recently Updated Users",
    slug="mobile_recently_updated_users",
    description=(
        "Users who updated their app within the last week. "
        "This excludes users who are new users"
    ),
    targeting="days_since_update < 7 && days_since_install >= 7",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(
        Application.FENIX.name,
        Application.IOS.name,
        Application.FOCUS_ANDROID.name,
        Application.FOCUS_IOS.name,
        Application.KLAR_ANDROID.name,
        Application.KLAR_IOS.name,
    ),
)


HOMEPAGE_GOOGLE = NimbusTargetingConfig(
    name="Homepage set to google.com",
    slug="homepage_google_dot_com",
    description="Users with their Homepage set to google.com",
    targeting=(
        "!homePageSettings.isDefault && "
        "homePageSettings.isCustomUrl && "
        "homePageSettings.urls[.host == 'google.com']|length > 0"
    ),
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

URLBAR_FIREFOX_SUGGEST = NimbusTargetingConfig(
    name="Urlbar (Firefox Suggest)",
    slug="urlbar_firefox_suggest",
    description="Users with the default search suggestion showing order",
    targeting="'browser.urlbar.showSearchSuggestionsFirst'|preferenceValue",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

URLBAR_FIREFOX_SUGGEST_DATA_COLLECTION_ENABLED = NimbusTargetingConfig(
    name="Urlbar (Firefox Suggest) - Data Collection Enabled",
    slug="urlbar_firefox_suggest_data_collection_enabled",
    description="Users with Firefox Suggest data collection enabled",
    targeting="'browser.urlbar.quicksuggest.dataCollection.enabled'|preferenceValue",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

URLBAR_FIREFOX_SUGGEST_DATA_COLLECTION_DISABLED = NimbusTargetingConfig(
    name="Urlbar (Firefox Suggest) - Data Collection Disabled",
    slug="urlbar_firefox_suggest_data_collection_disabled",
    description="Users with Firefox Suggest data collection disabled",
    targeting="!('browser.urlbar.quicksuggest.dataCollection.enabled'|preferenceValue)",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

URLBAR_FIREFOX_SUGGEST_SPONSORED_ENABLED = NimbusTargetingConfig(
    name="Urlbar (Firefox Suggest) - Sponsored Suggestions Enabled",
    slug="urlbar_firefox_suggest_sponsored_enabled",
    description=(
        "Users with sponsored Firefox Suggest suggestions enabled "
        "(IMPORTANT: You must restrict 'Locales' to one or more Suggest "
        "locales when using this!)"
    ),
    targeting=(
        "!('browser.urlbar.suggest.quicksuggest.sponsored'|preferenceIsUserSet) || "
        "'browser.urlbar.suggest.quicksuggest.sponsored'|preferenceValue"
    ),
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

MAC_ONLY = NimbusTargetingConfig(
    name="Mac OS users only",
    slug="mac_only",
    description="All users with Mac OS",
    targeting="os.isMac",
    desktop_telemetry="environment.system.os.name = 'Darwin'",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

NO_DISTRIBUTIONS = NimbusTargetingConfig(
    name="No distribution builds",
    slug="no_distribution_builds",
    description="Exclude users with distribution builds",
    targeting="!distributionId",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

NO_ENTERPRISE = NimbusTargetingConfig(
    name="No enterprise users",
    slug="no_enterprise_users",
    description="Exclude users with active enterpries policies",
    targeting="!hasActiveEnterprisePolicies",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

NO_AUTOFILL_ADDRESSES = NimbusTargetingConfig(
    name="No autofill addresses saved",
    slug="no_autofill_addresses",
    description="Only users who have 0 autofill addresses.",
    targeting="(addressesSaved == 0)",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

RELAY_USER = NimbusTargetingConfig(
    name="Relay user",
    slug="relay_user",
    description="Include users who have Relay",
    targeting=('("9ebfe2c2f9ea3c58" in attachedFxAOAuthClients|mapToProperty("id"))'),
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

NOT_RELAY_USER = NimbusTargetingConfig(
    name="Not Relay user",
    slug="not_relay_user",
    description="Excludes users who have Relay",
    targeting=f"!({RELAY_USER.targeting}) && isFxAEnabled && usesFirefoxSync",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

NOT_RELAY_USER_WITH_NO_AUTOFILL_ADDRESSES = NimbusTargetingConfig(
    name="FXA user without Relay & no autofill addresses saved",
    slug="not_relay_user_no_autofill_addresses",
    description="FXA user without Relay & no autofill addresses saved",
    targeting=f"{NOT_RELAY_USER.targeting} && {NO_AUTOFILL_ADDRESSES.targeting}",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

NO_ENTERPRISE_OR_PAST_VPN = NimbusTargetingConfig(
    name="No enterprise or past VPN use",
    slug="no_enterprise_or_past_vpn",
    description="Exclude users who have used Mozilla VPN or who are enterprise users",
    targeting=(
        f"{NO_ENTERPRISE.targeting} && "
        '!("e6eb0d1e856335fc" in attachedFxAOAuthClients|mapToProperty("id"))'
    ),
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

EXISTING_USER_NO_ENTERPRISE_OR_PAST_VPN = NimbusTargetingConfig(
    name="Existing users, no enterprise or past VPN use, on Mac, Linux, or Windows 10+",
    slug="existing_user_no_enterprise_or_past_vpn",
    description="Exclude users who have used Mozilla VPN or who are enterprise users",
    targeting=(
        f"{NO_ENTERPRISE.targeting} && "
        f"{PROFILE28DAYS} && "
        "(!os.isWindows || os.windowsBuildNumber >= 18362) && "
        "userMonthlyActivity|length >= 1 && "
        "!('e6eb0d1e856335fc' in attachedFxAOAuthClients|mapToProperty('id'))"
    ),
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

NEW_USER_NO_VPN_HAS_NOT_DISABLED_RECOMMEND_FEATURES = NimbusTargetingConfig(
    name=(
        "New users, no enterprise or past VPN use, hasn't disabled 'Recommend "
        "extensions/features'"
    ),
    slug="new_user_no_vpn_has_not_disabled_recommend_features",
    description=(
        "Profiles younger than 28 days, excluding users who have used Mozilla "
        "VPN, are enterprise users, or have disabled 'Recommend "
        "extensions/features'"
    ),
    targeting=(
        f"{NO_ENTERPRISE.targeting} && "
        f"{PROFILELESSTHAN28DAYS} && "
        "(!os.isWindows || os.windowsBuildNumber >= 18362) && "
        "!('e6eb0d1e856335fc' in attachedFxAOAuthClients|mapToProperty('id')) && "
        "'browser.newtabpage.activity-stream.asrouter.userprefs.cfr.features'|preferenceValue"
        " && "
        "'browser.newtabpage.activity-stream.asrouter.userprefs.cfr.addons'|preferenceValue"
    ),
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

EXISTING_USER_NO_VPN_HAS_NOT_DISABLED_RECOMMEND_FEATURES = NimbusTargetingConfig(
    name=(
        "Existing users, no enterprise or past VPN use, hasn't disabled "
        "'Recommend extensions/features'"
    ),
    slug="existing_user_no_vpn_has_not_disabled_recommend_features",
    description=(
        "Exclude users who have used Mozilla VPN, are enterprise users, or have"
        " disabled 'Recommend extensions/features'"
    ),
    targeting=(
        f"{EXISTING_USER_NO_ENTERPRISE_OR_PAST_VPN.targeting} && "
        "'browser.newtabpage.activity-stream.asrouter.userprefs.cfr.features'|preferenceValue"
        " && "
        "'browser.newtabpage.activity-stream.asrouter.userprefs.cfr.addons'|preferenceValue"
    ),
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

NO_VPN_HAS_NOT_DISABLED_RECOMMEND_FEATURES = NimbusTargetingConfig(
    name=(
        "All users, no enterprise or past VPN use, hasn't disabled "
        "'Recommend extensions/features'"
    ),
    slug="no_vpn_has_not_disabled_recommend_features",
    description=(
        "Exclude users who have used Mozilla VPN, are enterprise users, or have"
        " disabled 'Recommend extensions/features'"
    ),
    targeting=(
        f"{NO_ENTERPRISE_OR_PAST_VPN.targeting} && "
        "(!os.isWindows || os.windowsBuildNumber >= 18362) && "
        "'browser.newtabpage.activity-stream.asrouter.userprefs.cfr.features'|preferenceValue"
        " && "
        "'browser.newtabpage.activity-stream.asrouter.userprefs.cfr.addons'|preferenceValue"
    ),
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

NO_ENTERPRISE_OR_RECENT_VPN = NimbusTargetingConfig(
    name="No enterprise and no VPN connection in the last 30 days",
    slug="no_enterprise_or_last_30d_vpn_use",
    description="Exclude enterprise & users who have used MozVPN in the last 30 days",
    targeting=(
        f"{NO_ENTERPRISE.targeting} && "
        '(("e6eb0d1e856335fc" in attachedFxAOAuthClients|mapToProperty("id")) ? '
        '(attachedFxAOAuthClients[.id == "e6eb0d1e856335fc"].lastAccessedDaysAgo > 29) : '
        "true)"
    ),
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

INFREQUENT_USER_URIS = NimbusTargetingConfig(
    name="Infrequent user (uris)",
    slug="infrequent_user_uris",
    description="Between 1 and 6 days of activity in the past 28 days",
    targeting=(
        f"{PROFILE28DAYS} "
        "&& userMonthlyActivity|length >= 1 "
        "&& userMonthlyActivity|length <= 6"
    ),
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

INFREQUENT_USER_NEED_PIN = NimbusTargetingConfig(
    name="Infrequent user (need pin)",
    slug="infrequent_user_need_pin",
    description="Between 1 and 6 days of activity in the past 28 days needing pin",
    targeting=f"{INFREQUENT_USER_URIS.targeting} && doesAppNeedPin",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

INFREQUENT_USER_NEED_DEFAULT = NimbusTargetingConfig(
    name="Infrequent user (need default)",
    slug="infrequent_user_need_default",
    description="Between 1 and 6 days of activity in the past 28 days needing default",
    targeting=f"{INFREQUENT_USER_URIS.targeting} && {NEED_DEFAULT}",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

INFREQUENT_USER_NEED_DEFAULT_HAS_PIN = NimbusTargetingConfig(
    name="Infrequent user (need default, has pin)",
    slug="infrequent_user_need_default_has_pin",
    description="Between 1 & 6 days activity in past 28 days need default w/ pin",
    targeting=f"{INFREQUENT_USER_NEED_DEFAULT.targeting} && {HAS_PIN}",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

INFREQUENT_USER_HAS_DEFAULT_NEED_PIN = NimbusTargetingConfig(
    name="Infrequent user (has default, need pin)",
    slug="infrequent_user_has_default_need_pin",
    description="Between 1 & 6 days activity in past 28 days w/ default need pin",
    targeting=f"{INFREQUENT_USER_NEED_PIN.targeting} && isDefaultBrowser",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

INFREQUENT_WIN_USER_NEED_PIN = NimbusTargetingConfig(
    name="Infrequent Windows user (need pin)",
    slug="infrequent_windows_user_need_pin",
    description="Between 1 and 6 days of activity in the past 28 days needing pin on Win",
    targeting=f"{INFREQUENT_USER_NEED_PIN.targeting} && os.isWindows",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

INFREQUENT_WIN_USER_URIS = NimbusTargetingConfig(
    name="Infrequent Windows 1903+ user (need default)",
    slug="infrequent_win_user_uris",
    description="Infrequent non default users of past 28 days, on Windows 1903+",
    targeting=f"{INFREQUENT_USER_NEED_DEFAULT.targeting} && {WIN1903}",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

INFREQUENT_USER_FIVE_BOOKMARKS = NimbusTargetingConfig(
    name="Infrequent user (5 bookmarks)",
    slug="infrequent_user_5_bookmarks",
    description="Between 1-6 days of activity in past 28, has 5 bookmarks",
    # A proxy for "nothing has been imported". 5 is the default number of bookmarks
    # in a new profile created by (at least) 100 and newer, and probably
    # substantially older than that too.
    targeting=f"{INFREQUENT_USER_URIS.targeting} && totalBookmarksCount == 5",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

NEW_USER_WITH_7_28_DAY_PROFILE_AGE = NimbusTargetingConfig(
    name="New user with 7 to 28 day profile age",
    slug="new_user_with_7_28_day_profile_age",
    description="Users with a profile that is between 7-28 days old, inclusive",
    targeting=f"{PROFILELESSTHAN28DAYS} && {PROFILEMORETHAN7DAYS}",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

NEW_USER_WITH_INFREQUENT_USE = NimbusTargetingConfig(
    name="New user with infrequent use",
    slug="new_user_with_infrequent_use",
    description="0 - 6 days activity in past 28 & profile age 8-27 days",
    targeting=(
        f"{PROFILELESSTHAN28DAYS} "
        f"&& {PROFILEMORETHAN7DAYS} "
        "&& userMonthlyActivity|length <= 6"
    ),
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

NEW_WITH_INFREQUENT_USE_FIVE_BOOKMARKS = NimbusTargetingConfig(
    name="New user, infrequent use, 5 bookmarks",
    slug="new_with_infrequent_use_5_bookmarks",
    description="0-6 days act. in past 28, 5 bookmarks, profile 8-27 days, Mac or Win10+",
    targeting=(
        f"{NEW_USER_WITH_INFREQUENT_USE.targeting} "
        "&& ((os.isWindows && os.windowsVersion >= 10) "
        "|| os.isMac)"
    ),
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

CASUAL_USER_URIS = NimbusTargetingConfig(
    name="Casual user (uris)",
    slug="casual_user_uris",
    description="Between 7 and 13 days of activity in the past 28 days",
    targeting=(
        f"{PROFILE28DAYS} "
        "&& userMonthlyActivity|length >= 7 "
        "&& userMonthlyActivity|length <= 13"
    ),
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

CASUAL_USER_NEED_PIN = NimbusTargetingConfig(
    name="Casual user (need pin)",
    slug="casual_user_need_pin",
    description="Between 7 and 13 days of activity in the past 28 days needing pin",
    targeting=f"{CASUAL_USER_URIS.targeting} && doesAppNeedPin",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

CASUAL_USER_NEED_DEFAULT = NimbusTargetingConfig(
    name="Casual user (need default)",
    slug="casual_user_need_default",
    description="Between 7 and 14 days of activity in the past 28 days needing default",
    targeting=f"{CASUAL_USER_URIS.targeting} && {NEED_DEFAULT}",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

CASUAL_USER_NEED_DEFAULT_HAS_PIN = NimbusTargetingConfig(
    name="Casual user (need default, has pin)",
    slug="casual_user_need_default_has_pin",
    description="Between 7 and 14 days of activity in past 28 days need default w/ pin",
    targeting=f"{CASUAL_USER_NEED_DEFAULT.targeting} && {HAS_PIN}",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

CASUAL_USER_HAS_DEFAULT_NEED_PIN = NimbusTargetingConfig(
    name="Casual user (has default, need pin)",
    slug="casual_user_has_default_need_pin",
    description="Between 7 and 14 days of activity in past 28 days w/ default need pin",
    targeting=f"{CASUAL_USER_NEED_PIN.targeting} && isDefaultBrowser",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

REGULAR_USER_URIS = NimbusTargetingConfig(
    name="Regular user (uris)",
    slug="regular_user_uris",
    description="Between 14 and 20 days of activity in the past 28 days",
    targeting=(
        f"{PROFILE28DAYS} "
        "&& userMonthlyActivity|length >= 14 "
        "&& userMonthlyActivity|length <= 20"
    ),
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

REGULAR_USER_NEED_PIN = NimbusTargetingConfig(
    name="Regular user (need pin)",
    slug="regular_user_need_pin",
    description="Between 14 and 20 days of activity in the past 28 days needing pin",
    targeting=f"{REGULAR_USER_URIS.targeting} && doesAppNeedPin",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

REGULAR_USER_NEED_DEFAULT = NimbusTargetingConfig(
    name="Regular user (need default)",
    slug="regular_user_need_default",
    description="Between 14 and 20 days of activity in the past 28 days needing default",
    targeting=f"{REGULAR_USER_URIS.targeting} && {NEED_DEFAULT}",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

REGULAR_USER_NEED_DEFAULT_HAS_PIN = NimbusTargetingConfig(
    name="Regular user (need default, has pin)",
    slug="regular_user_need_default_has_pin",
    description="Between 14 and 20 days of activity in past 28 days need default w/ pin",
    targeting=f"{REGULAR_USER_NEED_DEFAULT.targeting} && {HAS_PIN}",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

REGULAR_USER_HAS_DEFAULT_NEED_PIN = NimbusTargetingConfig(
    name="Regular user (has default, need pin)",
    slug="regular_user_has_default_need_pin",
    description="Between 14 and 20 days of activity in past 28 days w/ default need pin",
    targeting=f"{REGULAR_USER_NEED_PIN.targeting} && isDefaultBrowser",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

REGULAR_USER_USES_FXA = NimbusTargetingConfig(
    name="Regular user (uses Firefox Accounts)",
    slug="regular_user_uses_fxa",
    description="Between 14 and 20 days of activity in the past 28 days signed in to FxA",
    targeting=f"{REGULAR_USER_URIS.targeting} && isFxAEnabled && usesFirefoxSync",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

CORE_USER_URIS = NimbusTargetingConfig(
    name="Core user (uris)",
    slug="core_user_uris",
    description="At least 21 days of activity in the past 28 days",
    targeting=f"{PROFILE28DAYS} && userMonthlyActivity|length >= 21",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

CORE_USER_NEED_PIN = NimbusTargetingConfig(
    name="Core user (need pin)",
    slug="core_user_need_pin",
    description="At least 21 days of activity in the past 28 days needing pin",
    targeting=f"{CORE_USER_URIS.targeting} && doesAppNeedPin",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

CORE_USER_NEED_DEFAULT = NimbusTargetingConfig(
    name="Core user (need default)",
    slug="core_user_need_default",
    description="At least 21 days of activity in the past 28 days needing default",
    targeting=f"{CORE_USER_URIS.targeting} && {NEED_DEFAULT}",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

CORE_USER_NEED_DEFAULT_HAS_PIN = NimbusTargetingConfig(
    name="Core user (need default, has pin)",
    slug="core_user_need_default_has_pin",
    description="At least 21 days of activity in past 28 days need default w/ pin",
    targeting=f"{CORE_USER_NEED_DEFAULT.targeting} && {HAS_PIN}",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

CORE_USER_HAS_DEFAULT_NEED_PIN = NimbusTargetingConfig(
    name="Core user (has default, need pin)",
    slug="core_user_has_default_need_pin",
    description="At least 21 days of activity in past 28 days w/ default need pin",
    targeting=f"{CORE_USER_NEED_PIN.targeting} && isDefaultBrowser",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

POCKET_COMMON = NimbusTargetingConfig(
    name="Pocket Common Filters",
    slug="pocket_common",
    description="All newtab sections are default",
    targeting="""
    (
        (
            (
                !('browser.newtabpage.enabled'|preferenceIsUserSet)
                ||
                !('browser.startup.homepage'|preferenceIsUserSet)
            )
            &&
            !('browser.newtabpage.activity-stream.showSearch'|preferenceIsUserSet)
            &&
            !('browser.newtabpage.activity-stream.feeds.topsites'|preferenceIsUserSet)
            &&
            !('browser.newtabpage.activity-stream.feeds.section.topstories'|preferenceIsUserSet)
            &&
            !('browser.newtabpage.activity-stream.feeds.section.highlights'|preferenceIsUserSet)
        )
    )
    """,
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

PIP_NEVER_USED = NimbusTargetingConfig(
    name="PiP Never Used",
    slug="pip_never_used",
    description="Users that have never used Picture in Picture",
    targeting="""
    (
        !('media.videocontrols.picture-in-picture.video-toggle.has-used'|preferenceValue)
        &&
        ('media.videocontrols.picture-in-picture.enabled'|preferenceValue)
        &&
        ('media.videocontrols.picture-in-picture.video-toggle.enabled'|preferenceValue)
    )
    """,
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

RALLY_CORE_ADDON_USER = NimbusTargetingConfig(
    name="Mozilla Rally Core Add-on User",
    slug="rally_core_addon_user",
    description="Users who have installed the Mozilla Rally Core Add-on",
    targeting="addonsInfo.addons['rally-core@mozilla.org'] != null",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

RALLY_PILOT_USER = NimbusTargetingConfig(
    name="Mozilla Rally Pilot User",
    slug="rally_pilot_user",
    description="Users who have installed \
    the Mozilla Rally Core Add-on or one of the Rally pilot studies",
    targeting="""
        addonsInfo.addons['rally-core@mozilla.org'] != null ||
        addonsInfo.addons['facebook-pixel-hunt@rally.mozilla.org'] != null ||
        addonsInfo.addons['beyond-the-paywall@rally.mozilla.org'] != null ||
        addonsInfo.addons['search-engine-usage@rally.mozilla.org'] != null ||
        addonsInfo.addons[
            'princeton-political-and-covid-19-news-study@rally.mozilla.org'
        ] != null
    """,
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

RALLY_ATTENTION_STREAM_USER = NimbusTargetingConfig(
    name="Mozilla Rally Attention Stream User",
    slug="rally_attention_stream_user",
    description="Users who have installed \
    the Mozilla Rally (f.k.a Attention Stream) Add-on",
    targeting="""
        addonsInfo.addons['attention-stream@rally.mozilla.org'] != null
    """,
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

REVIEW_CHECKER_SIDEBAR_RECOMMENDATION = NimbusTargetingConfig(
    name="Review Checker Sidebar Recommendation",
    slug="review_checker_sidebar_recommendation",
    description="Exclude users who have the Fakespot extension installed, "
    "or who have the CFR pref set to false",
    targeting="addonsInfo.addons['{44df5123-f715-9146-bfaa-c6e8d4461d44}'] == null && "
    "('browser.newtabpage.activity-stream.asrouter.userprefs.cfr.features'|preferenceValue)",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

EARLY_DAY_USER_REVIEW_CHECKER_SIDEBAR_RECOMMENDATION = NimbusTargetingConfig(
    name="Early Day User Review Checker Sidebar Recommendation",
    slug="early_day_user_review_checker_sidebar_recommendation",
    description="Exclude early day users who have the Fakespot extension installed, "
    "or who have the CFR pref set to false",
    targeting=(
        f"{PROFILELESSTHAN28DAYS} && {REVIEW_CHECKER_SIDEBAR_RECOMMENDATION.targeting}"
    ),
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

EXISTING_USER_REVIEW_CHECKER_SIDEBAR_RECOMMENDATION = NimbusTargetingConfig(
    name="Existing User Review Checker Sidebar Recommendation",
    slug="existing_user_review_checker_sidebar_recommendation",
    description="Exclude existing users who have the Fakespot extension installed, "
    "or who have the CFR pref set to false",
    targeting=(f"{PROFILE28DAYS} && {REVIEW_CHECKER_SIDEBAR_RECOMMENDATION.targeting}"),
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

BACKGROUND_TASK_NOTIFICATION = NimbusTargetingConfig(
    name="Background task notification",
    slug="Background_task_notification",
    description="Firefox running a background task",
    targeting="isBackgroundTaskMode",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

WINDOWS_10_PLUS_BACKGROUND_TASK_NOTIFICATION_ = NimbusTargetingConfig(
    name="Lapsed users background task notification",
    slug="background_task_notification_major_release_2022",
    description=(
        "Windows 10+ users with 0 days of activity in the past 28 days "
        "who are running a background task"
    ),
    targeting="""
    (
        (
            os.isWindows
            &&
            (os.windowsVersion >= 10)
        )
        &&
        (
            (
                ((defaultProfile|keys)|length == 0)
            )
            ||
            (
                ((currentDate|date - defaultProfile.currentDate|date) / 86400000 >= 28)
                &&
                (firefoxVersion > defaultProfile.firefoxVersion)
            )
        )
        &&
        isBackgroundTaskMode
    )
    """,
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

WINDOWS_10_PLUS_BACKGROUND_TASK_NOTIFICATION_AT_RISK_USER = NimbusTargetingConfig(
    name="At risk user background task notification",
    slug="background_task_notification_at_risk_user",
    description=(
        "Windows 10+ users with 20-28 days of activity in their past 28 days "
        "who have lapsed 7-28 days, and who are running a background task"
    ),
    targeting="""
    (
        (
            os.isWindows
            &&
            (os.windowsVersion >= 10)
        )
        &&
        (
            defaultProfile.userMonthlyActivity|length >= 20
        )
        &&
        (
            (
                (7 <= ((currentDate|date - defaultProfile.currentDate|date) / 86400000))
                &&
                (((currentDate|date - defaultProfile.currentDate|date) / 86400000) < 28)
            )
        )
        &&
        isBackgroundTaskMode
    )
    """,
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

WINDOWS_10_PLUS_BACKGROUND_TASK_NOTIFICATION_NEW_NON_DEFAULT_USER = NimbusTargetingConfig(
    name="New non-default user background task notification",
    slug="background_task_notification_new_non_default_user",
    description=(
        "Windows 10+ users with this Firefox not the default browser "
        "who created their profile exactly 7 days previously, "
        "and who are running a background task"
    ),
    targeting="""
    (
        (
            os.isWindows
            &&
            (os.windowsVersion >= 10)
        )
        &&
        !isDefaultBrowser
        &&
        (
            (7 <= ((currentDate|date - defaultProfile.profileAgeCreated|date) / 86400000))
            &&
            (((currentDate|date - defaultProfile.profileAgeCreated|date) / 86400000) < 8)
        )
        &&
        isBackgroundTaskMode
    )
    """,
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

NEWTAB_SPONSORED_TOPSITES_ENABLED = NimbusTargetingConfig(
    name="Newtab has Sponsored TopSites enabled ",
    slug="newtab_sponsored_topsites_enabled",
    description="Users with Sponsored TopSites enabled on the newtab",
    targeting="""
        'browser.newtabpage.activity-stream.showSponsoredTopSites'|preferenceValue
    """,
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

EXISTING_WINDOWS_USER = NimbusTargetingConfig(
    name="Existing Windows 7+ user",
    slug="existing_windows_user",
    description="Users on Windows 7+ with profiles older than 28 days",
    targeting=f"{PROFILE28DAYS} && os.isWindows && os.windowsVersion >= 6.1",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

EXISTING_WINDOWS_USER_NO_FX_ACCOUNT = NimbusTargetingConfig(
    name="Existing Windows 7+ user without Fx account",
    slug="existing_windows_user_no_fx_account",
    description="Windows 7+ users not logged into FxA with profiles older than 28 days",
    targeting=(
        f"{PROFILE28DAYS} "
        "&& os.isWindows "
        "&& os.windowsVersion >= 6.1"
        "&& !('services.sync.username'|preferenceIsUserSet)"
    ),
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

EXISTING_USER_UNSUPPORTED_WINDOWS_VERSION = NimbusTargetingConfig(
    name="Existing Windows <10 version user",
    slug="existing_user_usupported_windows_version",
    description="Users on Windows <10 with profiles older than 28 days",
    targeting=f"{PROFILE28DAYS} && os.isWindows && os.windowsVersion < 10",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

POST_FIRST_RUN_USER_UNSUPPORTED_WINDOWS_VERSION = NimbusTargetingConfig(
    name="Post first run Windows <10 version user",
    slug="post_first_run_user_unsupported_windows_version",
    description="Users on Windows <10 not on their first run of the application",
    targeting="!isFirstStartup && os.isWindows && os.windowsVersion < 10",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

TEST_STICKY_TARGETING = NimbusTargetingConfig(
    name="Test targeting",
    slug="test_targeting",
    description="Config for sticky targeting",
    targeting="'sticky.targeting.test.pref'|preferenceValue",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=[a.name for a in Application],
)

ANDROID_CORE_ACTIVE_USER = NimbusTargetingConfig(
    name="Core Active Users",
    slug="android_core_active_users",
    description="Users who have been active at least 21 out of the last 28 days",
    targeting=CORE_ACTIVE_USERS_TARGETING.format(event="events.app_opened"),
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.FENIX.name, Application.FOCUS_ANDROID.name),
)

IOS_CORE_ACTIVE_USER = NimbusTargetingConfig(
    name="Core Active Users",
    slug="ios_core_active_users",
    description="Users who have been active at least 21 out of the last 28 days",
    targeting=CORE_ACTIVE_USERS_TARGETING.format(event="app_cycle.foreground"),
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.IOS.name, Application.FOCUS_IOS.name),
)

ANDROID_RECENTLY_LOGGED_IN_USER = NimbusTargetingConfig(
    name="Recently Logged In Users",
    slug="android_recently_logged_in_users",
    description="Users who have completed a Sync login within the last 12 weeks",
    targeting=RECENTLY_LOGGED_IN_USERS_TARGETING.format(event="sync_auth.sign_in"),
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.FENIX.name, Application.FOCUS_ANDROID.name),
)

IOS_RECENTLY_LOGGED_IN_USER = NimbusTargetingConfig(
    name="Recently Logged In Users",
    slug="ios_recently_logged_in_users",
    description="Users who have completed a Sync login within the last 12 weeks",
    targeting=RECENTLY_LOGGED_IN_USERS_TARGETING.format(
        event="sync.login_completed_view"
    ),
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.IOS.name, Application.FOCUS_IOS.name),
)

HAS_GOOGLE_BING_DDG_AS_CURRENT_DEFAULT_SEARCH_ENGINE = NimbusTargetingConfig(
    name="Has Google, Bing, or DuckDuckGo as current default search engine",
    slug="has_google_bing_or_ddg_as_current_default_search_engine",
    description="Users with Google, Bing, or DuckDuckGo as current default engine",
    targeting=(
        "'google' in searchEngines.current ||"
        "searchEngines.current == 'bing' ||"
        "searchEngines.current == 'ddg'"
    ),
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

HAS_GOOGLE_AS_CURRENT_DEFAULT_SEARCH_ENGINE = NimbusTargetingConfig(
    name="Has Google as current default search engine",
    slug="has_google_as_current_default_search_engine",
    description="Users with Google as current default engine",
    targeting=("'google' in searchEngines.current"),
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

NEW_ANDROID_13_USERS = NimbusTargetingConfig(
    name="New Android 13 Users",
    slug="new_android_13_users",
    description="Users who have Android 13 and are on their first run of the application",
    targeting="(android_sdk_version|versionCompare('33') >= 0) && is_first_run",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=True,
    application_choice_names=(Application.FENIX.name,),
)

EXISTING_USER = NimbusTargetingConfig(
    name="Existing user",
    slug="existing_user",
    description="Users with profiles older than 28 days",
    targeting=f"{PROFILE28DAYS}",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

EXISTING_USER_HAS_DEFAULT_NEED_PIN = NimbusTargetingConfig(
    name="Existing user (has default, need pin)",
    slug="existing_user_has_default_need_pin",
    description="Users with profiles older than 28 days and w/ default need pin",
    targeting=f"{PROFILE28DAYS} && isDefaultBrowser && doesAppNeedPin",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

EXISTING_USER_NEED_DEFAULT_HAS_PIN = NimbusTargetingConfig(
    name="Existing user (need default, has pin)",
    slug="existing_user_need_default_has_pin",
    description="Users with profiles older than 28 days and need default w/ pin",
    targeting=f"{PROFILE28DAYS} && {NEED_DEFAULT} && {HAS_PIN}",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

EXISTING_USER_NEED_PIN = NimbusTargetingConfig(
    name="Existing user (need pin)",
    slug="existing_user_need_pin",
    description="Users with profiles older than 28 days who have not pinned",
    targeting=f"{PROFILE28DAYS} && doesAppNeedPin",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

EXISTING_USER_NEED_DEFAULT = NimbusTargetingConfig(
    name="Existing user (need default)",
    slug="existing_user_need_default",
    description="Users with profiles older than 28 days who have not set to default",
    targeting=f"{PROFILE28DAYS} && {NEED_DEFAULT}",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

NEW_USER_FIVE_BOOKMARKS = NimbusTargetingConfig(
    name="New user (5 bookmarks)",
    slug="new_user_5_bookmarks",
    description="Profile age less than 28 days, has 5 bookmarks",
    targeting=f"{PROFILELESSTHAN28DAYS} && totalBookmarksCount == 5",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

INFREQUENT_USER_OR_NEW_USER_FIVE_BOOKMARKS = NimbusTargetingConfig(
    name="Infrequent user or new user (5 bookmarks)",
    slug="infrequent_user_or_new_user_five_bookmarks",
    description="Infrequent users or new users with 5 bookmarks",
    targeting=(
        f"{INFREQUENT_USER_FIVE_BOOKMARKS.targeting}"
        " || "
        f"{NEW_USER_FIVE_BOOKMARKS.targeting}"
    ),
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

FIVE_BOOKMARKS = NimbusTargetingConfig(
    name="5 bookmarks",
    slug="5_bookmarks",
    description="Any user with exactly 5 bookmarks",
    targeting="totalBookmarksCount == 5",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

NOT_MAC = NimbusTargetingConfig(
    name="Not Mac Users",
    slug="not_mac_users",
    description="Clients not on mac",
    targeting="!os.isMac",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

EARLY_DAY_USER = NimbusTargetingConfig(
    name="Early day user (28 days or less)",
    slug="early_day_user",
    description="Users with profiles that are 28 days old or less",
    targeting="(currentDate|date - profileAgeCreated|date) / 86400000 <= 28",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

EARLY_DAY_USER_V2 = NimbusTargetingConfig(
    name="Early day user (less than 28 days)",
    slug="early_day_user_v2",
    description="Users with profiles that are less than 28 days old",
    targeting=f"{PROFILELESSTHAN28DAYS}",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

EARLY_DAY_USER_NEED_DEFAULT = NimbusTargetingConfig(
    name="Early day user (28 days or less) needs default",
    slug="early_day_user_need_default",
    description="Less than 28 day old profile age and has not set default",
    targeting=f"{EARLY_DAY_USER.targeting} && {NEED_DEFAULT}",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

EARLY_DAY_USER_NEED_DEFAULT_V2 = NimbusTargetingConfig(
    name="Early day user (less than 28 days) needs default",
    slug="early_day_user_need_default_v2",
    description="Users with profiles that are less than 28 days old and "
    "has not set default",
    targeting=f"{EARLY_DAY_USER_V2.targeting} && {NEED_DEFAULT}",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

EARLY_DAY_USER_NEED_PIN = NimbusTargetingConfig(
    name="Early day user (28 days or less) needs pin",
    slug="early_day_user_need_pin",
    description="Less than 28 day old profile age and has not pinned",
    targeting=f"{EARLY_DAY_USER.targeting} && doesAppNeedPin",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

EARLY_DAY_USER_NEED_PIN_V2 = NimbusTargetingConfig(
    name="Early day user (less than 28 days) needs pin",
    slug="early_day_user_need_pin_v2",
    description="Users with profiles that are less than 28 days old and has not pinned",
    targeting=f"{EARLY_DAY_USER_V2.targeting} && doesAppNeedPin",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

EARLY_DAY_USER_HAS_DEFAULT_NEED_PIN = NimbusTargetingConfig(
    name="Early day user (28 days or less) has default needs pin",
    slug="early_day_user_has_default_need_pin",
    description="Less than 28 day old profile age has set default and has not pinned",
    targeting=f"{EARLY_DAY_USER_NEED_PIN.targeting} && isDefaultBrowser",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

EARLY_DAY_USER_HAS_DEFAULT_NEED_PIN_V2 = NimbusTargetingConfig(
    name="Early day user (less than 28 days) has default needs pin",
    slug="early_day_user_has_default_need_pin_v2",
    description="Less than 28 day old profile age has set default and has not pinned",
    targeting=f"{EARLY_DAY_USER_NEED_PIN_V2.targeting} && isDefaultBrowser",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

TRR_MODE_ZERO = NimbusTargetingConfig(
    name="network.trr.mode = 0",
    slug="network_trr_mode_0",
    description="Users who are not using a trusted resolver",
    targeting="'network.trr.mode'|preferenceValue == 0",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

NOT_IMPORT_INFREQUENT_ROLLOUT = NimbusTargetingConfig(
    name="Not in Import Infrequent Rollouts",
    slug="not_import_infrequent_rollout",
    description="Exclude users in the import infrequent rollouts",
    targeting=(
        "(activeRollouts intersect ["
        "   'import-infrequent-rollout-make-yourself-at-home',"
        "   'updated-import-infrequent-rollout-make-yourself-at-home-copy'"
        "])|length == 0"
    ),
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

SET_DEFAULT_PDF_EXPERIMENT_ENROLLEES = NimbusTargetingConfig(
    name="Set Default PDF Experiment enrollees",
    slug="set_default_pdf_experiment_enrollees",
    description="Users who are enrolled in the set default pdf experiment",
    targeting=(
        "'existing-users-set-default-pdf-handler' in activeExperiments"
        " || 'existing-users-set-default-pdf-handler' in activeRollouts"
    ),
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

TEST_MOBILE_FIRST_RUN_TARGETING_CRITERIA_IOS = NimbusTargetingConfig(
    name="TEST first run targeting criteria",
    slug="test_mobile_first_run_targeting_criteria",
    description=(
        "Users for whom this is their first run of the application, and the number of "
        "days since install is less than 7. Additionally, though this targets first run "
        "users this advanced targeting option does not require first run to be enabled."
    ),
    targeting="(isFirstRun == 'true' || is_first_run == true) && days_since_install < 7",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(
        Application.FENIX.name,
        Application.IOS.name,
    ),
)

CORE_USER_FULLY_ACTIVE = NimbusTargetingConfig(
    name="Core user (Active Every Day)",
    slug="core_user_active_every_day",
    description="Active every day in the past 28 days",
    targeting=f"{PROFILE28DAYS} && userMonthlyActivity|length >= 28",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

EARLY_DAY_USER_HASNT_CHANGED_BOOKMARKS_TOOLBAR = NimbusTargetingConfig(
    name="Early Day User (Hasn't changed bookmarks toolbar behavior)",
    slug="early_day_user_bookmarks_toolbar_unchanged",
    description=(
        "Users with profiles < 28 days old who have not edited the default bookmarks "
        "toolbar behavior"
    ),
    targeting=(
        f"{PROFILELESSTHAN28DAYS} &&"
        " !('browser.toolbars.bookmarks.visibility'|preferenceIsUserSet)"
    ),
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

ANDROID_8_OR_HIGHER_USERS = NimbusTargetingConfig(
    name="Android Version 8.0+ Users",
    slug="android_8_or_higher_users",
    description="Users on Android version 8.0 or higher",
    targeting="(android_sdk_version|versionCompare('26') >= 0)",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.FENIX.name,),
)

WINDOWS_10_PLUS = NimbusTargetingConfig(
    name="Windows 10+",
    slug="windows_10_plus",
    description="Windows users on version 10 or higher",
    targeting="(os.isWindows && os.windowsVersion >= 10)",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

IOS_EARLY_DAY_USERS_IPHONE_ONLY = NimbusTargetingConfig(
    name="Early day users iPhone only",
    slug="ios_early_day_users_iphone_only",
    description="Targeting users under 28 since install with iPhones",
    targeting="is_phone && days_since_install < 28",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.IOS.name,),
)

IOS_LATER_DAY_USERS_IPHONE_ONLY = NimbusTargetingConfig(
    name="Later day users iPhone only",
    slug="ios_later_day_users_iphone_only",
    description="Targeting users equal to or greater than 28 since install with iPhones",
    targeting="is_phone && days_since_install >= 28",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.IOS.name,),
)

ANDROID_EARLY_DAY_USERS_ONLY = NimbusTargetingConfig(
    name="Early day users only",
    slug="android_early_day_users_only",
    description="Targeting users under 28 since install",
    targeting="days_since_install < 28",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.FENIX.name,),
)

ANDROID_LATER_DAY_USERS_ONLY = NimbusTargetingConfig(
    name="Later day users only",
    slug="android_later_day_users_only",
    description="Targeting users equal to or greater than 28 since install",
    targeting="days_since_install >= 28",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.FENIX.name,),
)

IOS_REVIEW_CHECKER_ENABLED_USERS_ONLY = NimbusTargetingConfig(
    name="Review checker enabled users only",
    slug="ios_review_checker_enabled_users_only",
    description="Targeting users who have opted in review checker",
    targeting="is_review_checker_enabled",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.IOS.name,),
)

ANDROID_REVIEW_CHECKER_ENABLED_USERS_ONLY = NimbusTargetingConfig(
    name="Review checker enabled users only",
    slug="android_review_checker_enabled_users_only",
    description="Targeting users who have opted in review checker",
    targeting="is_review_checker_enabled",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.FENIX.name,),
)

DEFAULT_PDF_IS_DIFFERENT_BROWSER = NimbusTargetingConfig(
    name="Default PDF handler is a different browser",
    slug="default_pdf_is_different_browser",
    description=(
        "Targeting users that have their default PDF handler set to a browser other "
        "than the current Firefox installation"
    ),
    targeting="!isDefaultHandler['pdf'] && defaultPDFHandler['knownBrowser']",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

SHOPPING_OPTED_IN = NimbusTargetingConfig(
    name="Users opted in to shopping",
    slug="shopping_opted_in",
    description="Users who have opted in to the shopping experience",
    targeting="'browser.shopping.experience2023.optedIn'|preferenceValue == 1",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

SHOPPING_ONBOARDING_SHOWN = NimbusTargetingConfig(
    name="Shopping onboarding shown",
    slug="shopping_onboarding_shown",
    description=(
        "Users that have seen the shopping experiment onboarding at least once. "
        "Used as a proxy to target shopping users for a feature continuity rollout, "
        "ensuring the shopping feature stays active across different experiments."
    ),
    targeting="'browser.shopping.experience2023.autoActivateCount'|preferenceValue >= 1",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

IS_64BIT_WITH_8GB_RAM = NimbusTargetingConfig(
    name="64bit Firefox build running on a computer with at least 8GB of RAM",
    slug="is_64bit_build_and_8gb_ram",
    description="Target 64bit builds running on computers with at least 8GB of RAM.",
    targeting="archBits == 64 && memoryMB >= 8000",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

VIEWPOINT_SURVEY_DESKTOP = NimbusTargetingConfig(
    name="User Research Viewpoint Survey (Rolling Enrollment)",
    slug="viewpoint_survey_desktop",
    description=(
        "Rolling enrollment based on date. Only for use by User Research Viewpoint "
        "surveys."
    ),
    targeting=(
        "['rolling-viewpoint', userId]|"
        "bucketSample(19468 + currentDate / (24 * 60 * 60 * 1000) + 1, 7, 7000)"
    ),
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)


class TargetingConstants:
    TARGETING_VERSION = "version|versionCompare('{version}') >= 0"
    TARGETING_CHANNEL = 'browserSettings.update.channel == "{channel}"'

    TARGETING_CONFIGS = {
        targeting.slug: targeting for targeting in NimbusTargetingConfig.targeting_configs
    }

    TargetingConfig = models.TextChoices(
        "TargetingConfig",
        [
            (targeting.slug.upper(), targeting.slug)
            for targeting in NimbusTargetingConfig.targeting_configs
        ],
    )

    TARGETING_APPLICATION_SUPPORTED_VERSION = {
        Application.FENIX: NimbusConstants.Version.FIREFOX_98,
        Application.FOCUS_ANDROID: NimbusConstants.Version.FIREFOX_98,
        Application.IOS: NimbusConstants.Version.FIREFOX_98,
        Application.FOCUS_IOS: NimbusConstants.Version.FIREFOX_97,
    }
