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
WIN22H2 = "os.windowsBuildNumber >= 19045"
CORE_ACTIVE_USERS_TARGETING = "'{event}'|eventCountNonZero('Days', 28, 0) >= 21"
RECENTLY_LOGGED_IN_USERS_TARGETING = "'{event}'|eventCountNonZero('Weeks', 12, 0) >= 1"

HAS_TOU_ACCEPTED_DATE = "('termsofuse.acceptedDate'|preferenceValue != '0')"
# Change stringified accepted timestamp to a number
TOU_ACCEPTED_DATE = "('termsofuse.acceptedDate'|preferenceValue * 1)"

ACCEPTED_TOU_V4 = "'termsofuse.acceptedVersion'|preferenceValue == 4"

ACCEPTED_TOU_V4_OR_HIGHER = "'termsofuse.acceptedVersion'|preferenceValue >= 4"

# From this point forward, TOU accepted version will remain at 4 and acceptance
# date will be used to determine what variations of the TOU/privacy notice was
# accepted.

# 23:59 UTC on Dec 9, 2025 when an updated version of the privacy
# notice was published.
DEC_9_2025 = 1765324740000
# Privacy Notification Published date of 12:00 PM UTC on Dec 15, 2025
DEC_15_2025 = 1765800000000
DEC_17_2025 = 1765972800000

TOU_NOTIFICATION_BYPASS_ENABLED = "'termsofuse.bypassNotification'|preferenceValue"

# The following indicate whether the user has changed prefs suggesting
# they prefer not to see ads or ad-like features
NEW_TAB_NOT_DEFAULT = """
(
    !newtabSettings.isDefault
    ||
    !'browser.newtabpage.enabled'|preferenceValue
)
"""
HOMEPAGE_NOT_DEFAULT = "!homePageSettings.isDefault"
TOPSITES_OR_SPONSORED_TOPSITES_DISABLED = """
(
    (
        'browser.newtabpage.activity-stream.feeds.system.topsites'|preferenceValue
        &&
        !'browser.newtabpage.activity-stream.feeds.topsites'|preferenceValue
    )
    ||
    !'browser.newtabpage.activity-stream.showSponsoredTopSites'|preferenceValue
)
"""
RECOMMENDED_OR_SPONSORED_STORIES_DISABLED = """
(
    (
        'browser.newtabpage.activity-stream.feeds.system.topstories'|preferenceValue
        &&
        !'browser.newtabpage.activity-stream.feeds.section.topstories'|preferenceValue
    )
    ||
    (
        'browser.newtabpage.activity-stream.system.showSponsored'|preferenceValue
        &&
        !'browser.newtabpage.activity-stream.showSponsored'|preferenceValue
    )
)
"""
SPONSORED_SEARCH_SUGGESTIONS_DISABLED = (
    "'browser.urlbar.suggest.quicksuggest.sponsored'|preferenceIsUserSet "
    "&& !'browser.urlbar.suggest.quicksuggest.sponsored'|preferenceValue"
)
ADS_DISABLED = f"""
(
    {NEW_TAB_NOT_DEFAULT}
    ||
    {HOMEPAGE_NOT_DEFAULT}
    ||
    {TOPSITES_OR_SPONSORED_TOPSITES_DISABLED}
    ||
    {RECOMMENDED_OR_SPONSORED_STORIES_DISABLED}
    ||
    {SPONSORED_SEARCH_SUGGESTIONS_DISABLED}
)
"""
# Most sponsored content is off by default in Brazil and Mexico, as of
# June 26, 2025.
ADS_DISABLED_BR_MX_2025_06_26 = TOPSITES_OR_SPONSORED_TOPSITES_DISABLED

# User has at least one non-default privacy setting:
#   ETP strict (see https://searchfox.org/firefox-main/source/browser/base/content/test/protectionsUI/browser_protectionsUI.js#193-200)
#   Global Privacy Control (see https://searchfox.org/firefox-main/source/modules/libpref/init/StaticPrefList.yaml#16139-16145)
#   Enable DNS over HTTPS - Max Protection (see https://firefox-source-docs.mozilla.org/networking/dns/dns-over-https-trr.html#implementation)
#   Enable HTTPS-Only Mode in all windows (see https://searchfox.org/firefox-main/source/modules/libpref/init/StaticPrefList.yaml#4430-4432)

HAS_PRIVACY_SETTING = """
(
    (
        ('browser.contentblocking.category'|preferenceValue) == "strict"
        ||
        ('browser.contentblocking.category'|preferenceValue) == "custom"
    )
    ||
    ('privacy.globalprivacycontrol.enabled'|preferenceValue)
    ||
    (
        ('network.trr.mode'|preferenceValue) == 3
        ||
        ('doh-rollout.mode'|preferenceValue) == 3
    )
    ||
    ('dom.security.https_only_mode'|preferenceValue)
)
"""
# User has uBlock, Adblocker Ultimate, Adblock Plus, or Ghostery extensions
HAS_AD_BLOCKER = """
(
    !!addonsInfo.addons
    &&
    (
        !!addonsInfo.addons["uBlock0@raymondhill.net"]
        ||
        !!addonsInfo.addons["firefox@ghostery.com"]
        ||
        !!addonsInfo.addons["adblockultimate@adblockultimate.net"]
        ||
        !!addonsInfo.addons["{d10d0bf8-f5b5-c8b4-a8b2-2b9879e08c5d}"]
        ||
        !!addonsInfo.addons["jid1-NIfFY2CA8fy1tg@jetpack"]
    )
)
"""

TOU_EXPERIENCE_TOTAL = f"""
    (
        ({ADS_DISABLED} && 1 || 0)
        +
        ({HAS_PRIVACY_SETTING} && 1 || 0)
        +
        ({HAS_AD_BLOCKER} && 1 || 0)
    )
"""

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

