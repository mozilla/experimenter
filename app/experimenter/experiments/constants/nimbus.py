from dataclasses import dataclass
from typing import Dict

from django.conf import settings
from django.db import models
from packaging import version


class Channel(models.TextChoices):
    NO_CHANNEL = ""
    UNBRANDED = "default"
    NIGHTLY = "nightly"
    BETA = "beta"
    RELEASE = "release"
    ESR = "esr"
    TESTFLIGHT = "testflight"


class BucketRandomizationUnit(models.TextChoices):
    NORMANDY = "normandy_id"
    NIMBUS = "nimbus_id"


@dataclass
class ApplicationConfig:
    name: str
    slug: str
    app_name: str
    channel_app_id: Dict[str, str]
    kinto_collection: str
    randomization_unit: str


APPLICATION_CONFIG_DESKTOP = ApplicationConfig(
    name="Firefox Desktop",
    slug="firefox-desktop",
    app_name="firefox_desktop",
    channel_app_id={
        Channel.NO_CHANNEL: "firefox-desktop",
        Channel.UNBRANDED: "firefox-desktop",
        Channel.NIGHTLY: "firefox-desktop",
        Channel.BETA: "firefox-desktop",
        Channel.RELEASE: "firefox-desktop",
        Channel.ESR: "firefox-desktop",
    },
    kinto_collection=settings.KINTO_COLLECTION_NIMBUS_DESKTOP,
    randomization_unit=BucketRandomizationUnit.NORMANDY,
)

APPLICATION_CONFIG_FENIX = ApplicationConfig(
    name="Firefox for Android (Fenix)",
    slug="fenix",
    app_name="fenix",
    channel_app_id={
        Channel.NIGHTLY: "org.mozilla.fenix",
        Channel.BETA: "org.mozilla.firefox_beta",
        Channel.RELEASE: "org.mozilla.firefox",
    },
    kinto_collection=settings.KINTO_COLLECTION_NIMBUS_MOBILE,
    randomization_unit=BucketRandomizationUnit.NIMBUS,
)

APPLICATION_CONFIG_IOS = ApplicationConfig(
    name="Firefox for iOS",
    slug="ios",
    app_name="firefox_ios",
    channel_app_id={
        Channel.NIGHTLY: "org.mozilla.ios.Fennec",
        Channel.BETA: "org.mozilla.ios.FirefoxBeta",
        Channel.RELEASE: "org.mozilla.ios.Firefox",
    },
    kinto_collection=settings.KINTO_COLLECTION_NIMBUS_MOBILE,
    randomization_unit=BucketRandomizationUnit.NIMBUS,
)

APPLICATION_CONFIG_FOCUS_ANDROID = ApplicationConfig(
    name="Focus for Android",
    slug="focus-android",
    app_name="focus_android",
    channel_app_id={
        Channel.NIGHTLY: "org.mozilla.focus.nightly",
        Channel.BETA: "org.mozilla.focus.beta",
        Channel.RELEASE: "org.mozilla.focus",
    },
    kinto_collection=settings.KINTO_COLLECTION_NIMBUS_MOBILE,
    randomization_unit=BucketRandomizationUnit.NIMBUS,
)

APPLICATION_CONFIG_KLAR_ANDROID = ApplicationConfig(
    name="Klar for Android",
    slug="klar-android",
    app_name="klar_android",
    channel_app_id={
        Channel.RELEASE: "org.mozilla.klar",
    },
    kinto_collection=settings.KINTO_COLLECTION_NIMBUS_MOBILE,
    randomization_unit=BucketRandomizationUnit.NIMBUS,
)


APPLICATION_CONFIG_FOCUS_IOS = ApplicationConfig(
    name="Focus for iOS",
    slug="focus-ios",
    app_name="focus_ios",
    channel_app_id={
        Channel.RELEASE: "org.mozilla.ios.Focus",
        Channel.TESTFLIGHT: "org.mozilla.ios.Focus",
    },
    kinto_collection=settings.KINTO_COLLECTION_NIMBUS_MOBILE,
    randomization_unit=BucketRandomizationUnit.NIMBUS,
)

APPLICATION_CONFIG_KLAR_IOS = ApplicationConfig(
    name="Klar for iOS",
    slug="klar-ios",
    app_name="klar_ios",
    channel_app_id={
        Channel.RELEASE: "org.mozilla.ios.Klar",
        Channel.TESTFLIGHT: "org.mozilla.ios.Klar",
    },
    kinto_collection=settings.KINTO_COLLECTION_NIMBUS_MOBILE,
    randomization_unit=BucketRandomizationUnit.NIMBUS,
)


class Application(models.TextChoices):
    DESKTOP = (APPLICATION_CONFIG_DESKTOP.slug, APPLICATION_CONFIG_DESKTOP.name)
    FENIX = (APPLICATION_CONFIG_FENIX.slug, APPLICATION_CONFIG_FENIX.name)
    IOS = (APPLICATION_CONFIG_IOS.slug, APPLICATION_CONFIG_IOS.name)
    FOCUS_ANDROID = (
        APPLICATION_CONFIG_FOCUS_ANDROID.slug,
        APPLICATION_CONFIG_FOCUS_ANDROID.name,
    )
    KLAR_ANDROID = (
        APPLICATION_CONFIG_KLAR_ANDROID.slug,
        APPLICATION_CONFIG_KLAR_ANDROID.name,
    )
    FOCUS_IOS = (
        APPLICATION_CONFIG_FOCUS_IOS.slug,
        APPLICATION_CONFIG_FOCUS_IOS.name,
    )
    KLAR_IOS = (
        APPLICATION_CONFIG_KLAR_IOS.slug,
        APPLICATION_CONFIG_KLAR_IOS.name,
    )


@dataclass
class NimbusTargetingConfig:
    name: str
    slug: str
    description: str
    targeting: str
    desktop_telemetry: str
    application_choice_names: list[str]


TARGETING_STICKY = "experiment.slug in activeExperiments"
TARGETING_HAS_PIN = "!doesAppNeedPin"
TARGETING_NEED_DEFAULT = "!isDefaultBrowser"
TARGETING_PROFILE28DAYS = "(currentDate|date - profileAgeCreated|date) / 86400000 >= 28"
TARGETING_WIN1903 = "os.windowsBuildNumber >= 18362"

TARGETING_NO_TARGETING = NimbusTargetingConfig(
    name="No Targeting",
    slug="",
    description="All users",
    targeting="",
    desktop_telemetry="",
    application_choice_names=[a.name for a in Application],
)

