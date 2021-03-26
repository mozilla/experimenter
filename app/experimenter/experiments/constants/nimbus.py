from dataclasses import dataclass

from django.conf import settings
from django.db import models


@dataclass
class NimbusTargetingConfig:
    name: str
    slug: str
    description: str
    targeting: str
    desktop_telemetry: str


TARGETING_ALL_ENGLISH = NimbusTargetingConfig(
    name="All English users",
    slug="all_english",
    description="All users in en-* locales.",
    targeting="localeLanguageCode == 'en'",
    desktop_telemetry="STARTS_WITH(environment.settings.locale, 'en')",
)

TARGETING_US_ONLY = NimbusTargetingConfig(
    name="US users (en)",
    slug="us_only",
    description="All users in the US with an en-* locale.",
    targeting="localeLanguageCode == 'en' && region == 'US'",
    desktop_telemetry=(
        "STARTS_WITH(environment.settings.locale, 'en') "
        "AND normalized_country_code = 'US'"
    ),
)

TARGETING_FIRST_RUN = NimbusTargetingConfig(
    name="First start-up users (en)",
    slug="first_run",
    description=("First start-up users (e.g. for about:welcome) with an en-* " "locale."),
    targeting=("{en} && (({is_first_startup} && {not_see_aw}) || {sticky})").format(
        en=TARGETING_ALL_ENGLISH.targeting,
        is_first_startup="isFirstStartup",
        not_see_aw="!('trailhead.firstrun.didSeeAboutWelcome'|preferenceValue)",
        sticky="experiment.slug in activeExperiments",
    ),
    desktop_telemetry=(
        "STARTS_WITH(environment.settings.locale, 'en') "
        "AND payload.info.profile_subsession_counter = 1"
    ),
)

TARGETING_FIRST_RUN_CHROME_ATTRIBUTION = NimbusTargetingConfig(
    name="First start-up users (en) from Chrome",
    slug="first_run_chrome",
    description=(
        "First start-up users (e.g. for about:welcome) who download Firefox "
        "from Chrome with an en-* locale."
    ),
    targeting=("{first_run} && attributionData.ua == 'chrome'").format(
        first_run=TARGETING_FIRST_RUN.targeting
    ),
    desktop_telemetry=(
        "{first_run} AND environment.settings.attribution.ua = 'chrome'"
    ).format(first_run=TARGETING_FIRST_RUN.desktop_telemetry),
)

TARGETING_FIRST_RUN_WINDOWS_1903_NEWER = NimbusTargetingConfig(
    name="First start-up users (en) on Windows 10 1903 (build 18362) or newer",
    slug="first_run_win1903",
    description=(
        "First start-up users (e.g. for about:welcome) on Win 18362+ with an en-* locale."
    ),
    targeting=("{first_run} && os.windowsBuildNumber >= 18362").format(
        first_run=TARGETING_FIRST_RUN.targeting
    ),
    desktop_telemetry=(
        "{first_run} AND environment.system.os.windows_build_number >= 18362"
    ).format(first_run=TARGETING_FIRST_RUN.desktop_telemetry),
)

TARGETING_HOMEPAGE_GOOGLE = NimbusTargetingConfig(
    name="Homepage set to google.com",
    slug="homepage_google_dot_com",
    description="US users (en) with their Homepage set to google.com",
    targeting=(
        "localeLanguageCode == 'en' && "
        "region == 'US' && "
        "!homePageSettings.isDefault && "
        "homePageSettings.isCustomUrl && "
        "homePageSettings.urls[.host == 'google.com']|length > 0"
    ),
    desktop_telemetry="",
)