HB_LESS_THAN_2_DAY_PROFILE = NimbusTargetingConfig(
    name="Heartbeat less than 2 day old profile",
    slug="hb_2_day_profile",
    description="Profile between 10 minutes and 2 days old (used for HB surveys)",
    targeting="({older_than_10_min} && {newer_than_2_days})".format(
        older_than_10_min="(currentDate|date - profileAgeCreated|date) / 60000 > 10",
        newer_than_2_days="(currentDate|date - profileAgeCreated|date) / 3600000 <= 48",
    ),
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

MSIX_FIRST_RUN = NimbusTargetingConfig(
    name="First start-up users with MSIX Firefox",
    slug="msix_first_run",
    description=("First start-up users (e.g. for about:welcome) with MSIX Firefox"),
    targeting="(isFirstStartup && os.isWindows && os.windowsVersion >= 10 && isMSIX)",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=True,
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
        "First start-up users (e.g. for about:welcome) who download Firefox from Chrome"
    ),
    targeting=f"{FIRST_RUN.targeting} && attributionData.ua == 'chrome'",
    desktop_telemetry=(
        f"{FIRST_RUN.desktop_telemetry} "
        "AND environment.settings.attribution.ua = 'chrome'"
    ),
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
        f"{FIRST_RUN.desktop_telemetry} "
        "AND environment.system.os.windows_build_number >= 18362"
    ),
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
        f"{FIRST_RUN.desktop_telemetry} "
        "AND environment.system.os.windows_build_number >= 18362 "
        f"AND {NEW_PROFILE}"
    ),
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
        f"{FIRST_RUN.desktop_telemetry} "
        "AND environment.system.os.windows_build_number >= 22621 "
        f"AND {NEW_PROFILE} AND !isDefaultBrowser AND doesAppNeedPin"
    ),
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
        f"{FIRST_RUN.desktop_telemetry} "
        "AND environment.system.os.windows_build_number >= 18362 AND "
        f"!isDefaultBrowser AND {NEW_PROFILE}"
    ),
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
        f"{FIRST_RUN_NEW_PROFILE_NEED_DEFAULT_WINDOWS_1903.targeting} "
        "&& !userPrefersReducedMotion"
    ),
    desktop_telemetry=(
        f"{FIRST_RUN_NEW_PROFILE_NEED_DEFAULT_WINDOWS_1903.desktop_telemetry} "
        "AND !userPrefersReducedMotion"
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
        f"{FIRST_RUN_NEW_PROFILE_NEED_DEFAULT_WINDOWS_1903.desktop_telemetry} "
        "AND doesAppNeedPin"
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
        f"{FIRST_RUN_NEW_PROFILE_NEED_DEFAULT_WINDOWS_1903.desktop_telemetry} "
        f"AND {HAS_PIN}"
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
        f"{FIRST_RUN_NEW_PROFILE_NEED_DEFAULT_WINDOWS_1903.targeting} "
        f"&& {ATTRIBUTION_MEDIUM_PAIDSEARCH.targeting}"
    ),
    desktop_telemetry=(
        f"{FIRST_RUN_NEW_PROFILE_NEED_DEFAULT_WINDOWS_1903.desktop_telemetry} "
        f"AND {ATTRIBUTION_MEDIUM_PAIDSEARCH.targeting}"
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
    desktop_telemetry=(
        f"{FIRST_RUN.desktop_telemetry} AND {WINDOWS_WITH_USERCHOICE.desktop_telemetry}"
    ),
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

WINDOWS_WITH_USERCHOICE_22H2 = NimbusTargetingConfig(
    name="Users on Windows version 22H2 with UserChoice support",
    slug="windows_userchoice_22h2",
    description=("Windows 22H2 with UserChoice support (version 22H2+/build ID 19045+)"),
    targeting=f"{WIN22H2}",
    desktop_telemetry="",
    sticky_required=False,
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
    name="New Users on Mobile (sticky)",
    slug="mobile_new_users",
    description=("New users on mobile who installed the app less than a week ago"),
    targeting="days_since_install < 7",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(
        Application.FENIX.name,
        Application.IOS.name,
    ),
)

MOBILE_NEW_USER_UNSTICKY = NimbusTargetingConfig(
    name="New Users on Mobile (not sticky)",
    slug="mobile_new_users_not_sticky",
    description=(
        "New users on mobile who installed the app less than a week ago "
        "and will be unenrolled after 7"
    ),
    targeting=MOBILE_NEW_USER.targeting,
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(
        Application.FENIX.name,
        Application.IOS.name,
    ),
)

MOBILE_EXISTING_USERS_OVER_7_DAYS = NimbusTargetingConfig(
    name="Existing mobile users with 7 or more days since install (not sticky)",
    slug="mobile_existing_users_over_7_days_not_sticky",
    description=("Existing mobile users who installed the app 7 or more days ago"),
    targeting="days_since_install >= 7",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(
        Application.FENIX.name,
        Application.IOS.name,
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

MOBILE_14_DAY_USER = NimbusTargetingConfig(
    name="Users who installed the app in the last 14 days",
    slug="mobile_14_day_users",
    description=("New users on mobile who installed the app in the last 2 weeks"),
    targeting="days_since_install < 15",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.FENIX.name,),
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

URLBAR_FIREFOX_SUGGEST_DATA_COLLECTION_ENABLED_NOT_STICKY = NimbusTargetingConfig(
    name="Urlbar (Firefox Suggest) - Data Collection Enabled (not sticky)",
    slug="urlbar_firefox_suggest_data_collection_enabled_not_sticky",
    description="Users with Firefox Suggest data collection enabled and not sticky",
    targeting="'browser.urlbar.quicksuggest.dataCollection.enabled'|preferenceValue",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

URLBAR_FIREFOX_SUGGEST_TOU_ONLINE = NimbusTargetingConfig(
    name="Urlbar (Firefox Suggest) - Accepted ToU, online enabled",
    slug="urlbar_firefox_suggest_tou_online",
    description=(
        "User matches all of the following: "
        "(1) accepted ToU on or after Dec 15, 2025, "
        "(2) online Firefox Suggest enabled"
    ),
    targeting=f"""
    (
        {HAS_TOU_ACCEPTED_DATE}
        &&
        ({TOU_ACCEPTED_DATE} >= {DEC_15_2025})
        &&
        'browser.urlbar.quicksuggest.online.enabled'|preferenceValue
    )
    """,
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

URLBAR_FIREFOX_SUGGEST_TOU_ONLINE_SPONSORED = NimbusTargetingConfig(
    name="Urlbar (Firefox Suggest) - Accepted ToU, online enabled, sponsored enabled",
    slug="urlbar_firefox_suggest_tou_online_sponsored",
    description=(
        "User matches all of the following: "
        "(1) accepted TOU on or after Dec 15, 2025, "
        "(2) online Firefox Suggest enabled, "
        "(3) sponsored suggestions enabled - "
        "IMPORTANT! You must restrict 'Locales' to one or more Firefox Suggest "
        "locales when using this!"
    ),
    targeting=f"""
    (
        {HAS_TOU_ACCEPTED_DATE}
        &&
        ({TOU_ACCEPTED_DATE} >= {DEC_15_2025})
        &&
        'browser.urlbar.quicksuggest.online.enabled'|preferenceValue
        && (
            !('browser.urlbar.suggest.quicksuggest.sponsored'|preferenceIsUserSet) ||
            'browser.urlbar.suggest.quicksuggest.sponsored'|preferenceValue
        )
    )
    """,
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

LINUX_ONLY = NimbusTargetingConfig(
    name="Linux users only",
    slug="linux_only",
    description="All users with Linux",
    targeting="os.isLinux",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

MAC_LINUX_ONLY = NimbusTargetingConfig(
    name="Mac and Linux users only",
    slug="mac_linux_only",
    description="All users with Mac or Linux",
    targeting="(os.isLinux || os.isMac)",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

MAC_WINDOWS_ONLY = NimbusTargetingConfig(
    name="Mac and Windows users only",
    slug="mac_windows_only",
    description="All users with Mac or Windows",
    targeting="(os.isWindows || os.isMac)",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

MAC_WINDOWS_11_ONLY = NimbusTargetingConfig(
    name="Mac and Windows 11+ users only",
    slug="mac_windows_11_only",
    description="All users with Mac or Windows 11+",
    targeting="((os.isWindows && os.windowsBuildNumber >= 22000) || os.isMac)",
    desktop_telemetry="",
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

NO_ENTERPRISE_MAC_WINDOWS_ONLY = NimbusTargetingConfig(
    name="No enterprise users (Mac, Windows only)",
    slug="no_enterprise_users_mac_windows_only",
    description="Exclude users with active enterpries policies on Mac and Windows only",
    targeting=f"({NO_ENTERPRISE.targeting}) && ({MAC_WINDOWS_ONLY.targeting})",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

NO_ENTERPRISE_MAC_WINDOWS_11_ONLY = NimbusTargetingConfig(
    name="No enterprise users (Mac, Windows 11+ only)",
    slug="no_enterprise_users_mac_windows_11_only",
    description=(
        "Exclude users with active enterpries policies on Mac and Windows 11+ only"
    ),
    targeting=f"({NO_ENTERPRISE.targeting}) && ({MAC_WINDOWS_11_ONLY.targeting})",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

NO_ENTERPRISE_MAC_LINUX_WINDOWS_11_ONLY = NimbusTargetingConfig(
    name="No enterprise users (Mac, Linux or Windows 11+ only)",
    slug="no_enterprise_users_mac_linux_windows_11_only",
    description=(
        "Exclude users with active enterpries policies on Mac, Linux, or Windows 11+"
    ),
    targeting=(
        f"({NO_ENTERPRISE.targeting}) && "
        "((os.isWindows && os.windowsBuildNumber >= 22000) || os.isMac || os.isLinux)"
    ),
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

WIN10_NOT_WIN11 = NimbusTargetingConfig(
    name="Windows 10 users but not Windows 11 users",
    slug="win10_not_win11",
    description="Windows 10 users but not Windows 11 users (Windows 10 build < 22000)",
    targeting="os.isWindows && os.windowsVersion >= 10 && os.windowsBuildNumber < 22000",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

WIN10_VPN_PROMOTION_ELIGIBLE = NimbusTargetingConfig(
    name="Windows 10 users eligible for VPN promotion",
    slug="win10_vpn_promotion_eligible",
    description=(
        "Windows 10 users who are signed out, at least 7 days old, "
        "no enterprise, default newtab, no adblock"
    ),
    targeting=(
        "os.isWindows && os.windowsVersion >= 10 && "
        "os.windowsBuildNumber < 22000 && "
        "isFxAEnabled && !isFxASignedIn && "
        f"{NO_ENTERPRISE.targeting} && "
        "newtabSettings.isDefault && "
        f"{PROFILEMORETHAN7DAYS} && "
        "!(['uBlock0@raymondhill.net','{d10d0bf8-f5b5-c8b4-a8b2-2b9879e08c5d}',"
        "'adblockultimate@adblockultimate.net','jid1-NIfFY2CA8fy1tg@jetpack',"
        "'adguardadblocker@adguard.com','firefox@ghostery.com'] "
        "intersect addonsInfo.addons|keys)|length"
    ),
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

WIN10_EOS_SYNC_ELIGIBLE = NimbusTargetingConfig(
    name="Windows 10 users eligible for Windows 10 EoS Sync promotion",
    slug="win10_eos_sync_promotion_eligible",
    description=(
        "Windows 10 users who are signed out, have FxA enabled, are at least 7 "
        "days old, without enterprise policies"
    ),
    targeting=(
        "os.isWindows && os.windowsVersion >= 10 && "
        "os.windowsBuildNumber < 22000 && "
        "isFxAEnabled && !isFxASignedIn && "
        f"{NO_ENTERPRISE.targeting} && "
        f"{PROFILEMORETHAN7DAYS}"
    ),
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

WIN10_EOS_SYNC_TOAST_ELIGIBLE = NimbusTargetingConfig(
    name="Users in the Windows 10 EOS Sync treatment branch",
    slug="win10_eos_sync_toast_eligible",
    description="Users in the Windows 10 EOS Sync treatment branch",
    targeting=(
        "isBackgroundTaskMode "
        "&& ((defaultProfile.enrollmentsMap['optin-windows-10-eos-sync-messaging'] "
        "== 'treatment-a')"
        " || (defaultProfile.enrollmentsMap['windows-10-eos-sync-messaging'] "
        "== 'treatment-a'))"
    ),
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

WIN10_EOS_SYNC_TOAST_ROLLOUT_ELIGIBLE = NimbusTargetingConfig(
    name="Users in the Windows 10 EOS Sync rollout",
    slug="win10_eos_sync_toast_rollout_eligible",
    description="Users in the Windows 10 EOS Sync rollout",
    targeting=(
        "isBackgroundTaskMode && (("
        "defaultProfile.enrollmentsMap['optin-windows-10-eos-sync-messaging-rollout-1'] "
        "== 'treatment-a')"
        " || (defaultProfile.enrollmentsMap['windows-10-eos-sync-messaging-rollout-1'] "
        "== 'treatment-a'))"
    ),
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

WIN10_EOS_REMINDER_ELIGIBLE = NimbusTargetingConfig(
    name="Windows 10 users eligible for Windows 10 EoS Reminder messages",
    slug="win10_eos_reminder_messages_eligible",
    description=(
        "Windows 10 users who have FxA enabled, are at least 7 "
        "days old, without enterprise policies"
    ),
    targeting=(
        "os.isWindows && os.windowsVersion >= 10 && "
        "os.windowsBuildNumber < 22000 && "
        "isFxAEnabled && "
        f"{NO_ENTERPRISE.targeting} && "
        f"{PROFILEMORETHAN7DAYS}"
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

REVIEW_CHECKER_SIDEBAR_RECOMMENDATION_CFR_ONLY = NimbusTargetingConfig(
    name="Review Checker Sidebar Recommendation (CFR Only)",
    slug="review_chercker_sidebar_reccomendation_cfr_only",
    description="Only include users who have not opted out of recommendations",
    targeting="('browser.newtabpage.activity-stream.asrouter.userprefs.cfr.features'|preferenceValue)",
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

WINDOWS_10_BACKGROUND_TASK_NOTIFICATION_ONE_YEAR = NimbusTargetingConfig(
    name="Lapsed users background task notification for up to a year",
    slug="background_task_notification_one_year",
    description=(
        "Windows 10+ users with 0 days of activity in the past 28 days "
        "who were last active 28 to 365 days ago "
        "who are running a background task"
    ),
    targeting=(
        "(os.isWindows && os.windowsVersion >= 10) && !isMSIX"
        "&& ((currentDate|date - defaultProfile.currentDate|date) / 86400000 >= 28) "
        "&& ((currentDate|date - defaultProfile.currentDate|date) / 86400000 <= 365) "
        "&& isBackgroundTaskMode"
    ),
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

WINDOWS_10_BACKGROUND_TASK_NOTIFICATION_TASKBAR_TABS_ELIGIBLE = NimbusTargetingConfig(
    name=(
        "Windows 10+ users with background task notification, "
        "eligible for the taskbar tabs message"
    ),
    slug="windows_10_background_task_notification_taskbar_tabs",
    description=(
        "New and Infrequent Windows 10+ users (no MSIX) "
        "with Firefox running a background task"
    ),
    targeting=(
        "(os.isWindows && os.windowsVersion >= 10) && !isMSIX"
        "&& defaultProfile.userMonthlyActivity|length <= 14 "
        "&& isBackgroundTaskMode"
    ),
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

WINDOWS_10_PLUS_WITH_BACKGROUND_TASK_NOTIFICATION = NimbusTargetingConfig(
    name="Windows 10+ users with background task notification",
    slug="windows_10_background_task_notification",
    description="Windows 10+ users with Firefox running a background task",
    targeting="isBackgroundTaskMode && (os.isWindows && os.windowsVersion >= 10)",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

WINDOWS_10_PLUS_BACKGROUND_TASK_NOTIFICATION_1HR_INACTIVITY = NimbusTargetingConfig(
    name="Windows 10+ users with background task notification and 1hr+ of inactivity",
    slug="windows10_background_task_notification_1hr_inactivity",
    description=(
        "Windows 10+ users with 1hr+ of inactivity in the past day "
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
            ((currentDate|date - defaultProfile.currentDate|date) / 3600000 >= 1)
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

WHATS_NEW_NOTIFICATION_SIDEBAR_VERTICAL_TABS_ROLLOUT_V2 = NimbusTargetingConfig(
    name=(
        "Windows 10+ users with 1hr+ of inactivity in the past day "
        "who are running a background task and are "
        "not enrolled in treatment-a of WNN sidebar/vertical tabs experiment"
    ),
    slug="whats_new_notification_sidebar_vertical_tabs_rollout_v2",
    description=(
        "Windows 10+ users with 1hr+ of inactivity in the past day "
        "who are running a background task and are "
        "not enrolled in treatment-a of WNN sidebar/vertical tabs experiment"
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
            ((currentDate|date - defaultProfile.currentDate|date) / 3600000 >= 1)
        )
        &&
        isBackgroundTaskMode
        &&
        ((defaultProfile.enrollmentsMap['whats-new-notification-sidebarvertical-tabs']
        == 'treatment-a') == false)
    )
    """,
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

WHATS_NEW_NOTIFICATION_SIDEBAR_VERTICAL_TABS_ROLLOUT_V3 = NimbusTargetingConfig(
    name=(
        "Windows 10+ users with 1hr+ of inactivity in the past day "
        "who are running a background task and have CFR pref enabled "
        "and excludes users with enterprise policies, "
        "enrolled in treatment-a of WNN sidebar/vertical tabs experiment, "
        "and enrolled in the previous rollout of WNN sidebar/vertical tabs "
    ),
    slug="whats_new_notification_sidebar_vertical_tabs_rollout_v3",
    description=(
        "Windows 10+ users with 1hr+ of inactivity in the past day "
        "who are running a background task and have CFR pref enabled "
        "and not enrolled in treatment-a of WNN sidebar/vertical tabs "
        "experiment and rollout"
    ),
    targeting="""
    (
        (os.isWindows && (os.windowsVersion >= 10))
        &&
        ((currentDate|date - defaultProfile.currentDate|date) / 3600000 >= 1)
        &&
        isBackgroundTaskMode
        &&
        defaultProfile.enrollmentsMap['whats-new-notification-sidebarvertical-tabs']
        != 'treatment-a'
        &&
        defaultProfile.enrollmentsMap['whats-new-notification-sidebarvertical-tabs-rollout-v2']
        != 'treatment-a'
        &&
        defaultProfile.userPrefs.cfrFeatures
        &&
        !defaultProfile.hasActiveEnterprisePolicies
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

ANDROID_CORE_ACTIVE_USER = NimbusTargetingConfig(
    name="Core Active Users",
    slug="android_core_active_users",
    description="Users who have been active at least 21 out of the last 28 days",
    targeting=CORE_ACTIVE_USERS_TARGETING.format(event="events.app_opened"),
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.FENIX.name,),
)

IOS_CORE_ACTIVE_USER = NimbusTargetingConfig(
    name="Core Active Users",
    slug="ios_core_active_users",
    description="Users who have been active at least 21 out of the last 28 days",
    targeting=CORE_ACTIVE_USERS_TARGETING.format(event="app_cycle.foreground"),
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.IOS.name,),
)

IOS_EXISTING_USERS = NimbusTargetingConfig(
    name="ios existing users",
    slug="ios existing users",
    description="Targeting users equal to or greater than 28 since install",
    targeting="days_since_install >= 28",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.IOS.name,),
)

ANDROID_RECENTLY_LOGGED_IN_USER = NimbusTargetingConfig(
    name="Recently Logged In Users",
    slug="android_recently_logged_in_users",
    description="Users who have completed a Sync login within the last 12 weeks",
    targeting=RECENTLY_LOGGED_IN_USERS_TARGETING.format(event="sync_auth.sign_in"),
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.FENIX.name,),
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
    application_choice_names=(Application.IOS.name,),
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

HAS_GOOGLE_AS_CURRENT_DEFAULT_SEARCH_ENGINE_NO_STICKY = NimbusTargetingConfig(
    name="Has Google as current default search engine no sticky",
    slug="has_google_as_current_default_search_engine_no_sticky",
    description="Users with Google as current default engine no sticky enrollment",
    targeting=("'google' in searchEngines.current"),
    desktop_telemetry="",
    sticky_required=False,
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

EXISTING_USER_NEED_DEFAULT_WIN1903 = NimbusTargetingConfig(
    name="Existing user (need default, Windows 1903+)",
    slug="existing_user_need_default_windows_1903",
    description=(
        "Users with profiles older than 28 days "
        "who have not set to default, on Windows 1903+"
    ),
    targeting=f"{PROFILE28DAYS} && {NEED_DEFAULT} && {WIN1903}",
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

USER_NOT_SET_TO_DEFAULT = NimbusTargetingConfig(
    name="User not set to default",
    slug="user_not_set_to_default",
    description="Users who have not set to default",
    targeting=f"{NEED_DEFAULT}",
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

ANDROID_10_OR_HIGHER_USERS = NimbusTargetingConfig(
    name="Android Version 10+ Users",
    slug="android_10_or_higher_users",
    description="Users on Android version 10 or higher",
    targeting="(android_sdk_version|versionCompare('29') >= 0)",
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


WINDOWS_10_NOMSIX = NimbusTargetingConfig(
    name="Windows 10+ without msix",
    slug="windows_10_plus_nomsix",
    description="Windows users on version 10 or higher, but no MSIX intallations",
    targeting="(os.isWindows && os.windowsVersion >= 10 && !isMSIX)",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

WINDOWS_10_MSIX_ONLY = NimbusTargetingConfig(
    name="Windows 10+ msix only",
    slug="windows_10_plus_msix_only",
    description="Windows users on version 10 or higher using msix installation",
    targeting="(os.isWindows && os.windowsVersion >= 10 && isMSIX)",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

IOS_DEFAULT_BROWSER_FIRST_RUN_USER = NimbusTargetingConfig(
    name="Default Browser & First Run FXiOS Users",
    slug="ios_default_browser_user",
    description="Users that already have FXiOS set as the default browser",
    targeting="is_default_browser == true && is_first_run",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=True,
    application_choice_names=(Application.IOS.name,),
)

IOS_BOTTOM_TOOLBAR_USER = NimbusTargetingConfig(
    name="Existing Bottom Toolbar Users",
    slug="ios_bottom_toolbar_user",
    description="Users that already have a preference set to bottom for the toolbar",
    targeting="is_bottom_toolbar_user == true",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.IOS.name,),
)

IOS_TIPS_NOTIFICATIONS_ENABLED_USER = NimbusTargetingConfig(
    name="Users With Tips Notifications Enabled",
    slug="ios_tips_notifications_enabled_user",
    description="Users that already have enabled notifications for tips and features",
    targeting="has_enabled_tips_notifications == true",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.IOS.name,),
)

IOS_ACCEPTED_TERMS_OF_USE_USER = NimbusTargetingConfig(
    name="Users Who Accepted Terms of Use",
    slug="ios_accepted_terms_of_use_user",
    description="Users that have already accepted the Terms of Use",
    targeting="has_accepted_terms_of_use == true",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.IOS.name,),
)

IOS_NOT_ACCEPTED_TERMS_OF_USE_USER = NimbusTargetingConfig(
    name="Users Who Have Not Accepted Terms of Use",
    slug="ios_not_accepted_terms_of_use_user",
    description="Users that have not accepted the Terms of Use",
    targeting="has_accepted_terms_of_use == false",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.IOS.name,),
)

IOS_EXISTING_USERS_NOT_ACCEPTED_TERMS_OF_USE = NimbusTargetingConfig(
    name="Existing Users Who Have Not Accepted Terms of Use",
    slug="ios_existing_users_not_accepted_terms_of_use",
    description="Existing users for 28+ days who have not accepted Terms of Use",
    targeting="has_accepted_terms_of_use == false && days_since_install >= 28",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.IOS.name,),
)

IOS_TOU_EXPERIENCE_0_POINTS = NimbusTargetingConfig(
    name="iOS ToU Experience 0 Points",
    slug="ios_tou_experience_0_points",
    description="Existing iOS users who have not accepted ToU and have 0 points",
    targeting=(
        "has_accepted_terms_of_use == false && "
        "days_since_install >= 28 && "
        "tou_experience_points == 0"
    ),
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.IOS.name,),
)

IOS_TOU_EXPERIENCE_1_POINT = NimbusTargetingConfig(
    name="iOS ToU Experience 1 Point",
    slug="ios_tou_experience_1_point",
    description="Existing iOS users who have not accepted ToU and have 1 point",
    targeting=(
        "has_accepted_terms_of_use == false && "
        "days_since_install >= 28 && "
        "tou_experience_points == 1"
    ),
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.IOS.name,),
)

IOS_TOU_EXPERIENCE_2_POINTS = NimbusTargetingConfig(
    name="iOS ToU Experience 2 Points",
    slug="ios_tou_experience_2_points",
    description="Existing iOS users who have not accepted ToU and have 2 points",
    targeting=(
        "has_accepted_terms_of_use == false && "
        "days_since_install >= 28 && "
        "tou_experience_points == 2"
    ),
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.IOS.name,),
)

IOS_APPLE_INTELLIGENCE_AVAILABLE_USER = NimbusTargetingConfig(
    name="Apple Intelligence Available Users",
    slug="ios_apple_intelligence_available_user",
    description="Users that have apple intelligence available",
    targeting="is_apple_intelligence_available",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.IOS.name,),
)

CANNOT_USE_APPLE_INTELLIGENCE_USER = NimbusTargetingConfig(
    name="Cannot Use Apple Intelligence Users",
    slug="cannot_use_apple_intelligence_user",
    description="Users who cannot use the Apple Intelligence model",
    targeting="cannot_use_apple_intelligence",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.IOS.name,),
)

IOS_IPHONE_USERS_ONLY = NimbusTargetingConfig(
    name="iPhone users only",
    slug="ios_iphone_users_only",
    description="Targeting iPhone users",
    targeting="is_phone",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.IOS.name,),
)

IOS_IPHONE_FIRST_RUN_USER = NimbusTargetingConfig(
    name="First run Users on iPhone",
    slug="ios_iphone_first_run_user",
    description="First-run users on Firefox for iOS on iPhones",
    targeting="isFirstRun == 'true' && is_phone",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=True,
    application_choice_names=(Application.IOS.name,),
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

ANDROID_EARLY_APP_LAUNCH_USERS_ONLY = NimbusTargetingConfig(
    name="Android early app launch users only",
    slug="android_early_app_launch_users_only",
    description="Targeting users under or equal 20 app launches since install",
    targeting="number_of_app_launches <= 20",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.FENIX.name,),
)

ANDROID_LATER_APP_LAUNCH_USERS_ONLY = NimbusTargetingConfig(
    name="Android later app launch users only",
    slug="android_later_app_launch_users_only",
    description="Targeting users over 20 app launches since install",
    targeting="number_of_app_launches > 20",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.FENIX.name,),
)

ANDROID_DMA_USERS_ONLY = NimbusTargetingConfig(
    name="DMA users only",
    slug="android_dma_users_only",
    description="Targeting users who installed Firefox Android through DMA choice screen",
    targeting="install_referrer_response_utm_source == 'eea-browser-choice'",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.FENIX.name,),
)


ANDROID_LARGE_SCREEN_USERS_ONLY = NimbusTargetingConfig(
    name="Large screen device users only",
    slug="large_screen_device_users_only",
    description="Targeting users who have large screen devices",
    targeting="is_large_device",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.FENIX.name,),
)

ANDROID_EXISTING_USERS_NOT_ACCEPTED_TERMS_OF_USE = NimbusTargetingConfig(
    name="Existing users who have not accepted Terms of Use",
    slug="android_existing_users_not_accepted_terms_of_use",
    description="Existing users for 28+ days who have not accepted Terms of Use",
    targeting="user_accepted_tou == false && days_since_install >= 28",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.FENIX.name,),
)

ANDROID_EXISTING_USERS_NOT_ACCEPTED_TOU_AND_NO_SPONSORED_OPT_OUTS = NimbusTargetingConfig(
    name=(
        "Existing users for 28+ days who have not accepted Terms of Use "
        "and have not opted out of any sponsored content"
    ),
    slug="android_existing_users_not_accepted_terms_of_use_no_shortcuts_or_stories_opt_outs",
    description=(
        "Targeting users who have NOT accepted the Terms of Use "
        "and have NOT opted out of any sponsored content"
    ),
    targeting=(
        "user_accepted_tou == false && no_shortcuts_or_stories_opt_outs == true "
        "&& days_since_install >= 28"
    ),
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.FENIX.name,),
)

ANDROID_EXISTING_USERS_NOT_ACCEPTED_TERMS_OF_USE_ZERO_POINTS = NimbusTargetingConfig(
    name=(
        "Existing users who have not accepted the Terms of Use and have zero ToU points."
    ),
    slug="android_existing_users_not_accepted_terms_of_use_zero_tou_points",
    description=(
        "Existing users for 28+ days who "
        "have not accepted the Terms of Use, "
        "have zero ToU points and "
        "don't have any of the specified ad-blockers installed."
    ),
    targeting=(
        "user_accepted_tou == false && "
        "days_since_install >= 28 && "
        "("
        "tou_points == 0 && "
        "("
        "addon_ids['uBlock0@raymondhill.net'] == null && "
        "addon_ids['{d10d0bf8-f5b5-c8b4-a8b2-2b9879e08c5d}'] == null && "
        "addon_ids['adguardadblocker@adguard.com'] == null && "
        "addon_ids['adblockultimate@adblockultimate.net'] == null && "
        "addon_ids['firefox@ghostery.com'] == null && "
        "addon_ids['lock@adblock'] == null && "
        "addon_ids['ultrablock-pro@ultrablock.com'] == null && "
        "addon_ids['{2b3f2f5d-f5ae-44b3-846e-b630acf8eced}'] == null && "
        "addon_ids['kolesin.work@gmail.com'] == null && "
        "addon_ids['adblocker@pcmatic.com'] == null && "
        "addon_ids['{73a6fe31-595d-460b-a920-fcc0f8843232}'] == null"
        "))"
    ),
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.FENIX.name,),
)

ANDROID_EXISTING_USERS_NOT_ACCEPTED_TERMS_OF_USE_ONE_POINT = NimbusTargetingConfig(
    name=(
        "Existing users who have not accepted the Terms of Use and have one ToU point."
    ),
    slug="android_existing_users_not_accepted_terms_of_use_one_tou_point",
    description=(
        "Existing users for 28+ days who "
        "have not accepted the Terms of Use, "
        "have one ToU point or "
        "have at least one of the specified ad-blockers installed."
    ),
    targeting=(
        "user_accepted_tou == false && "
        "days_since_install >= 28 && "
        "("
        "tou_points == 1 || "
        "("
        "addon_ids['uBlock0@raymondhill.net'] != null || "
        "addon_ids['{d10d0bf8-f5b5-c8b4-a8b2-2b9879e08c5d}'] != null || "
        "addon_ids['adguardadblocker@adguard.com'] != null || "
        "addon_ids['adblockultimate@adblockultimate.net'] != null || "
        "addon_ids['firefox@ghostery.com'] != null || "
        "addon_ids['lock@adblock'] != null || "
        "addon_ids['ultrablock-pro@ultrablock.com'] != null || "
        "addon_ids['{2b3f2f5d-f5ae-44b3-846e-b630acf8eced}'] != null || "
        "addon_ids['kolesin.work@gmail.com'] != null || "
        "addon_ids['adblocker@pcmatic.com'] != null || "
        "addon_ids['{73a6fe31-595d-460b-a920-fcc0f8843232}'] != null"
        "))"
    ),
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.FENIX.name,),
)

ANDROID_EXISTING_USERS_NOT_ACCEPTED_TERMS_OF_USE_OVER_ONE_POINT = NimbusTargetingConfig(
    name=(
        "Existing users who have not accepted the Terms of Use "
        "and have more than one ToU point."
    ),
    slug="android_existing_users_not_accepted_terms_of_use_more_than_one_tou_point",
    description=(
        "Existing users for 28+ days who "
        "have not accepted the Terms of Use, "
        "have one ToU point and "
        "have at least one of the specified ad-blockers installed."
    ),
    targeting=(
        "user_accepted_tou == false && "
        "days_since_install >= 28 && "
        "("
        "tou_points == 1 && "
        "("
        "addon_ids['uBlock0@raymondhill.net'] != null || "
        "addon_ids['{d10d0bf8-f5b5-c8b4-a8b2-2b9879e08c5d}'] != null || "
        "addon_ids['adguardadblocker@adguard.com'] != null || "
        "addon_ids['adblockultimate@adblockultimate.net'] != null || "
        "addon_ids['firefox@ghostery.com'] != null || "
        "addon_ids['lock@adblock'] != null || "
        "addon_ids['ultrablock-pro@ultrablock.com'] != null || "
        "addon_ids['{2b3f2f5d-f5ae-44b3-846e-b630acf8eced}'] != null || "
        "addon_ids['kolesin.work@gmail.com'] != null || "
        "addon_ids['adblocker@pcmatic.com'] != null || "
        "addon_ids['{73a6fe31-595d-460b-a920-fcc0f8843232}'] != null"
        "))"
    ),
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.FENIX.name,),
)

TOU_TARGETING_ANDROID_ACCEPTED = NimbusTargetingConfig(
    name="Users that have accepted the Terms of Use",
    slug="users_accepted_tou",
    description="Targeting users who have accepted the Terms of Use",
    targeting="user_accepted_tou == true",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.FENIX.name,),
)

CHATBOT_IS_HUGGINGCHAT = NimbusTargetingConfig(
    name="Chatbot provider is HuggingChat",
    slug="chatbot_is_huggingchat",
    description="Users who selected HuggingChat",
    targeting="'browser.ml.chat.provider'|preferenceValue == 'https://huggingface.co/chat'",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

DEFAULT_PDF_IS_DIFFERENT_BROWSER = NimbusTargetingConfig(
    name="Default PDF handler is a different browser",
    slug="default_pdf_is_different_browser",
    description=(
        "Targeting users that have their default PDF handler set to a browser other "
        "than the current Firefox installation"
    ),
    targeting=(
        "!(isDefaultHandler || {}).pdf &&  (defaultPDFHandler || {}).knownBrowser"
    ),
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

ELIGIBLE_FOR_DEFAULT_PDF_HANDLER = NimbusTargetingConfig(
    name="Eligible for default PDF handler",
    slug="eligible_for_default_pdf_handler",
    description=(
        "Targeting users that are eligible to set Firefox as the default PDF "
        "handler and have yet to do so. This includes only users of Windows "
        "10+, and excludes users with enterprise policies and users that have "
        "set their default PDF handler to an app other than a browser (like a "
        "PDF editor)."
    ),
    targeting=(
        "os.isWindows &&"
        "  os.windowsVersion >= 10 &&"
        "  !hasActiveEnterprisePolicies &&"
        "  !(isDefaultHandler || {}).pdf &&"
        "  (!(defaultPDFHandler || {}).registered ||"
        "    (defaultPDFHandler || {}).knownBrowser)"
    ),
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

INELIGIBLE_FOR_DEFAULT_PDF_HANDLER = NimbusTargetingConfig(
    name="Ineligible for default PDF handler",
    slug="ineligible_for_default_pdf_handler",
    description=(
        "Targeting users that are ineligible to set Firefox as the default PDF "
        "handler or have already done so. This includes users of non-Windows "
        "OSes, users of Windows versions < 10, users with enterprise policies, "
        "users that have set Firefox as their default PDF handler, and users "
        "who have set their default PDF handler to a non-browser app."
    ),
    targeting=(
        "!os.isWindows ||"
        "  os.windowsVersion < 10 ||"
        "  hasActiveEnterprisePolicies ||"
        "  (isDefaultHandler || {}).pdf ||"
        "  ((defaultPDFHandler || {}).registered &&"
        "    !(defaultPDFHandler || {}).knownBrowser)"
    ),
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

DEBUG_INELIGIBLE_FOR_DEFAULT_PDF_HANDLER = NimbusTargetingConfig(
    name="DEBUG Ineligible for default PDF handler",
    slug="debug_ineligible_for_default_pdf_handler",
    description=(
        "Targeting users that are ineligible to set Firefox as the default PDF "
        "handler or have already done so. This omits safe navigators so bugs "
        "in the targeting getters can be debugged."
    ),
    targeting=(
        "(!os.isWindows || os.windowsVersion < 10) "
        "|| hasActiveEnterprisePolicies "
        "|| isDefaultHandler.pdf "
        "|| (defaultPDFHandler.registered && !defaultPDFHandler.knownBrowser)"
    ),
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

IS_4GB_RAM = NimbusTargetingConfig(
    name="Firefox build running on a computer with at least 4GB of RAM",
    slug="is_atleast_4gb_ram",
    description="Target computers with at least 4GB of RAM.",
    targeting="memoryMB >= 4000",
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

# --- Desktop Tier 1: High-End (≥16GB RAM) ---
IS_DESKTOP_TIER_1_HIGH_END = NimbusTargetingConfig(
    name="Desktop Tier 1: High-End (≥16GB RAM)",
    slug="desktop_tier_1_high_end",
    targeting="memoryMB >= 16384",
    description=(
        "High-end desktop devices with ≥16GB RAM, typically with SSDs and modern CPUs. "
        "Suitable for Performance Mode with acceptable memory/CPU trade-offs. "
        "Approximately 18.7% of desktop users (Dec 2025 data)."
    ),
    desktop_telemetry="metrics.quantity.system_memory >= 16384",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

# --- Desktop Tier 2: Mid-Range (8-16GB RAM) ---
IS_DESKTOP_TIER_2_MID_RANGE = NimbusTargetingConfig(
    name="Desktop Tier 2: Mid-Range (8-16GB RAM)",
    slug="desktop_tier_2_mid_range",
    targeting="memoryMB >= 8192 && memoryMB < 16384",
    description=(
        "Mid-range desktop devices with 8-16GB RAM. Suitable for Eco Mode when "
        "on battery, not recommended for Performance Mode due to OOM risk. "
        "Approximately 34.4% of desktop users (Dec 2025 data)."
    ),
    desktop_telemetry=(
        "metrics.quantity.system_memory >= 8192 "
        "AND metrics.quantity.system_memory < 16384"
    ),
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

# --- Desktop Tier 3: Low-End (<8GB RAM) ---
IS_DESKTOP_TIER_3_LOW_END = NimbusTargetingConfig(
    name="Desktop Tier 3: Low-End (<8GB RAM)",
    slug="desktop_tier_3_low_end",
    targeting="memoryMB < 8192",
    description=(
        "Low-end desktop devices with <8GB RAM, often with HDDs and older CPUs. "
        "Strongly recommended for Eco Mode to improve battery life and reduce "
        "thermal issues. Approximately 46.9% of desktop users "
        "(Dec 2025 data) - LARGEST segment."
    ),
    desktop_telemetry="metrics.quantity.system_memory < 8192",
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

VIEWPOINT_SURVEY_IOS = NimbusTargetingConfig(
    name="User Research Viewpoint Survey (Rolling Enrollmment)",
    slug="viewpoint_survey_ios",
    description=(
        "Rolling enrollment based on date. Only for use by User Research Viewpoint "
        "surveys."
    ),
    targeting=(
        "['rolling-viewpoint', nimbus_id]"
        "|bucketSample(current_date / (24 * 60 * 60 * 1000), 7, 233)"
    ),
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.IOS.name,),
)

VIEWPOINT_SURVEY_FENIX = NimbusTargetingConfig(
    name="User Research Viewpoint Survey (Rolling Enrollmment)",
    slug="viewpoint_survey_fenix",
    description=(
        "Rolling enrollment based on date. Only for use by User Research Viewpoint "
        "surveys."
    ),
    targeting=(
        "['rolling-viewpoint', nimbus_id]"
        "|bucketSample(current_date / (24 * 60 * 60 * 1000), 7, 350)"
    ),
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.FENIX.name,),
)

NEW_PROFILE_MAC_ONLY = NimbusTargetingConfig(
    name="New profile Mac OS only",
    slug="mac_only_new_profiles",
    description="New profiles with Mac OS",
    targeting=f"os.isMac && {NEW_PROFILE}",
    desktop_telemetry=f"{NEW_PROFILE} AND environment.system.os.name = 'Darwin'",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

SEARCH_ROLLOUT_1 = NimbusTargetingConfig(
    name="Search Rollout 1",
    slug="search_rollout_1",
    description="Search Rollout 1 Namespace",
    targeting="",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

SEARCH_ROLLOUT_2 = NimbusTargetingConfig(
    name="Search Rollout 2",
    slug="search_rollout_2",
    description="Search Rollout 2 Namespace",
    targeting="",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

AD_BLOCKERS_INSTALLED = NimbusTargetingConfig(
    name="Ad blockers installed",
    slug="ad_blockers_installed",
    description="Users who have installed an adblocker.",
    targeting=(
        "addonsInfo.addons['uBlock0@raymondhill.net'] != null || "
        "addonsInfo.addons['adblockultimate@adblockultimate.net'] != null || "
        "addonsInfo.addons['firefox@ghostery.com'] != null || "
        "addonsInfo.addons['jid1-NIfFY2CA8fy1tg@jetpack'] != null || "
        "addonsInfo.addons['{d10d0bf8-f5b5-c8b4-a8b2-2b9879e08c5d}'] != null || "
        "addonsInfo.addons['jid1-MnnxcxisBPnSXQ@jetpack'] != null || "
        "addonsInfo.addons['{74145f27-f039-47ce-a470-a662b129930a}'] != null"
    ),
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

HAS_BING_AS_DEFAULT_SEARCH_ENGINE_AND_AD_BLOCKERS_INSTALLED = NimbusTargetingConfig(
    name="Has Bing as current default search engine and ad blockers installed",
    slug="has_bing_as_current_default_search_engine_and_ad_blockers_installed",
    description=(
        "Users with bing as current default search engine and has an adblocker installed."
    ),
    targeting=(f"searchEngines.current =='bing' && ({AD_BLOCKERS_INSTALLED.targeting})"),
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

HAS_BING_AS_DEFAULT_SEARCH_ENGINE_AND_NO_AD_BLOCKERS_INSTALLED = NimbusTargetingConfig(
    name="Has Bing as current default search engine and no ad blockers installed",
    slug="has_bing_as_current_default_search_engine_and_no_ad_blockers_installed",
    description=(
        "Users with bing as current default search engine and has no adblocker installed."
    ),
    targeting=(f"searchEngines.current =='bing' && !({AD_BLOCKERS_INSTALLED.targeting})"),
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

EARLY_DAY_WIN1903_USER_HAS_DEFAULT = NimbusTargetingConfig(
    name="Early Day Windows 10 1903 User Has Default",
    slug="early_day_win1903_user_has_default",
    description=(
        "Early day (<28 days) Windows 10 1903+ users who have set "
        "Firefox as their default browser"
    ),
    targeting=f"{PROFILELESSTHAN28DAYS} && {WIN1903} && isDefaultBrowser",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

EXISTING_WIN1903_USER_HAS_DEFAULT = NimbusTargetingConfig(
    name="Existing Windows 1903+ User Has Default",
    slug="existing_win1903_user_has_default",
    description=(
        "Existing (>=28 days) Windows 1903+ users who have set Firefox "
        "as their default browser"
    ),
    targeting=f"{PROFILE28DAYS} && {WIN1903} && isDefaultBrowser",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

SIGNED_IN_USER = NimbusTargetingConfig(
    name="Signed-in User",
    slug="signed_in_user",
    description="Users who are signed into FxA",
    targeting="isFxASignedIn",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

SIGNED_OUT_USER = NimbusTargetingConfig(
    name="Signed-out User",
    slug="signed_out_user",
    description="Users who are NOT signed into FxA",
    targeting="!isFxASignedIn",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

SYNC_USER = NimbusTargetingConfig(
    name="Sync User",
    slug="sync_user",
    description="Users who have sync enabled and are signed into FxA",
    targeting="isFxASignedIn && usesFirefoxSync",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

EXISTING_USER_HASNT_CHANGED_BOOKMARKS_TOOLBAR = NimbusTargetingConfig(
    name="Existing User, Hasn't Changed Bookmarks Toolbar Behavior",
    slug="existing_user_bookmarks_toolbar_unchanged",
    description=(
        "Existing users (>=28 days) who have not edited the default bookmarks' "
        "toolbar behavior"
    ),
    targeting=(
        f"{PROFILE28DAYS} &&"
        " !('browser.toolbars.bookmarks.visibility'|preferenceIsUserSet)"
    ),
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

MOZILLA_TESTDAY_EVENT = NimbusTargetingConfig(
    name="Mozilla Testday",
    slug="users_that_have_testday_pref",
    description="Users that will be part of the Mozilla Testday events",
    targeting="'messaging-system-action.testday'|preferenceValue == 'testday'",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

DEFAULT_WINDOWS_CONTENT_PROCESS_SANDBOX_LEVEL = NimbusTargetingConfig(
    name="Windows users and default content process sandbox level",
    slug="default_windows_content_process_sandbox_level",
    description=(
        "Windows users who have not changed the content process sandbox level pref"
    ),
    targeting=("os.isWindows && !('security.sandbox.content.level'|preferenceIsUserSet)"),
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

DEFAULT_AUTOFILL_CREDIT_CARDS_SUPPORTED = NimbusTargetingConfig(
    name="Users with Default or Non-'On' Setting for Credit Card Autofill",
    slug="default_autofill_credit_cards_supported",
    description=(
        "Targets users who have left the 'extensions.formautofill.creditCards.supported' "
        "preference at its default value or set it to something other than 'on'."
    ),
    targeting=(
        "!('extensions.formautofill.creditCards.supported'|preferenceIsUserSet) || "
        "'extensions.formautofill.creditCards.supported'|preferenceValue != 'on'"
    ),
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

DEFAULT_AUTOFILL_ADDRESSES_SUPPORTED = NimbusTargetingConfig(
    name="Users with Default or Non-'On' Setting for Address Autofill",
    slug="default_autofill_addresses_supported",
    description=(
        "Targets users who have left the 'extensions.formautofill.addresses.supported' "
        "preference at its default value or set it to something other than 'on'."
    ),
    targeting=(
        "!('extensions.formautofill.addresses.supported'|preferenceIsUserSet) || "
        "'extensions.formautofill.addresses.supported'|preferenceValue != 'on'"
    ),
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

NO_HTTPS_ONLY_DESKTOP = NimbusTargetingConfig(
    name="Users who are not in HTTPS-Only Mode",
    slug="no_https_only_desktop",
    description=(
        "Targets users who do not have HTTPS-Only Mode enabled. Neither with "
        "'dom.security.https_only_mode' nor 'dom.security.https_only_mode_pbm'."
    ),
    targeting=(
        "!('dom.security.https_only_mode'|preferenceValue || "
        "'dom.security.https_only_mode_pbm'|preferenceValue)"
    ),
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

NO_PINNED_TABS = NimbusTargetingConfig(
    name="Users who have no pinned tabs",
    slug="no_pinned_tabs_desktop",
    description=("Targets users who have 0 pinned tabs in their open windows."),
    targeting=("!hasPinnedTabs"),
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

NON_SIDEBAR_USERS = NimbusTargetingConfig(
    name="Users that have never used the sidebar",
    slug="non_sidebar_users",
    description="Target users who have never used the new or old sidebar",
    targeting=(
        "!('sidebar.old-sidebar.has-used'|preferenceValue) && "
        "!('sidebar.revamp'|preferenceValue) && "
        "!('browser.engagement.sidebar-button.has-used'|preferenceValue) && "
        "primaryResolution.width > 1366 && "
        "primaryResolution.height > 768 && "
        "addonsInfo.addons['{446900e4-71c2-419f-a6a7-df9c091e268b}'] == null && "
        "addonsInfo.addons['{c3c10168-4186-445c-9c5b-63f12b8e2c87}'] == null && "
        "addonsInfo.addons['@m3u8link'] == null && "
        "addonsInfo.addons['jid0-adyhmvsP91nUO8pRv0Mn2VKeB84@jetpack'] == null && "
        "addonsInfo.addons['{3c078156-979c-498b-8990-85f7987dd929}'] == null && "
        "addonsInfo.addons['simple-tab-groups@drive4ik'] == null && "
        "addonsInfo.addons['{531906d3-e22f-4a6c-a102-8057b88a1a63}'] == null && "
        "addonsInfo.addons['tab-stash@condordes.net'] == null && "
        "addonsInfo.addons['treestyletab@piro.sakura.ne.jp'] == null && "
        "addonsInfo.addons['{b9db16a4-6edc-47ec-a1f4-b86292ed211d}'] == null"
    ),
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

NON_SIDEBAR_USERS_V2 = NimbusTargetingConfig(
    name="Users that have never used the sidebar v2",
    slug="non_sidebar_users_v2",
    description="Target users who have never used the new or old sidebar v2",
    targeting=(
        "!('sidebar.old-sidebar.has-used'|preferenceValue) && "
        "!('sidebar.revamp'|preferenceValue) && "
        "!('browser.engagement.sidebar-button.has-used'|preferenceValue) && "
        "primaryResolution.width > 1366 && "
        "primaryResolution.height > 768 && "
        "addonsInfo.addons['{c3c10168-4186-445c-9c5b-63f12b8e2c87}'] == null && "
        "addonsInfo.addons['@m3u8link'] == null && "
        "addonsInfo.addons['{3c078156-979c-498b-8990-85f7987dd929}'] == null && "
        "addonsInfo.addons['simple-tab-groups@drive4ik'] == null && "
        "addonsInfo.addons['treestyletab@piro.sakura.ne.jp'] == null"
    ),
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

OLD_SIDEBAR_USERS_V2 = NimbusTargetingConfig(
    name="Users that use the old sidebar",
    slug="old_sidebar_users_v2",
    description="Target users who use the old sidebar",
    targeting="!('sidebar.revamp'|preferenceValue) && "
    "'browser.uiCustomization.state'|preferenceValue('')|regExpMatch"
    "('sidebar-button') != null",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

NEW_SIDEBAR_USERS = NimbusTargetingConfig(
    name="Users that use the new sidebar",
    slug="new_sidebar_users",
    description="Target users who use the new sidebar",
    targeting="'sidebar.revamp'|preferenceValue",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

SIGNED_OUT_EARLY_DAY_USER = NimbusTargetingConfig(
    name="Signed-out early day user",
    slug="signed_out_early_day_user",
    description="Early day users who are NOT signed into FxA",
    targeting=f"{PROFILELESSTHAN28DAYS} && !isFxASignedIn",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

SIGNED_OUT_EXISTING_USER = NimbusTargetingConfig(
    name="Signed-out existing user",
    slug="signed_out_existing_user",
    description="Existing users who are NOT signed into FxA",
    targeting=f"{PROFILE28DAYS} && !isFxASignedIn",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

SIGNED_OUT_EARLY_DAY_USER_FXA_ENABLED_NO_ENTERPRISE = NimbusTargetingConfig(
    name="Signed-out early day user, FxA enabled, no enterprise policies",
    slug="signed_out_early_day_user_fxa_enabled_no_enterprise",
    description=(
        "Existing users who are NOT signed into FxA, with FxA enabled, "
        "and no enterprise policies"
    ),
    targeting=(
        f"{PROFILELESSTHAN28DAYS} && {NO_ENTERPRISE.targeting} && "
        "!isFxASignedIn && isFxAEnabled"
    ),
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

SIGNED_OUT_EXISTING_USER_FXA_ENABLED_NO_ENTERPRISE = NimbusTargetingConfig(
    name="Signed-out existing user, FxA enabled, no enterprise policies",
    slug="signed_out_existing_user_fxa_enabled_no_enterprise",
    description=(
        "Existing users who are NOT signed into FxA, with FxA enabled, "
        "and no enterprise policies"
    ),
    targeting=(
        f"{PROFILE28DAYS} && {NO_ENTERPRISE.targeting} && !isFxASignedIn && isFxAEnabled"
    ),
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

SIGNED_OUT_USER_FXA_ENABLED_NO_ENTERPRISE = NimbusTargetingConfig(
    name="Signed-out user, FxA enabled, no enterprise policies",
    slug="signed_out_user_fxa_enabled_no_enterprise",
    description=(
        "Users with profiles older than 7 days, who are NOT signed into FxA, "
        "with FxA enabled, and no enterprise policies"
    ),
    targeting=(
        f"{PROFILEMORETHAN7DAYS} && {NO_ENTERPRISE.targeting} "
        "&& !isFxASignedIn && isFxAEnabled"
    ),
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

SIGNED_OUT_POST_FIRST_RUN_USER_FXA_ENABLED_NO_ENTERPRISE = NimbusTargetingConfig(
    name="Signed-out user, post first run, FxA enabled, no enterprise policies",
    slug="signed_out_user_post_first_run_fxa_enabled_no_enterprise",
    description=(
        "Users with profiles older than 7 days, post first run, "
        "who are NOT signed into FxA, with FxA enabled, and no enterprise policies"
    ),
    targeting=(
        f"{PROFILEMORETHAN7DAYS} && {NO_ENTERPRISE.targeting} "
        "&& !isFirstStartup && !isFxASignedIn && isFxAEnabled"
    ),
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

TOU_ACCEPTED_V4PLUS_MAC_OR_WIN = NimbusTargetingConfig(
    name="TOU version 4 or higher accepted, Mac or Win",
    slug="tou_accepted_mac_win",
    description=("Users who have accepted the terms of use, and are on Mac or Windows"),
    targeting=f"""
    (
        (
            os.isWindows
            ||
            os.isMac
        )
        &&
        {ACCEPTED_TOU_V4_OR_HIGHER}
    )
    """,
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

TOU_NOT_ACCEPTED_V4PLUS_MAC_OR_WIN = NimbusTargetingConfig(
    name="TOU version 4 or higher NOT accepted, Mac or Win",
    slug="tou_not_accepted_mac_win",
    description=(
        "Users who have NOT accepted the terms of use, "
        "are not configured to bypass TOU, "
        "and are on Mac or Windows"
    ),
    targeting=f"""
    (
        (
            (
                os.isWindows
                ||
                os.isMac
            )
            &&
            !({ACCEPTED_TOU_V4_OR_HIGHER})
        )
        &&
        !({TOU_NOTIFICATION_BYPASS_ENABLED})
    )
    """,
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

TOU_ACCEPTED_V4_MAC_OR_WIN_AND_SPONSORED_TOPSITES_ENABLED = NimbusTargetingConfig(
    name="Mac or Windows users accepted TOU version 4 and Sponsored TopSites enabled",
    slug="tou_accepted_mac_win_newtab_sponsored_topsites_enabled",
    description=(
        "TOU version 4 or higher accepted, Mac or Win, and Sponsored TopSites enabled"
    ),
    targeting=f"""
    (
        (
            os.isWindows
            ||
            os.isMac
        )
        &&
        {ACCEPTED_TOU_V4_OR_HIGHER}
        &&
        'browser.newtabpage.activity-stream.showSponsoredTopSites'|preferenceValue
    )
    """,
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

TOU_ACCEPTED_V4_MAC_OR_WIN_AND_SPONSORED_TOPSITES_ENABLED_V2 = NimbusTargetingConfig(
    name="Mac or Windows users accepted TOU V4, all TopSites enabled",
    slug="tou_accepted_mac_win_newtab_sponsored_topsites_enabled_v2",
    description=(
        "TOU version 4 or higher accepted, Mac or Win, and all TopSites enabled"
    ),
    targeting=f"""
    (
        (
            os.isWindows
            ||
            os.isMac
        )
        &&
        {ACCEPTED_TOU_V4_OR_HIGHER}
        &&
        'browser.newtabpage.activity-stream.feeds.topsites'|preferenceValue
        &&
        'browser.newtabpage.activity-stream.showSponsoredTopSites'|preferenceValue
    )
    """,
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

WIN10_FIREFOX_VPN_ELIGIBLE = NimbusTargetingConfig(
    name="Windows 10 users eligible for Firefox VPN",
    slug="win10_firefox_vpn",
    description=(
        "Windows 10 users who are signed out, at least 7 days old, "
        "no enterprise, are not using a proxy, and "
        "do not have the VPN extension installed"
    ),
    targeting=(
        "os.isWindows && os.windowsVersion >= 10.0 && os.windowsBuildNumber < 22000 &&"
        "isFxAEnabled && !isFxASignedIn && "
        f"{NO_ENTERPRISE.targeting} && "
        f"{PROFILEMORETHAN7DAYS} && "
        "'network.proxy.type'|preferenceValue != 1 && "
        "addonsInfo.addons['vpn@mozilla.com'] == null"
    ),
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

# TO DO - add MAC AND WINDOWS ONLY for all three levels
TOU_EXPERIENCE_0 = NimbusTargetingConfig(
    name="TOU Experience 0",
    slug="tou_experience_0",
    description=(
        "User has not accepted TOU V4 or higher and should see TOU experience 0, "
        "and is on Mac or Windows"
    ),
    targeting=f"""
    (
        (
            os.isWindows
            ||
            os.isMac
        )
        &&
        !({ACCEPTED_TOU_V4_OR_HIGHER})
        &&
        !({TOU_NOTIFICATION_BYPASS_ENABLED})
        &&
        {TOU_EXPERIENCE_TOTAL} == 0
    )
    """,
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

TOU_EXPERIENCE_1 = NimbusTargetingConfig(
    name="TOU Experience 1",
    slug="tou_experience_1",
    description=(
        "User has not accepted TOU V4 or higher and should see TOU experience 1, "
        "and is on Mac or Windows"
    ),
    targeting=f"""
    (
        (
            os.isWindows
            ||
            os.isMac
        )
        &&
        !({ACCEPTED_TOU_V4_OR_HIGHER})
        &&
        !({TOU_NOTIFICATION_BYPASS_ENABLED})
        &&
        {TOU_EXPERIENCE_TOTAL} == 1
    )
    """,
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

TOU_EXPERIENCE_2 = NimbusTargetingConfig(
    name="TOU Experience 2",
    slug="tou_experience_2",
    description=(
        "User has not accepted TOU V4 or higher and should see TOU experience 2, "
        "and is on Mac or Windows"
    ),
    targeting=f"""
    (
        (
            os.isWindows
            ||
            os.isMac
        )
        &&
        !({ACCEPTED_TOU_V4_OR_HIGHER})
        &&
        !({TOU_NOTIFICATION_BYPASS_ENABLED})
        &&
        {TOU_EXPERIENCE_TOTAL} >= 2
    )
    """,
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

ACCEPTED_TOU_BEFORE_DEC_9_2025 = NimbusTargetingConfig(
    name="Accepted TOU before Dec 9, 2025",
    slug="accepted_tou_before_dec_9_2025",
    description=("User accepted TOU before Dec 9, 2025 (excludes Linux)"),
    targeting=f"""
    (
        !os.isLinux
        &&
        {HAS_TOU_ACCEPTED_DATE}
        &&
        ({TOU_ACCEPTED_DATE} < {DEC_9_2025})
    )
    """,
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

ACCEPTED_TOU_ON_OR_AFTER_DEC_9_2025 = NimbusTargetingConfig(
    name="Accepted TOU on or after Dec 9, 2025",
    slug="accepted_tou_on_or_after_dec_9_2025",
    description=("User accepted TOU on or after Dec 9, 2025"),
    targeting=f"""
    (
        {HAS_TOU_ACCEPTED_DATE}
        &&
        ({TOU_ACCEPTED_DATE} >= {DEC_9_2025})
    )
    """,
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

ACCEPTED_TOU_BEFORE_DEC_17_2025 = NimbusTargetingConfig(
    name="Accepted TOU before Dec 17, 2025",
    slug="accepted_tou_before_dec_17_2025",
    description=("User accepted TOU before Dec 17, 2025 (excludes Linux)"),
    targeting=f"""
    (
        !os.isLinux
        &&
        {HAS_TOU_ACCEPTED_DATE}
        &&
        ({TOU_ACCEPTED_DATE} < {DEC_17_2025})
    )
    """,
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

ACCEPTED_TOU_ON_OR_AFTER_DEC_15_2025 = NimbusTargetingConfig(
    name="Accepted TOU on or after Dec 15, 2025",
    slug="accepted_tou_on_or_after_dec_15_2025",
    description=("User accepted TOU on or after Dec 15, 2025"),
    targeting=f"""
    (
        {HAS_TOU_ACCEPTED_DATE}
        &&
        ({TOU_ACCEPTED_DATE} >= {DEC_15_2025})
    )
    """,
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

WINDOWS_10_PLUS_SIGNED_OUT_USER = NimbusTargetingConfig(
    name="Windows 10+ signed out user",
    slug="windows_10_plus_signed_out",
    description="Windows users on version 10 or higher who are not signed into FxA",
    targeting="!isFxASignedIn && (os.isWindows && os.windowsVersion >= 10)",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

MAC_SIGNED_OUT_USER = NimbusTargetingConfig(
    name="Mac signed out user",
    slug="mac_signed_out",
    description="Mac users who are not signed into FxA",
    targeting="!isFxASignedIn && os.isMac",
    desktop_telemetry="",
    sticky_required=True,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

FX_145_TRAINHOP = NimbusTargetingConfig(
    name="New Tab Fx145 9-19 Trainhop",
    slug="newtab-145-0919-trainhop",
    description="Desktop users having the New Tab 145.0.20250919 train hop,"
    "which includes users of Fx143",
    targeting="newtabAddonVersion|versionCompare('145.0.20250919.173227') >= 0",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

FX_145_1_TRAINHOP = NimbusTargetingConfig(
    name="New Tab Fx145 10-09 Trainhop",
    slug="newtab-145-1009-trainhop",
    description="Desktop users having the New Tab 145.1.20251009 train hop,"
    "which includes users of Fx144",
    targeting="newtabAddonVersion|versionCompare('145.1.20251009.134757') >= 0",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

FX_146_TRAINHOP = NimbusTargetingConfig(
    name="New Tab Fx146.0.1 11-24 Trainhop",
    slug="newtab-146-1124-trainhop",
    description=(
        "Desktop users having the New Tab 146.0.20251107.60212 train hop, "
        "which includes users of Fx145_0_1"
    ),
    targeting="newtabAddonVersion|versionCompare('146.0.20251107.60212') >= 0",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

FX_146_1_TRAINHOP = NimbusTargetingConfig(
    name="New Tab Fx146 11-24 Trainhop",
    slug="newtab-146-1-1124-trainhop",
    description=(
        "Desktop users having the New Tab 147.0.20251114.194929 train hop, "
        "which includes users of Fx145_0_1"
    ),
    targeting="newtabAddonVersion|versionCompare('147.0.20251114.194929') >= 0",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

FX_148_TRAINHOP = NimbusTargetingConfig(
    name="New Tab Fx148 12-11 Trainhop",
    slug="newtab-148-1211-trainhop",
    description=(
        "Desktop users having the New Tab 148.0.20251211.63751 train hop, "
        "which includes users of Fx146"
    ),
    targeting="newtabAddonVersion|versionCompare('148.0.20251211.63751') >= 0",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

BUILDID_20251006095753 = NimbusTargetingConfig(
    name="Build ID 20251006095753 or higher",
    slug="buildid-20251006095753",
    description="Desktop users having the Build ID 20251006095753 or higher",
    targeting="buildId >= 20251006095753",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

PROFILES_NUM_ZERO = NimbusTargetingConfig(
    name="Number of Profiles is Zero",
    slug="number_of_profiles_is_zero",
    description="Desktop users having zero profiles",
    targeting="profileGroupProfileCount == 0",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

PROFILES_NUM_NON_ZERO = NimbusTargetingConfig(
    name="Number of Profiles is Non-Zero",
    slug="number_of_profiles_is_non_zero",
    description="Desktop users having non-zero profiles",
    targeting="profileGroupProfileCount > 0",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)

AI_TAB_GROUPING_ENABLED = NimbusTargetingConfig(
    name="AI Tab Grouping Enabled",
    slug="ai_tab_grouping_enabled",
    description="Users with AI tab grouping feature enabled via preferences",
    targeting=(
        "'browser.tabs.groups.smart.enabled'|preferenceValue && "
        "'browser.tabs.groups.smart.userEnabled'|preferenceValue && "
        "'browser.tabs.groups.smart.optin'|preferenceValue"
    ),
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)


class TargetingConstants:
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
        Application.IOS: NimbusConstants.Version.FIREFOX_98,
    }