TARGETING_FIRST_RUN = NimbusTargetingConfig(
    name="First start-up users",
    slug="first_run",
    description=("First start-up users (e.g. for about:welcome)"),
    targeting=("(({is_first_startup} && {not_see_aw}) || {sticky})").format(
        is_first_startup="isFirstStartup",
        not_see_aw="!('trailhead.firstrun.didSeeAboutWelcome'|preferenceValue)",
        sticky=TARGETING_STICKY,
    ),
    desktop_telemetry=("payload.info.profile_subsession_counter = 1"),
    application_choice_names=(Application.DESKTOP.name,),
)

TARGETING_FIRST_RUN_CHROME_ATTRIBUTION = NimbusTargetingConfig(
    name="First start-up users from Chrome",
    slug="first_run_chrome",
    description=(
        "First start-up users (e.g. for about:welcome) who download Firefox "
        "from Chrome"
    ),
    targeting=("{first_run} && attributionData.ua == 'chrome'").format(
        first_run=TARGETING_FIRST_RUN.targeting
    ),
    desktop_telemetry=(
        "{first_run} AND environment.settings.attribution.ua = 'chrome'"
    ).format(first_run=TARGETING_FIRST_RUN.desktop_telemetry),
    application_choice_names=(Application.DESKTOP.name,),
)

TARGETING_FIRST_RUN_WINDOWS_1903_NEWER = NimbusTargetingConfig(
    name="First start-up users on Windows 10 1903 (build 18362) or newer",
    slug="first_run_win1903",
    description="First start-up users (e.g. for about:welcome) on Windows 1903+",
    targeting=("{first_run} && os.windowsBuildNumber >= 18362").format(
        first_run=TARGETING_FIRST_RUN.targeting
    ),
    desktop_telemetry=(
        "{first_run} AND environment.system.os.windows_build_number >= 18362"
    ).format(first_run=TARGETING_FIRST_RUN.desktop_telemetry),
    application_choice_names=(Application.DESKTOP.name,),
)

TARGETING_NOT_TCP_STUDY = NimbusTargetingConfig(
    name="Exclude users in the TCP revenue study",
    slug="not_tcp_study",
    description="Exclude users with certain search codes set",
    targeting="!'browser.search.param.google_channel_us'|preferenceValue('')|regExpMatch"
    "('^[ntc]us5$') && !'browser.search.param.google_channel_row'|preferenceValue('')|"
    "regExpMatch('^[ntc]row5$')",
    desktop_telemetry="",
    application_choice_names=(Application.DESKTOP.name,),
)

TARGETING_NOT_TCP_STUDY_FIRST_RUN = NimbusTargetingConfig(
    name="First start-up users excluding TCP revenue study",
    slug="not_tcp_study_first_run",
    description="First start-up users excluding certain search codes",
    targeting="{first_run} && {not_tcp_study}".format(
        first_run=TARGETING_FIRST_RUN.targeting,
        not_tcp_study=TARGETING_NOT_TCP_STUDY.targeting,
    ),
    desktop_telemetry="",
    application_choice_names=(Application.DESKTOP.name,),
)

TARGETING_WINDOWS_WITH_USERCHOICE = NimbusTargetingConfig(
    name="Users on Windows with UserChoice support",
    slug="windows_userchoice",
    description=(
        "Users on Windows with UserChoice support (version 1809+/build ID 17763+)"
    ),
    targeting="os.windowsBuildNumber >= 17763",
    desktop_telemetry="environment.system.os.windows_build_number >= 17763",
    application_choice_names=(Application.DESKTOP.name,),
)

TARGETING_WINDOWS_WITH_USERCHOICE_FIRST_RUN = NimbusTargetingConfig(
    name="First start-up users on Windows with UserChoice support",
    slug="windows_userchoice_first_run",
    description=(
        "First start-up users (e.g. for about:welcome) on Windows with "
        "UserChoice support (version 1809+/build ID 17763+)"
    ),
    targeting="{first_run} && {user_choice}".format(
        first_run=TARGETING_FIRST_RUN.targeting,
        user_choice=TARGETING_WINDOWS_WITH_USERCHOICE.targeting,
    ),
    desktop_telemetry=("{first_run} AND {user_choice}").format(
        first_run=TARGETING_FIRST_RUN.desktop_telemetry,
        user_choice=TARGETING_WINDOWS_WITH_USERCHOICE.desktop_telemetry,
    ),
    application_choice_names=(Application.DESKTOP.name,),
)

TARGETING_FX95_DESKTOP_USERS = NimbusTargetingConfig(
    name="Desktop Users on Fx95",
    slug="fx95_desktop_users",
    description=("Firefox 95 Desktop users"),
    targeting=(
        "(version|versionCompare('95.!') >= 0) && (version|versionCompare('96.!') < 0)"
    ),
    desktop_telemetry="",
    application_choice_names=(Application.DESKTOP.name,),
)

TARGETING_MOBILE_NEW_USER = NimbusTargetingConfig(
    name="New Users on Mobile",
    slug="mobile_new_users",
    description=("New users on mobile who installed the app less than a week ago"),
    targeting=("is_already_enrolled || days_since_install < 7"),
    desktop_telemetry="",
    application_choice_names=(
        Application.FENIX.name,
        Application.IOS.name,
        Application.FOCUS_ANDROID.name,
        Application.FOCUS_IOS.name,
        Application.KLAR_ANDROID.name,
        Application.KLAR_IOS.name,
    ),
)

TARGETING_MOBILE_RECENTLY_UPDATED = NimbusTargetingConfig(
    name="Recently Updated Users",
    slug="mobile_recently_updated_users",
    description=(
        "Users who updated their app within the last week. "
        "This excludes users who are new users"
    ),
    targeting=(
        "is_already_enrolled || (days_since_update < 7 && days_since_install >= 7)"
    ),
    desktop_telemetry="",
    application_choice_names=(
        Application.FENIX.name,
        Application.IOS.name,
        Application.FOCUS_ANDROID.name,
        Application.FOCUS_IOS.name,
        Application.KLAR_ANDROID.name,
        Application.KLAR_IOS.name,
    ),
)


TARGETING_HOMEPAGE_GOOGLE = NimbusTargetingConfig(
    name="Homepage set to google.com",
    slug="homepage_google_dot_com",
    description="Users with their Homepage set to google.com",
    targeting=(
        "!homePageSettings.isDefault && "
        "homePageSettings.isCustomUrl && "
        "homePageSettings.urls[.host == 'google.com']|length > 0"
    ),
    desktop_telemetry="",
    application_choice_names=(Application.DESKTOP.name,),
)