class NimbusConstants(object):
    class Status(models.TextChoices):
        DRAFT = "Draft"
        PREVIEW = "Preview"
        REVIEW = "Review"
        ACCEPTED = "Accepted"
        LIVE = "Live"
        COMPLETE = "Complete"

    VALID_STATUS_TRANSITIONS = {
        Status.DRAFT: (
            Status.PREVIEW,
            Status.REVIEW,
        ),
        Status.PREVIEW: (
            Status.DRAFT,
            Status.REVIEW,
        ),
    }
    STATUS_ALLOWS_UPDATE = (Status.DRAFT,)

    class PublishStatus(models.TextChoices):
        IDLE = "Idle"
        REVIEW = "Review"
        APPROVED = "Approved"
        WAITING = "Waiting"

    VALID_PUBLISH_STATUS_TRANSITIONS = {
        PublishStatus.IDLE: (PublishStatus.REVIEW,),
        PublishStatus.REVIEW: (
            PublishStatus.IDLE,
            PublishStatus.APPROVED,
        ),
    }
    PUBLISH_STATUS_ALLOWS_UPDATE = (PublishStatus.IDLE,)

    class Application(models.TextChoices):
        DESKTOP = "firefox-desktop"
        FENIX = "fenix"

    FIREFOX_DESKTOP_APP_NAME = "firefox_desktop"

    APPLICATION_APP_NAME = {
        Application.DESKTOP: FIREFOX_DESKTOP_APP_NAME,
        Application.FENIX: Application.FENIX,
    }

    APP_NAME_APPLICATION = {v: k for k, v in APPLICATION_APP_NAME.items()}

    KINTO_APPLICATION_COLLECTION = {
        Application.DESKTOP: settings.KINTO_COLLECTION_NIMBUS_DESKTOP,
        Application.FENIX: settings.KINTO_COLLECTION_NIMBUS_MOBILE,
    }

    class Channel(models.TextChoices):
        NO_CHANNEL = ""
        UNBRANDED = "default"
        NIGHTLY = "nightly"
        BETA = "beta"
        RELEASE = "release"

    class FenixAppId(models.TextChoices):
        NIGHTLY = "org.mozilla.fenix"
        BETA = "org.mozilla.firefox.beta"
        RELEASE = "org.mozilla.firefox"

    CHANNEL_FENIX_APP_ID = {
        Channel.NIGHTLY: FenixAppId.NIGHTLY,
        Channel.BETA: FenixAppId.BETA,
        Channel.RELEASE: FenixAppId.RELEASE,
    }

    class DocumentationLink(models.TextChoices):
        DS_JIRA = "DS_JIRA", "Data Science Jira Ticket"
        DESIGN_DOC = "DESIGN_DOC", "Experiment Design Document"
        ENG_TICKET = "ENG_TICKET", "Engineering Ticket (Bugzilla/Jira/GitHub)"

    class Version(models.TextChoices):
        NO_VERSION = ""
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
        FIREFOX_93 = "93.!"
        FIREFOX_94 = "94.!"
        FIREFOX_95 = "95.!"
        FIREFOX_96 = "96.!"
        FIREFOX_97 = "97.!"
        FIREFOX_98 = "98.!"
        FIREFOX_99 = "99.!"
        FIREFOX_100 = "100.!"

    class EmailType(models.TextChoices):
        EXPERIMENT_END = "experiment end"

    class BucketRandomizationUnit(models.TextChoices):
        NORMANDY = "normandy_id"
        NIMBUS = "nimbus_id"

    APPLICATION_BUCKET_RANDOMIZATION_UNIT = {
        Application.DESKTOP: BucketRandomizationUnit.NORMANDY,
        Application.FENIX: BucketRandomizationUnit.NIMBUS,
    }

    EMAIL_EXPERIMENT_END_SUBJECT = "Action required: Please turn off your Experiment"

    TARGETING_VERSION = "version|versionCompare('{version}') >= 0"
    TARGETING_CHANNEL = 'browserSettings.update.channel == "{channel}"'

    TARGETING_CONFIGS = {
        TARGETING_ALL_ENGLISH.slug: TARGETING_ALL_ENGLISH,
        TARGETING_US_ONLY.slug: TARGETING_US_ONLY,
        TARGETING_FIRST_RUN.slug: TARGETING_FIRST_RUN,
        TARGETING_FIRST_RUN_CHROME_ATTRIBUTION.slug: (
            TARGETING_FIRST_RUN_CHROME_ATTRIBUTION
        ),
        TARGETING_FIRST_RUN_WINDOWS_1903_NEWER.slug: (
            TARGETING_FIRST_RUN_WINDOWS_1903_NEWER
        ),
        TARGETING_HOMEPAGE_GOOGLE.slug: TARGETING_HOMEPAGE_GOOGLE,
    }

    class TargetingConfig(models.TextChoices):
        NO_TARGETING = ""
        ALL_ENGLISH = TARGETING_ALL_ENGLISH.slug, TARGETING_ALL_ENGLISH.name
        US_ONLY = TARGETING_US_ONLY.slug, TARGETING_US_ONLY.name
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
