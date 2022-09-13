from dataclasses import dataclass

from django.db import models

from experimenter.experiments.constants import Application, NimbusConstants


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
WIN1903 = "os.windowsBuildNumber >= 18362"

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

FIRST_RUN_CHROME_ATTRIBUTION = NimbusTargetingConfig(
    name="First start-up users from Chrome",
    slug="first_run_chrome",
    description=(
        "First start-up users (e.g. for about:welcome) who download Firefox "
        "from Chrome"
    ),
    targeting="{first_run} && attributionData.ua == 'chrome'".format(
        first_run=FIRST_RUN.targeting
    ),
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
    targeting="{first_run} && os.windowsBuildNumber >= 18362".format(
        first_run=FIRST_RUN.targeting
    ),
    desktop_telemetry=(
        "{first_run} AND environment.system.os.windows_build_number >= 18362"
    ).format(first_run=FIRST_RUN.desktop_telemetry),
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
    targeting="{first_run} && {not_tcp_study}".format(
        first_run=FIRST_RUN.targeting,
        not_tcp_study=NOT_TCP_STUDY.targeting,
    ),
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
    targeting="{first_run} && {user_choice}".format(
        first_run=FIRST_RUN.targeting,
        user_choice=WINDOWS_WITH_USERCHOICE.targeting,
    ),
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