TARGETING_URLBAR_FIREFOX_SUGGEST = NimbusTargetingConfig(
    name="Urlbar (Firefox Suggest)",
    slug="urlbar_firefox_suggest",
    description="Users with the default search suggestion showing order",
    targeting="'browser.urlbar.showSearchSuggestionsFirst'|preferenceValue",
    desktop_telemetry="",
    application_choice_names=(Application.DESKTOP.name,),
)

TARGETING_MAC_ONLY = NimbusTargetingConfig(
    name="Mac OS users only",
    slug="mac_only",
    description="All users with Mac OS",
    targeting="os.isMac",
    desktop_telemetry="environment.system.os.name = 'Darwin'",
    application_choice_names=(Application.DESKTOP.name,),
)

TARGETING_NO_ENTERPRISE = NimbusTargetingConfig(
    name="No enterprise users",
    slug="no_enterprise_users",
    description="Exclude users with active enterpries policies",
    targeting="!hasActiveEnterprisePolicies",
    desktop_telemetry="",
    application_choice_names=(Application.DESKTOP.name,),
)

TARGETING_NO_ENTERPRISE_OR_PAST_VPN = NimbusTargetingConfig(
    name="No enterprise or past VPN use",
    slug="no_enterprise_or_past_vpn",
    description="Exclude users who have used Mozilla VPN or who are enterprise users",
    targeting=(
        f"{TARGETING_NO_ENTERPRISE.targeting} && "
        '!("e6eb0d1e856335fc" in attachedFxAOAuthClients|mapToProperty("id"))'
    ),
    desktop_telemetry="",
    application_choice_names=(Application.DESKTOP.name,),
)

TARGETING_NO_ENTERPRISE_OR_RECENT_VPN = NimbusTargetingConfig(
    name="No enterprise and no VPN connection in the last 30 days",
    slug="no_enterprise_or_last_30d_vpn_use",
    description="Exclude enterprise & users who have used MozVPN in the last 30 days",
    targeting=(
        f"{TARGETING_NO_ENTERPRISE.targeting} && "
        '(("e6eb0d1e856335fc" in attachedFxAOAuthClients|mapToProperty("id")) ? '
        '(attachedFxAOAuthClients[.id == "e6eb0d1e856335fc"].lastAccessedDaysAgo > 29) : '
        "true)"
    ),
    desktop_telemetry="",
    application_choice_names=(Application.DESKTOP.name,),
)

INFREQUENT_USER_URIS = NimbusTargetingConfig(
    name="Infrequent user (uris)",
    slug="infrequent_user_uris",
    description="Between 1 and 6 days of activity in the past 28 days",
    targeting=f"{TARGETING_STICKY} || {TARGETING_PROFILE28DAYS} && "
    "userMonthlyActivity|length >= 1 && userMonthlyActivity|length <= 6",
    desktop_telemetry="",
    application_choice_names=(Application.DESKTOP.name,),
)

INFREQUENT_USER_NEED_PIN = NimbusTargetingConfig(
    name="Infrequent user (need pin)",
    slug="infrequent_user_need_pin",
    description="Between 1 and 6 days of activity in the past 28 days needing pin",
    targeting=f"{INFREQUENT_USER_URIS.targeting} && doesAppNeedPin",
    desktop_telemetry="",
    application_choice_names=(Application.DESKTOP.name,),
)

INFREQUENT_USER_NEED_DEFAULT = NimbusTargetingConfig(
    name="Infrequent user (need default)",
    slug="infrequent_user_need_default",
    description="Between 1 and 6 days of activity in the past 28 days needing default",
    targeting=f"{INFREQUENT_USER_URIS.targeting} && {TARGETING_NEED_DEFAULT}",
    desktop_telemetry="",
    application_choice_names=(Application.DESKTOP.name,),
)

INFREQUENT_USER_NEED_DEFAULT_HAS_PIN = NimbusTargetingConfig(
    name="Infrequent user (need default, has pin)",
    slug="infrequent_user_need_default_has_pin",
    description="Between 1 & 6 days activity in past 28 days need default w/ pin",
    targeting=f"{INFREQUENT_USER_NEED_DEFAULT.targeting} && {TARGETING_HAS_PIN}",
    desktop_telemetry="",
    application_choice_names=(Application.DESKTOP.name,),
)

INFREQUENT_USER_HAS_DEFAULT_NEED_PIN = NimbusTargetingConfig(
    name="Infrequent user (has default, need pin)",
    slug="infrequent_user_has_default_need_pin",
    description="Between 1 & 6 days activity in past 28 days w/ default need pin",
    targeting=f"{INFREQUENT_USER_NEED_PIN.targeting} && isDefaultBrowser",
    desktop_telemetry="",
    application_choice_names=(Application.DESKTOP.name,),
)

INFREQUENT_WIN_USER_NEED_PIN = NimbusTargetingConfig(
    name="Infrequent Windows user (need pin)",
    slug="infrequent_windows_user_need_pin",
    description="Between 1 and 6 days of activity in the past 28 days needing pin on Win",
    targeting=f"{INFREQUENT_USER_NEED_PIN.targeting} && os.isWindows",
    desktop_telemetry="",
    application_choice_names=(Application.DESKTOP.name,),
)

INFREQUENT_WIN_USER_URIS = NimbusTargetingConfig(
    name="Infrequent Windows 1903+ user (need default)",
    slug="infrequent_win_user_uris",
    description="Infrequent non default users of past 28 days, on Windows 1903+",
    targeting=f"{INFREQUENT_USER_NEED_DEFAULT.targeting} && {TARGETING_WIN1903}",
    desktop_telemetry="",
    application_choice_names=(Application.DESKTOP.name,),
)

CASUAL_USER_URIS = NimbusTargetingConfig(
    name="Casual user (uris)",
    slug="casual_user_uris",
    description="Between 7 and 13 days of activity in the past 28 days",
    targeting=f"{TARGETING_STICKY} || {TARGETING_PROFILE28DAYS} && "
    "userMonthlyActivity|length >= 7 && userMonthlyActivity|length <= 13",
    desktop_telemetry="",
    application_choice_names=(Application.DESKTOP.name,),
)

CASUAL_USER_NEED_PIN = NimbusTargetingConfig(
    name="Casual user (need pin)",
    slug="casual_user_need_pin",
    description="Between 7 and 13 days of activity in the past 28 days needing pin",
    targeting=f"{CASUAL_USER_URIS.targeting} && doesAppNeedPin",
    desktop_telemetry="",
    application_choice_names=(Application.DESKTOP.name,),
)

