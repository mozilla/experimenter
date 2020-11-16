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
        "STARTS_WITH(environment.settings.locale, 'en') "
        "AND payload.info.profile_subsession_counter = 1"
        "AND environment.settings.attribution.ua = 'chrome'"
    ),
)


class NimbusConstants(object):
    class Status(models.TextChoices):
        DRAFT = "Draft"
        REVIEW = "Review"
        ACCEPTED = "Accepted"
        LIVE = "Live"
        COMPLETE = "Complete"

    class Application(models.TextChoices):
        DESKTOP = "firefox-desktop"
        FENIX = "fenix"

    KINTO_APPLICATION_COLLECTION = {
        Application.DESKTOP: settings.KINTO_COLLECTION_NIMBUS_DESKTOP,
        Application.FENIX: settings.KINTO_COLLECTION_NIMBUS_MOBILE,
    }

    class Channel(models.TextChoices):
        DESKTOP_BETA = "beta"
        DESKTOP_NIGHTLY = "nightly"
        DESKTOP_RELEASE = "release"
        DESKTOP_UNBRANDED = "default"
        FENIX_BETA = "org.mozilla.firefox.beta"
        FENIX_NIGHTLY = "org.mozilla.fenix"
        FENIX_RELEASE = "org.mozilla.firefox"

    ApplicationChannels = {
        Application.DESKTOP: [
            Channel.DESKTOP_UNBRANDED,
            Channel.DESKTOP_NIGHTLY,
            Channel.DESKTOP_BETA,
            Channel.DESKTOP_RELEASE,
        ],
        Application.FENIX: [
            Channel.FENIX_NIGHTLY,
            Channel.FENIX_BETA,
            Channel.FENIX_RELEASE,
        ],
    }

    class Version(models.TextChoices):
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

    class ProbeKind(models.TextChoices):
        EVENT = "event"
        SCALAR = "scalar"

    class EmailType(models.TextChoices):
        EXPERIMENT_END = "experiment end"

    EMAIL_EXPERIMENT_END_SUBJECT = "Action required: Please turn off your Experiment"

    TARGETING_VERSION = "version|versionCompare('{version}') >= 0"
    TARGETING_CHANNELS = "browserSettings.update.channel in {channels}"

    TARGETING_CONFIGS = {
        TARGETING_ALL_ENGLISH.slug: TARGETING_ALL_ENGLISH,
        TARGETING_US_ONLY.slug: TARGETING_US_ONLY,
        TARGETING_FIRST_RUN.slug: TARGETING_FIRST_RUN,
        TARGETING_FIRST_RUN_CHROME_ATTRIBUTION.slug: (
            TARGETING_FIRST_RUN_CHROME_ATTRIBUTION
        ),
    }

    class TargetingConfig(models.TextChoices):
        ALL_ENGLISH = TARGETING_ALL_ENGLISH.slug
        US_ONLY = TARGETING_US_ONLY.slug
        TARGETING_FIRST_RUN = TARGETING_FIRST_RUN.slug
        TARGETING_FIRST_RUN_CHROME_ATTRIBUTION = (
            TARGETING_FIRST_RUN_CHROME_ATTRIBUTION.slug
        )

    # Telemetry systems including Firefox Desktop Telemetry v4 and Glean
    # have limits on the length of their unique identifiers, we should
    # limit the size of our slugs to the smallest limit, which is 80
    # for Firefox Desktop Telemetry v4.
    MAX_SLUG_LEN = 80

    MAX_DURATION = 1000

    # Bucket stuff
    BUCKET_TOTAL = 10000
    BUCKET_RANDOMIZATION_UNIT = "normandy_id"

    HYPOTHESIS_DEFAULT = """If we <do this/build this/create this change in the experiment> for <these users>, then we will see <this outcome>.
We believe this because we have observed <this> via <data source, UR, survey>.

Optional - We believe this outcome will <describe impact> on <core metric>
    """  # noqa

    MAX_PRIMARY_PROBE_SETS = 2