CASUAL_USER_NEED_DEFAULT = NimbusTargetingConfig(
    name="Casual user (need default)",
    slug="casual_user_need_default",
    description="Between 7 and 14 days of activity in the past 28 days needing default",
    targeting=f"{CASUAL_USER_URIS.targeting} && {TARGETING_NEED_DEFAULT}",
    desktop_telemetry="",
    application_choice_names=(Application.DESKTOP.name,),
)

CASUAL_USER_NEED_DEFAULT_HAS_PIN = NimbusTargetingConfig(
    name="Casual user (need default, has pin)",
    slug="casual_user_need_default_has_pin",
    description="Between 7 and 14 days of activity in past 28 days need default w/ pin",
    targeting=f"{CASUAL_USER_NEED_DEFAULT.targeting} && {TARGETING_HAS_PIN}",
    desktop_telemetry="",
    application_choice_names=(Application.DESKTOP.name,),
)

CASUAL_USER_HAS_DEFAULT_NEED_PIN = NimbusTargetingConfig(
    name="Casual user (has default, need pin)",
    slug="casual_user_has_default_need_pin",
    description="Between 7 and 14 days of activity in past 28 days w/ default need pin",
    targeting=f"{CASUAL_USER_NEED_PIN.targeting} && isDefaultBrowser",
    desktop_telemetry="",
    application_choice_names=(Application.DESKTOP.name,),
)

REGULAR_USER_URIS = NimbusTargetingConfig(
    name="Regular user (uris)",
    slug="regular_user_uris",
    description="Between 14 and 20 days of activity in the past 28 days",
    targeting=f"{TARGETING_STICKY} || {TARGETING_PROFILE28DAYS} && "
    "userMonthlyActivity|length >= 14 && userMonthlyActivity|length <= 20",
    desktop_telemetry="",
    application_choice_names=(Application.DESKTOP.name,),
)

REGULAR_USER_NEED_PIN = NimbusTargetingConfig(
    name="Regular user (need pin)",
    slug="regular_user_need_pin",
    description="Between 14 and 20 days of activity in the past 28 days needing pin",
    targeting=f"{REGULAR_USER_URIS.targeting} && doesAppNeedPin",
    desktop_telemetry="",
    application_choice_names=(Application.DESKTOP.name,),
)

REGULAR_USER_NEED_DEFAULT = NimbusTargetingConfig(
    name="Regular user (need default)",
    slug="regular_user_need_default",
    description="Between 14 and 20 days of activity in the past 28 days needing default",
    targeting=f"{REGULAR_USER_URIS.targeting} && {TARGETING_NEED_DEFAULT}",
    desktop_telemetry="",
    application_choice_names=(Application.DESKTOP.name,),
)

REGULAR_USER_NEED_DEFAULT_HAS_PIN = NimbusTargetingConfig(
    name="Regular user (need default, has pin)",
    slug="regular_user_need_default_has_pin",
    description="Between 14 and 20 days of activity in past 28 days need default w/ pin",
    targeting=f"{REGULAR_USER_NEED_DEFAULT.targeting} && {TARGETING_HAS_PIN}",
    desktop_telemetry="",
    application_choice_names=(Application.DESKTOP.name,),
)

REGULAR_USER_HAS_DEFAULT_NEED_PIN = NimbusTargetingConfig(
    name="Regular user (has default, need pin)",
    slug="regular_user_has_default_need_pin",
    description="Between 14 and 20 days of activity in past 28 days w/ default need pin",
    targeting=f"{REGULAR_USER_NEED_PIN.targeting} && isDefaultBrowser",
    desktop_telemetry="",
    application_choice_names=(Application.DESKTOP.name,),
)

REGULAR_USER_USES_FXA = NimbusTargetingConfig(
    name="Regular user (uses Firefox Accounts)",
    slug="regular_user_uses_fxa",
    description="Between 14 and 20 days of activity in the past 28 days signed in to FxA",
    targeting=f"{REGULAR_USER_URIS.targeting} && isFxAEnabled && usesFirefoxSync",
    desktop_telemetry="",
    application_choice_names=(Application.DESKTOP.name,),
)

CORE_USER_URIS = NimbusTargetingConfig(
    name="Core user (uris)",
    slug="core_user_uris",
    description="At least 21 days of activity in the past 28 days",
    targeting=f"{TARGETING_STICKY} || {TARGETING_PROFILE28DAYS} && "
    "userMonthlyActivity|length >= 21",
    desktop_telemetry="",
    application_choice_names=(Application.DESKTOP.name,),
)

CORE_USER_NEED_PIN = NimbusTargetingConfig(
    name="Core user (need pin)",
    slug="core_user_need_pin",
    description="At least 21 days of activity in the past 28 days needing pin",
    targeting=f"{CORE_USER_URIS.targeting} && doesAppNeedPin",
    desktop_telemetry="",
    application_choice_names=(Application.DESKTOP.name,),
)

CORE_USER_NEED_DEFAULT = NimbusTargetingConfig(
    name="Core user (need default)",
    slug="core_user_need_default",
    description="At least 21 days of activity in the past 28 days needing default",
    targeting=f"{CORE_USER_URIS.targeting} && {TARGETING_NEED_DEFAULT}",
    desktop_telemetry="",
    application_choice_names=(Application.DESKTOP.name,),
)

CORE_USER_NEED_DEFAULT_HAS_PIN = NimbusTargetingConfig(
    name="Core user (need default, has pin)",
    slug="core_user_need_default_has_pin",
    description="At least 21 days of activity in past 28 days need default w/ pin",
    targeting=f"{CORE_USER_NEED_DEFAULT.targeting} && {TARGETING_HAS_PIN}",
    desktop_telemetry="",
    application_choice_names=(Application.DESKTOP.name,),
)

CORE_USER_HAS_DEFAULT_NEED_PIN = NimbusTargetingConfig(
    name="Core user (has default, need pin)",
    slug="core_user_has_default_need_pin",
    description="At least 21 days of activity in past 28 days w/ default need pin",
    targeting=f"{CORE_USER_NEED_PIN.targeting} && isDefaultBrowser",
    desktop_telemetry="",
    application_choice_names=(Application.DESKTOP.name,),
)

TARGETING_POCKET_COMMON = NimbusTargetingConfig(
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
    application_choice_names=(Application.DESKTOP.name,),
)

TARGETING_PIP_NEVER_USED = NimbusTargetingConfig(
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
    application_choice_names=(Application.DESKTOP.name,),
)

TARGETING_PIP_NEVER_USED_STICKY = NimbusTargetingConfig(
    name="PiP Never Used (Sticky)",
    slug="pip_never_used_sticky",
    description="Users that have never used Picture in Picture, with sticky enrollment",
    targeting="(({pip}) || ({sticky}))".format(
        pip=TARGETING_PIP_NEVER_USED.targeting,
        sticky=TARGETING_STICKY,
    ),
    desktop_telemetry="",
    application_choice_names=(Application.DESKTOP.name,),
)


class NimbusConstants(object):
    class Status(models.TextChoices):
        DRAFT = "Draft"
        PREVIEW = "Preview"
        LIVE = "Live"
        COMPLETE = "Complete"

    class PublishStatus(models.TextChoices):
        IDLE = "Idle"
        REVIEW = "Review"
        APPROVED = "Approved"
        WAITING = "Waiting"

    class ConclusionRecommendation(models.TextChoices):
        RERUN = "RERUN", "Rerun"
        GRADUATE = "GRADUATE", "Graduate"
        CHANGE_COURSE = "CHANGE_COURSE", "Change course"
        STOP = "STOP", "Stop"
        FOLLOWUP = "FOLLOWUP", "Run follow ups"

    Application = Application

    VALID_STATUS_TRANSITIONS = {
        Status.DRAFT: (Status.PREVIEW,),
        Status.PREVIEW: (Status.DRAFT,),
    }
    STATUS_ALLOWS_UPDATE = (Status.DRAFT,)

    # Valid status_next values for given status values
    VALID_STATUS_NEXT_VALUES = {
        Status.DRAFT: (None, Status.LIVE),
        Status.PREVIEW: (None, Status.LIVE),
        Status.LIVE: (None, Status.LIVE, Status.COMPLETE),
    }

    VALID_PUBLISH_STATUS_TRANSITIONS = {
        PublishStatus.IDLE: (PublishStatus.REVIEW, PublishStatus.APPROVED),
        PublishStatus.REVIEW: (
            PublishStatus.IDLE,
            PublishStatus.APPROVED,
        ),
    }
    PUBLISH_STATUS_ALLOWS_UPDATE = (PublishStatus.IDLE,)

    STATUS_UPDATE_EXEMPT_FIELDS = (
        "is_archived",
        "publish_status",
        "status_next",
        "status",
        "takeaways_summary",
        "conclusion_recommendation",
    )

    ARCHIVE_UPDATE_EXEMPT_FIELDS = (
        "is_archived",
        "changelog_message",
    )

    APPLICATION_CONFIGS = {
        Application.DESKTOP: APPLICATION_CONFIG_DESKTOP,
        Application.FENIX: APPLICATION_CONFIG_FENIX,
        Application.IOS: APPLICATION_CONFIG_IOS,
        Application.FOCUS_ANDROID: APPLICATION_CONFIG_FOCUS_ANDROID,
        Application.KLAR_ANDROID: APPLICATION_CONFIG_KLAR_ANDROID,
        Application.FOCUS_IOS: APPLICATION_CONFIG_FOCUS_IOS,
        Application.KLAR_IOS: APPLICATION_CONFIG_KLAR_IOS,
    }

    Channel = Channel

    class DocumentationLink(models.TextChoices):
        DS_JIRA = "DS_JIRA", "Data Science Jira Ticket"
        DESIGN_DOC = "DESIGN_DOC", "Experiment Design Document"
        ENG_TICKET = "ENG_TICKET", "Engineering Ticket (Bugzilla/Jira/GitHub)"

    class Version(models.TextChoices):
        @staticmethod
        def parse(version_str):
            return version.parse(version_str.replace("!", "0"))

        NO_VERSION = ""
        FIREFOX_11 = "11.!"
        FIREFOX_12 = "12.!"
        FIREFOX_13 = "13.!"
        FIREFOX_14 = "14.!"
        FIREFOX_15 = "15.!"
        FIREFOX_16 = "16.!"
        FIREFOX_17 = "17.!"
        FIREFOX_18 = "18.!"
        FIREFOX_19 = "19.!"
        FIREFOX_20 = "20.!"
        FIREFOX_21 = "21.!"
        FIREFOX_22 = "22.!"
        FIREFOX_23 = "23.!"
        FIREFOX_24 = "24.!"
        FIREFOX_25 = "25.!"
        FIREFOX_26 = "26.!"
        FIREFOX_27 = "27.!"
        FIREFOX_28 = "28.!"
        FIREFOX_29 = "29.!"
        FIREFOX_30 = "30.!"
        FIREFOX_31 = "31.!"
        FIREFOX_32 = "32.!"
        FIREFOX_33 = "33.!"
        FIREFOX_34 = "34.!"
        FIREFOX_35 = "35.!"
        FIREFOX_36 = "36.!"
        FIREFOX_37 = "37.!"
        FIREFOX_38 = "38.!"
        FIREFOX_39 = "39.!"
        FIREFOX_40 = "40.!"
        FIREFOX_41 = "41.!"
        FIREFOX_42 = "42.!"
        FIREFOX_43 = "43.!"
        FIREFOX_44 = "44.!"
        FIREFOX_45 = "45.!"
        FIREFOX_46 = "46.!"
        FIREFOX_47 = "47.!"
        FIREFOX_48 = "48.!"
        FIREFOX_49 = "49.!"
        FIREFOX_50 = "50.!"
        FIREFOX_51 = "51.!"
        FIREFOX_52 = "52.!"
        FIREFOX_53 = "53.!"
        FIREFOX_54 = "54.!"
        FIREFOX_55 = "55.!"
        FIREFOX_56 = "56.!"
        FIREFOX_57 = "57.!"
        FIREFOX_58 = "58.!"
        FIREFOX_59 = "59.!"
        FIREFOX_60 = "60.!"
        FIREFOX_61 = "61.!"
        FIREFOX_62 = "62.!"
        FIREFOX_63 = "63.!"
        FIREFOX_64 = "64.!"
        FIREFOX_65 = "65.!"
        FIREFOX_66 = "66.!"
        FIREFOX_67 = "67.!"
        FIREFOX_68 = "68.!"
        FIREFOX_69 = "69.!"
        FIREFOX_70 = "70.!"
        FIREFOX_71 = "71.!"
        FIREFOX_72 = "72.!"
        FIREFOX_73 = "73.!"
        FIREFOX_74 = "74.!"
        FIREFOX_75 = "75.!"
        FIREFOX_76 = "76.!"
        FIREFOX_77 = "77.!"
        FIREFOX_78 = "78.!"
        FIREFOX_79 = "79.!"
        FIREFOX_80 = "80.!"
        FIREFOX_81 = "81.!"
        FIREFOX_82 = "82.!"
        FIREFOX_83 = "83.!"
        FIREFOX_84 = "84.!"
        FIREFOX_85 = "85.!"
        FIREFOX_86 = "86.!"
        FIREFOX_87 = "87.!"
        FIREFOX_88 = "88.!"
        FIREFOX_89 = "89.!"
        FIREFOX_90 = "90.!"
        FIREFOX_91 = "91.!"
        FIREFOX_92 = "92.!"
        FIREFOX_9201 = "92.0.1"
        FIREFOX_93 = "93.!"
        FIREFOX_94 = "94.!"
        FIREFOX_95 = "95.!"
        FIREFOX_96 = "96.!"
        FIREFOX_9601 = "96.0.1"
        FIREFOX_9602 = "96.0.2"
        FIREFOX_97 = "97.!"
        FIREFOX_98 = "98.!"
        FIREFOX_9830 = "98.3.0"
        FIREFOX_99 = "99.!"
        FIREFOX_9910 = "99.1.0"
        FIREFOX_100 = "100.!"
        FIREFOX_101 = "101.!"
        FIREFOX_102 = "102.!"
        FIREFOX_103 = "103.!"
        FIREFOX_104 = "104.!"
        FIREFOX_105 = "105.!"
        FIREFOX_106 = "106.!"
        FIREFOX_107 = "107.!"
        FIREFOX_108 = "108.!"
        FIREFOX_109 = "109.!"
        FIREFOX_110 = "110.!"
        FIREFOX_111 = "111.!"
        FIREFOX_112 = "112.!"
        FIREFOX_113 = "113.!"
        FIREFOX_114 = "114.!"
        FIREFOX_115 = "115.!"
        FIREFOX_116 = "116.!"
        FIREFOX_117 = "117.!"
        FIREFOX_118 = "118.!"
        FIREFOX_119 = "119.!"
        FIREFOX_120 = "120.!"

    class EmailType(models.TextChoices):
        EXPERIMENT_END = "experiment end"
        ENROLLMENT_END = "enrollment end"

    EMAIL_EXPERIMENT_END_SUBJECT = "Action required: Please turn off your Experiment"
    EMAIL_ENROLLMENT_END_SUBJECT = "Action required: Please end experiment enrollment"

    TARGETING_VERSION = "version|versionCompare('{version}') >= 0"
    TARGETING_CHANNEL = 'browserSettings.update.channel == "{channel}"'

    TARGETING_CONFIGS = {
        TARGETING_NO_TARGETING.slug: TARGETING_NO_TARGETING,
        TARGETING_FIRST_RUN.slug: TARGETING_FIRST_RUN,
        TARGETING_FIRST_RUN_CHROME_ATTRIBUTION.slug: (
            TARGETING_FIRST_RUN_CHROME_ATTRIBUTION
        ),
        TARGETING_FIRST_RUN_WINDOWS_1903_NEWER.slug: (
            TARGETING_FIRST_RUN_WINDOWS_1903_NEWER
        ),
        TARGETING_HOMEPAGE_GOOGLE.slug: TARGETING_HOMEPAGE_GOOGLE,
        TARGETING_URLBAR_FIREFOX_SUGGEST.slug: TARGETING_URLBAR_FIREFOX_SUGGEST,
        TARGETING_MAC_ONLY.slug: TARGETING_MAC_ONLY,
        TARGETING_NO_ENTERPRISE.slug: TARGETING_NO_ENTERPRISE,
        TARGETING_FX95_DESKTOP_USERS.slug: TARGETING_FX95_DESKTOP_USERS,
        TARGETING_NOT_TCP_STUDY.slug: TARGETING_NOT_TCP_STUDY,
        TARGETING_NOT_TCP_STUDY_FIRST_RUN.slug: TARGETING_NOT_TCP_STUDY_FIRST_RUN,
        TARGETING_WINDOWS_WITH_USERCHOICE.slug: TARGETING_WINDOWS_WITH_USERCHOICE,
        TARGETING_WINDOWS_WITH_USERCHOICE_FIRST_RUN.slug: (
            TARGETING_WINDOWS_WITH_USERCHOICE_FIRST_RUN
        ),
        TARGETING_MOBILE_NEW_USER.slug: TARGETING_MOBILE_NEW_USER,
        TARGETING_MOBILE_RECENTLY_UPDATED.slug: TARGETING_MOBILE_RECENTLY_UPDATED,
        TARGETING_NO_ENTERPRISE_OR_PAST_VPN.slug: TARGETING_NO_ENTERPRISE_OR_PAST_VPN,
        TARGETING_NO_ENTERPRISE_OR_RECENT_VPN.slug: TARGETING_NO_ENTERPRISE_OR_RECENT_VPN,
        INFREQUENT_USER_URIS.slug: INFREQUENT_USER_URIS,
        INFREQUENT_USER_NEED_PIN.slug: INFREQUENT_USER_NEED_PIN,
        INFREQUENT_USER_NEED_DEFAULT.slug: INFREQUENT_USER_NEED_DEFAULT,
        INFREQUENT_USER_NEED_DEFAULT_HAS_PIN.slug: INFREQUENT_USER_NEED_DEFAULT_HAS_PIN,
        INFREQUENT_USER_HAS_DEFAULT_NEED_PIN.slug: INFREQUENT_USER_HAS_DEFAULT_NEED_PIN,
        INFREQUENT_WIN_USER_NEED_PIN.slug: INFREQUENT_WIN_USER_NEED_PIN,
        INFREQUENT_WIN_USER_URIS.slug: INFREQUENT_WIN_USER_URIS,
        CASUAL_USER_URIS.slug: CASUAL_USER_URIS,
        CASUAL_USER_NEED_PIN.slug: CASUAL_USER_NEED_PIN,
        CASUAL_USER_NEED_DEFAULT.slug: CASUAL_USER_NEED_DEFAULT,
        CASUAL_USER_NEED_DEFAULT_HAS_PIN.slug: CASUAL_USER_NEED_DEFAULT_HAS_PIN,
        CASUAL_USER_HAS_DEFAULT_NEED_PIN.slug: CASUAL_USER_HAS_DEFAULT_NEED_PIN,
        REGULAR_USER_URIS.slug: REGULAR_USER_URIS,
        REGULAR_USER_NEED_PIN.slug: REGULAR_USER_NEED_PIN,
        REGULAR_USER_NEED_DEFAULT.slug: REGULAR_USER_NEED_DEFAULT,
        REGULAR_USER_NEED_DEFAULT_HAS_PIN.slug: REGULAR_USER_NEED_DEFAULT_HAS_PIN,
        REGULAR_USER_HAS_DEFAULT_NEED_PIN.slug: REGULAR_USER_HAS_DEFAULT_NEED_PIN,
        REGULAR_USER_USES_FXA.slug: REGULAR_USER_USES_FXA,
        CORE_USER_URIS.slug: CORE_USER_URIS,
        CORE_USER_NEED_PIN.slug: CORE_USER_NEED_PIN,
        CORE_USER_NEED_DEFAULT.slug: CORE_USER_NEED_DEFAULT,
        CORE_USER_NEED_DEFAULT_HAS_PIN.slug: CORE_USER_NEED_DEFAULT_HAS_PIN,
        CORE_USER_HAS_DEFAULT_NEED_PIN.slug: CORE_USER_HAS_DEFAULT_NEED_PIN,
        TARGETING_POCKET_COMMON.slug: TARGETING_POCKET_COMMON,
        TARGETING_PIP_NEVER_USED.slug: TARGETING_PIP_NEVER_USED,
        TARGETING_PIP_NEVER_USED_STICKY.slug: TARGETING_PIP_NEVER_USED_STICKY,
    }

    class TargetingConfig(models.TextChoices):
        NO_TARGETING = TARGETING_NO_TARGETING.slug, TARGETING_NO_TARGETING.name
        TARGETING_FIRST_RUN = TARGETING_FIRST_RUN.slug, TARGETING_FIRST_RUN.name
        TARGETING_FIRST_RUN_CHROME_ATTRIBUTION = (
            TARGETING_FIRST_RUN_CHROME_ATTRIBUTION.slug
        ), TARGETING_FIRST_RUN_CHROME_ATTRIBUTION.name
        TARGETING_FIRST_RUN_WINDOWS_1903_NEWER = (
            TARGETING_FIRST_RUN_WINDOWS_1903_NEWER.slug
        ), TARGETING_FIRST_RUN_WINDOWS_1903_NEWER.name
        TARGETING_HOMEPAGE_GOOGLE = (
            TARGETING_HOMEPAGE_GOOGLE.slug,
            TARGETING_HOMEPAGE_GOOGLE.name,
        )
        TARGETING_URLBAR_FIREFOX_SUGGEST = (
            TARGETING_URLBAR_FIREFOX_SUGGEST.slug,
            TARGETING_URLBAR_FIREFOX_SUGGEST.name,
        )
        TARGETING_MAC_ONLY = (TARGETING_MAC_ONLY.slug, TARGETING_MAC_ONLY.name)
        TARGETING_NO_ENTERPRISE = (
            TARGETING_NO_ENTERPRISE.slug,
            TARGETING_NO_ENTERPRISE.name,
        )
        TARGETING_FX95_DESKTOP_USERS = (
            TARGETING_FX95_DESKTOP_USERS.slug,
            TARGETING_FX95_DESKTOP_USERS.name,
        )
        TARGETING_NOT_TCP_STUDY = (
            TARGETING_NOT_TCP_STUDY.slug,
            TARGETING_NOT_TCP_STUDY.name,
        )
        TARGETING_NOT_TCP_STUDY_FIRST_RUN = (
            TARGETING_NOT_TCP_STUDY_FIRST_RUN.slug,
            TARGETING_NOT_TCP_STUDY_FIRST_RUN.name,
        )
        TARGETING_WINDOWS_WITH_USERCHOICE = (
            TARGETING_WINDOWS_WITH_USERCHOICE.slug,
            TARGETING_WINDOWS_WITH_USERCHOICE.name,
        )
        TARGETING_WINDOWS_WITH_USERCHOICE_FIRST_RUN = (
            TARGETING_WINDOWS_WITH_USERCHOICE_FIRST_RUN.slug,
            TARGETING_WINDOWS_WITH_USERCHOICE_FIRST_RUN.name,
        )
        TARGETING_MOBILE_NEW_USER = (
            TARGETING_MOBILE_NEW_USER.slug,
            TARGETING_MOBILE_NEW_USER.name,
        )
        TARGETING_MOBILE_RECENTLY_UPDATED = (
            TARGETING_MOBILE_RECENTLY_UPDATED.slug,
            TARGETING_MOBILE_RECENTLY_UPDATED.name,
        )
        INFREQUENT_USER_URIS = (
            INFREQUENT_USER_URIS.slug,
            INFREQUENT_USER_URIS.name,
        )
        INFREQUENT_USER_NEED_PIN = (
            INFREQUENT_USER_NEED_PIN.slug,
            INFREQUENT_USER_NEED_PIN.name,
        )
        INFREQUENT_USER_NEED_DEFAULT = (
            INFREQUENT_USER_NEED_DEFAULT.slug,
            INFREQUENT_USER_NEED_DEFAULT.name,
        )
        INFREQUENT_WIN_USER_NEED_PIN = (
            INFREQUENT_WIN_USER_NEED_PIN.slug,
            INFREQUENT_WIN_USER_NEED_PIN.name,
        )
        INFREQUENT_USER_NEED_DEFAULT_HAS_PIN = (
            INFREQUENT_USER_NEED_DEFAULT_HAS_PIN.slug,
            INFREQUENT_USER_NEED_DEFAULT_HAS_PIN.name,
        )
        INFREQUENT_USER_HAS_DEFAULT_NEED_PIN = (
            INFREQUENT_USER_HAS_DEFAULT_NEED_PIN.slug,
            INFREQUENT_USER_HAS_DEFAULT_NEED_PIN.name,
        )
        INFREQUENT_WIN_USER_URIS = (
            INFREQUENT_WIN_USER_URIS.slug,
            INFREQUENT_WIN_USER_URIS.name,
        )
        CASUAL_USER_URIS = (
            CASUAL_USER_URIS.slug,
            CASUAL_USER_URIS.name,
        )
        CASUAL_USER_NEED_PIN = (
            CASUAL_USER_NEED_PIN.slug,
            CASUAL_USER_NEED_PIN.name,
        )
        CASUAL_USER_NEED_DEFAULT = (
            CASUAL_USER_NEED_DEFAULT.slug,
            CASUAL_USER_NEED_DEFAULT.name,
        )
        CASUAL_USER_NEED_DEFAULT_HAS_PIN = (
            CASUAL_USER_NEED_DEFAULT_HAS_PIN.slug,
            CASUAL_USER_NEED_DEFAULT_HAS_PIN.name,
        )
        CASUAL_USER_HAS_DEFAULT_NEED_PIN = (
            CASUAL_USER_HAS_DEFAULT_NEED_PIN.slug,
            CASUAL_USER_HAS_DEFAULT_NEED_PIN.name,
        )
        REGULAR_USER_URIS = (
            REGULAR_USER_URIS.slug,
            REGULAR_USER_URIS.name,
        )
        REGULAR_USER_NEED_PIN = (
            REGULAR_USER_NEED_PIN.slug,
            REGULAR_USER_NEED_PIN.name,
        )
        REGULAR_USER_NEED_DEFAULT = (
            REGULAR_USER_NEED_DEFAULT.slug,
            REGULAR_USER_NEED_DEFAULT.name,
        )
        REGULAR_USER_NEED_DEFAULT_HAS_PIN = (
            REGULAR_USER_NEED_DEFAULT_HAS_PIN.slug,
            REGULAR_USER_NEED_DEFAULT_HAS_PIN.name,
        )
        REGULAR_USER_HAS_DEFAULT_NEED_PIN = (
            REGULAR_USER_HAS_DEFAULT_NEED_PIN.slug,
            REGULAR_USER_HAS_DEFAULT_NEED_PIN.name,
        )
        REGULAR_USER_USES_FXA = (
            REGULAR_USER_USES_FXA.slug,
            REGULAR_USER_USES_FXA.name,
        )
        CORE_USER_URIS = (
            CORE_USER_URIS.slug,
            CORE_USER_URIS.name,
        )
        CORE_USER_NEED_PIN = (
            CORE_USER_NEED_PIN.slug,
            CORE_USER_NEED_PIN.name,
        )
        CORE_USER_NEED_DEFAULT = (
            CORE_USER_NEED_DEFAULT.slug,
            CORE_USER_NEED_DEFAULT.name,
        )
        CORE_USER_NEED_DEFAULT_HAS_PIN = (
            CORE_USER_NEED_DEFAULT_HAS_PIN.slug,
            CORE_USER_NEED_DEFAULT_HAS_PIN.name,
        )
        CORE_USER_HAS_DEFAULT_NEED_PIN = (
            CORE_USER_HAS_DEFAULT_NEED_PIN.slug,
            CORE_USER_HAS_DEFAULT_NEED_PIN.name,
        )
        TARGETING_NO_ENTERPRISE_OR_PAST_VPN = (
            TARGETING_NO_ENTERPRISE_OR_PAST_VPN.slug,
            TARGETING_NO_ENTERPRISE_OR_PAST_VPN.name,
        )
        TARGETING_NO_ENTERPRISE_OR_RECENT_VPN = (
            TARGETING_NO_ENTERPRISE_OR_RECENT_VPN.slug,
            TARGETING_NO_ENTERPRISE_OR_RECENT_VPN.name,
        )
        TARGETING_POCKET_COMMON = (
            TARGETING_POCKET_COMMON.slug,
            TARGETING_POCKET_COMMON.name,
        )
        TARGETING_PIP_NEVER_USED = (
            TARGETING_PIP_NEVER_USED.slug,
            TARGETING_PIP_NEVER_USED.name,
        )
        TARGETING_PIP_NEVER_USED_STICKY = (
            TARGETING_PIP_NEVER_USED_STICKY.slug,
            TARGETING_PIP_NEVER_USED_STICKY.name,
        )

    TARGETING_APPLICATION_SUPPORTED_VERSION = {
        Application.FENIX: Version.FIREFOX_98,
        Application.FOCUS_ANDROID: Version.FIREFOX_98,
        Application.IOS: Version.FIREFOX_98,
        Application.FOCUS_IOS: Version.FIREFOX_97,
    }

    # Telemetry systems including Firefox Desktop Telemetry v4 and Glean
    # have limits on the length of their unique identifiers, we should
    # limit the size of our slugs to the smallest limit, which is 80
    # for Firefox Desktop Telemetry v4.
    MAX_SLUG_LEN = 80

    MAX_DURATION = 1000

    # Bucket stuff
    BUCKET_TOTAL = 10000

    HYPOTHESIS_DEFAULT = """If we <do this/build this/create this change in the experiment> for <these users>, then we will see <this outcome>.
We believe this because we have observed <this> via <data source, UR, survey>.

Optional - We believe this outcome will <describe impact> on <core metric>
    """  # noqa

    MAX_PRIMARY_OUTCOMES = 2
    DEFAULT_PROPOSED_DURATION = 28
    DEFAULT_PROPOSED_ENROLLMENT = 7

    # Serializer validation errors
    ERROR_DUPLICATE_BRANCH_NAME = "Branch names must be unique."
    ERROR_SINGLE_BRANCH_FOR_ROLLOUT = "A rollout may have only a single reference branch"
    ERROR_DUPLICATE_BRANCH_FEATURE_VALUE = (
        "A branch can not have multiple configurations for the same feature"
    )
    ERROR_BRANCH_NO_VALUE = "A value must be supplied for an enabled feature."
    ERROR_BRANCH_NO_ENABLED = "Enabled must be specified to include a value."
    ERROR_REQUIRED_QUESTION = "This question may not be blank."
    ERROR_REQUIRED_FIELD = "This field may not be blank."
    ERROR_REQUIRED_FEATURE_CONFIG = (
        "You must select a feature configuration from the drop down."
    )
    ERROR_LAUNCHING_DISABLED = (
        "Launching experiments has been temporarily disabled by the site administrators."
    )
    ERROR_POPULATION_PERCENT_MIN = "Ensure this value is greater than or equal to 0.0001."
    ERROR_FIREFOX_VERSION_MIN = (
        "Ensure this value is less than or equal to the maximum version"
    )
    ERROR_FIREFOX_VERSION_MAX = (
        "Ensure this value is greater than or equal to the minimum version"
    )

    # Analysis can be computed starting the week after enrollment
    # completion for "week 1" of the experiment. However, an extra
    # buffer day is added for Jetstream to compute the results.
    DAYS_UNTIL_ANALYSIS = 8

    # As a buffer, continue to pull in analysis from Jetstream
    # for 3 days after an experiment is complete.
    DAYS_ANALYSIS_BUFFER = 3

    PUBLISHED_TARGETING_MISSING = "Published targeting JEXL not found"

    DEFAULT_REFERENCE_BRANCH_NAME = "Control"
    DEFAULT_TREATMENT_BRANCH_NAME = "Treatment A"
