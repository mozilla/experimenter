from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Optional

from django.conf import settings
from django.db import models
from mozilla_nimbus_schemas.experiments import RandomizationUnit
from packaging import version

if TYPE_CHECKING:  # pragma: no cover
    from experimenter.experiments.models import NimbusExperiment


class Channel(models.TextChoices):
    NO_CHANNEL = ""
    UNBRANDED = "default"
    NIGHTLY = "nightly"
    BETA = "beta"
    RELEASE = "release"
    ESR = "esr"
    TESTFLIGHT = "testflight"
    AURORA = "aurora"
    DEVELOPER = "developer"
    STAGING = "staging"
    PRODUCTION = "production"


class ChangeEventType(Enum):
    GENERAL = "GENERAL"
    CREATION = "CREATION"
    DETAILED = "DETAILED"
    STATE = "STATE"
    BOOLEAN = "BOOLEAN"


class RelationalFields:
    # This is a list of models whose field values are stored as reference keys
    # instead of actual values in the NimbusChangelog

    NATIVE_MODELS = [
        "countries",
        "locales",
        "languages",
        "required_experiments",
        "excluded_experiments",
    ]


BucketRandomizationUnit = models.TextChoices(
    "BucketRandomizationUnit", [(r.name, r.value) for r in RandomizationUnit]
)


class TargetingMultipleKintoCollectionsError(Exception):
    """An error that is raised when an experiment contains multiple features
    that each would require it to be published to different kinto
    collections.
    """


@dataclass
class ApplicationConfig:
    name: str
    slug: str
    app_name: str
    channel_app_id: dict[str, str]
    default_kinto_collection: str
    randomization_unit: str
    is_web: bool
    preview_collection: str
    kinto_collections_by_feature_id: Optional[dict[str, str]] = field(default=None)

    def get_kinto_collection_for(self, experiment: NimbusExperiment) -> str:
        # If the experiment in question contains any features in the feature to
        # collection map, then *all* features must be present in the map and
        # they all must point to the same collection.
        if self.kinto_collections_by_feature_id is not None:
            target_collections = {
                self.kinto_collections_by_feature_id.get(
                    feature.slug, self.default_kinto_collection
                )
                for feature in experiment.feature_configs.all()
            }

            if len(target_collections) == 1:
                return next(iter(target_collections))

            elif len(target_collections) > 1:
                raise TargetingMultipleKintoCollectionsError(
                    "Experiment targets multiple collections"
                )

        return self.default_kinto_collection

    @property
    def kinto_collections(self) -> set[str]:
        collections = {self.default_kinto_collection}
        if self.kinto_collections_by_feature_id is not None:
            collections.update(self.kinto_collections_by_feature_id.values())

        return collections


DESKTOP_PREFFLIPS_SLUG = "prefFlips"

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
        Channel.AURORA: "firefox-desktop",
    },
    default_kinto_collection=settings.KINTO_COLLECTION_NIMBUS_DESKTOP,
    randomization_unit=BucketRandomizationUnit.NORMANDY,
    is_web=False,
    kinto_collections_by_feature_id={
        DESKTOP_PREFFLIPS_SLUG: settings.KINTO_COLLECTION_NIMBUS_SECURE,
    },
    preview_collection=settings.KINTO_COLLECTION_NIMBUS_PREVIEW,
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
    default_kinto_collection=settings.KINTO_COLLECTION_NIMBUS_MOBILE,
    randomization_unit=BucketRandomizationUnit.NIMBUS,
    is_web=False,
    preview_collection=settings.KINTO_COLLECTION_NIMBUS_PREVIEW,
)

APPLICATION_CONFIG_IOS = ApplicationConfig(
    name="Firefox for iOS",
    slug="ios",
    app_name="firefox_ios",
    channel_app_id={
        Channel.DEVELOPER: "org.mozilla.ios.Fennec",
        Channel.BETA: "org.mozilla.ios.FirefoxBeta",
        Channel.RELEASE: "org.mozilla.ios.Firefox",
    },
    default_kinto_collection=settings.KINTO_COLLECTION_NIMBUS_MOBILE,
    randomization_unit=BucketRandomizationUnit.NIMBUS,
    is_web=False,
    preview_collection=settings.KINTO_COLLECTION_NIMBUS_PREVIEW,
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
    default_kinto_collection=settings.KINTO_COLLECTION_NIMBUS_MOBILE,
    randomization_unit=BucketRandomizationUnit.NIMBUS,
    is_web=False,
    preview_collection=settings.KINTO_COLLECTION_NIMBUS_PREVIEW,
)

APPLICATION_CONFIG_KLAR_ANDROID = ApplicationConfig(
    name="Klar for Android",
    slug="klar-android",
    app_name="klar_android",
    channel_app_id={
        Channel.RELEASE: "org.mozilla.klar",
    },
    default_kinto_collection=settings.KINTO_COLLECTION_NIMBUS_MOBILE,
    randomization_unit=BucketRandomizationUnit.NIMBUS,
    is_web=False,
    preview_collection=settings.KINTO_COLLECTION_NIMBUS_PREVIEW,
)


APPLICATION_CONFIG_FOCUS_IOS = ApplicationConfig(
    name="Focus for iOS",
    slug="focus-ios",
    app_name="focus_ios",
    channel_app_id={
        Channel.RELEASE: "org.mozilla.ios.Focus",
        Channel.TESTFLIGHT: "org.mozilla.ios.Focus",
    },
    default_kinto_collection=settings.KINTO_COLLECTION_NIMBUS_MOBILE,
    randomization_unit=BucketRandomizationUnit.NIMBUS,
    is_web=False,
    preview_collection=settings.KINTO_COLLECTION_NIMBUS_PREVIEW,
)

APPLICATION_CONFIG_KLAR_IOS = ApplicationConfig(
    name="Klar for iOS",
    slug="klar-ios",
    app_name="klar_ios",
    channel_app_id={
        Channel.RELEASE: "org.mozilla.ios.Klar",
        Channel.TESTFLIGHT: "org.mozilla.ios.Klar",
    },
    default_kinto_collection=settings.KINTO_COLLECTION_NIMBUS_MOBILE,
    randomization_unit=BucketRandomizationUnit.NIMBUS,
    is_web=False,
    preview_collection=settings.KINTO_COLLECTION_NIMBUS_PREVIEW,
)

APPLICATION_CONFIG_MONITOR_WEB = ApplicationConfig(
    name="Monitor Web",
    slug="monitor-web",
    app_name="monitor_cirrus",
    channel_app_id={
        Channel.STAGING: "monitor.cirrus",
        Channel.PRODUCTION: "monitor.cirrus",
    },
    default_kinto_collection=settings.KINTO_COLLECTION_NIMBUS_WEB,
    randomization_unit=BucketRandomizationUnit.USER_ID,
    is_web=True,
    preview_collection=settings.KINTO_COLLECTION_NIMBUS_WEB_PREVIEW,
)

APPLICATION_CONFIG_VPN_WEB = ApplicationConfig(
    name="VPN Web",
    slug="vpn-web",
    app_name="mozillavpn_backend_cirrus",
    channel_app_id={
        Channel.PRODUCTION: "mozillavpn_backend_cirrus",
    },
    default_kinto_collection=settings.KINTO_COLLECTION_NIMBUS_WEB,
    randomization_unit=BucketRandomizationUnit.USER_ID,
    is_web=True,
    preview_collection=settings.KINTO_COLLECTION_NIMBUS_WEB_PREVIEW,
)

APPLICATION_CONFIG_FXA_WEB = ApplicationConfig(
    name="Firefox Accounts Web",
    slug="fxa-web",
    app_name="accounts_cirrus",
    channel_app_id={
        Channel.PRODUCTION: "accounts.cirrus",
    },
    default_kinto_collection=settings.KINTO_COLLECTION_NIMBUS_WEB,
    randomization_unit=BucketRandomizationUnit.USER_ID,
    is_web=True,
    preview_collection=settings.KINTO_COLLECTION_NIMBUS_WEB_PREVIEW,
)

APPLICATION_CONFIG_DEMO_APP = ApplicationConfig(
    name="Demo App",
    slug="demo-app",
    app_name="demo_app",
    channel_app_id={
        Channel.BETA: "demo-app-beta",
        Channel.RELEASE: "demo-app-release",
    },
    default_kinto_collection=settings.KINTO_COLLECTION_NIMBUS_WEB,
    randomization_unit=BucketRandomizationUnit.USER_ID,
    is_web=True,
    preview_collection=settings.KINTO_COLLECTION_NIMBUS_WEB_PREVIEW,
)

NO_FEATURE_SLUG = [
    "no-feature-focus-android",
    "no-feature-klar-ios",
    "no-feature-focus-ios",
    "no-feature-klar-android",
    "no-feature-ios",
    "no-feature-fenix",
    "no-feature-firefox-desktop",
    "no-feature-monitor",
]


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
    MONITOR = (
        APPLICATION_CONFIG_MONITOR_WEB.slug,
        APPLICATION_CONFIG_MONITOR_WEB.name,
    )
    VPN = (
        APPLICATION_CONFIG_VPN_WEB.slug,
        APPLICATION_CONFIG_VPN_WEB.name,
    )
    FXA = (
        APPLICATION_CONFIG_FXA_WEB.slug,
        APPLICATION_CONFIG_FXA_WEB.name,
    )
    DEMO_APP = (APPLICATION_CONFIG_DEMO_APP.slug, APPLICATION_CONFIG_DEMO_APP.name)

    @staticmethod
    def is_sdk(application):
        return application != Application.DESKTOP

    @staticmethod
    def is_mobile(application):
        return application in (
            Application.FENIX,
            Application.IOS,
            Application.FOCUS_ANDROID,
            Application.KLAR_ANDROID,
            Application.FOCUS_IOS,
            Application.KLAR_IOS,
        )

    @staticmethod
    def is_web(application):
        return application in (
            Application.DEMO_APP,
            Application.MONITOR,
            Application.VPN,
            Application.FXA,
        )


class NimbusConstants:
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
        NONE = "NONE", "None"

    Application = Application

    class Type(models.TextChoices):
        EXPERIMENT = "Experiment"
        ROLLOUT = "Rollout"

    class Takeaways(models.TextChoices):
        QBR_LEARNING = "QBR Learning"
        DAU_GAIN = "Statistically significant DAU Gain"

    ARCHIVE_UPDATE_EXEMPT_FIELDS = (
        "is_archived",
        "changelog_message",
        "qa_status",
        "qa_comment",
    )

    class QAStatus(models.TextChoices):
        RED = "RED"
        YELLOW = "YELLOW"
        GREEN = "GREEN"
        NOT_SET = "NOT SET"

    APPLICATION_CONFIGS = {
        Application.DESKTOP: APPLICATION_CONFIG_DESKTOP,
        Application.FENIX: APPLICATION_CONFIG_FENIX,
        Application.IOS: APPLICATION_CONFIG_IOS,
        Application.FOCUS_ANDROID: APPLICATION_CONFIG_FOCUS_ANDROID,
        Application.KLAR_ANDROID: APPLICATION_CONFIG_KLAR_ANDROID,
        Application.FOCUS_IOS: APPLICATION_CONFIG_FOCUS_IOS,
        Application.KLAR_IOS: APPLICATION_CONFIG_KLAR_IOS,
        Application.MONITOR: APPLICATION_CONFIG_MONITOR_WEB,
        Application.VPN: APPLICATION_CONFIG_VPN_WEB,
        Application.FXA: APPLICATION_CONFIG_FXA_WEB,
        Application.DEMO_APP: APPLICATION_CONFIG_DEMO_APP,
    }

    ApplicationNameMap = models.TextChoices(
        "ApplicationNameMap", [(a.slug, a.app_name) for a in APPLICATION_CONFIGS.values()]
    )

    DESKTOP_PREFFLIPS_SLUG = DESKTOP_PREFFLIPS_SLUG

    Channel = Channel

    class DocumentationLink(models.TextChoices):
        DS_JIRA = "DS_JIRA", "Data Science Jira Ticket"
        DESIGN_DOC = "DESIGN_DOC", "Experiment Design Document"
        ENG_TICKET = "ENG_TICKET", "Engineering Ticket (Bugzilla/Jira/GitHub)"
        QA_TICKET = "QA_TICKET", "QA Testing Ticket (Bugzilla/Jira/Github)"

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
        FIREFOX_10301 = "103.0.1"
        FIREFOX_104 = "104.!"
        FIREFOX_105 = "105.!"
        FIREFOX_10501 = "105.0.1"
        FIREFOX_10502 = "105.0.2"
        FIREFOX_10503 = "105.0.3"
        FIREFOX_106 = "106.!"
        FIREFOX_10601 = "106.0.1"
        FIREFOX_10602 = "106.0.2"
        FIREFOX_107 = "107.!"
        FIREFOX_108 = "108.!"
        FIREFOX_109 = "109.!"
        FIREFOX_110 = "110.!"
        FIREFOX_111 = "111.!"
        FIREFOX_111_0_1 = "111.0.1"
        FIREFOX_112 = "112.!"
        FIREFOX_113 = "113.!"
        FIREFOX_113_0_1 = "113.0.1"
        FIREFOX_114 = "114.!"
        FIREFOX_114_3_0 = "114.3.0"
        FIREFOX_115 = "115.!"
        FIREFOX_115_0_2 = "115.0.2"
        FIREFOX_115_7 = "115.7.0"
        FIREFOX_116 = "116.!"
        FIREFOX_116_0_1 = "116.0.1"
        FIREFOX_116_2_0 = "116.2.0"
        FIREFOX_116_3_0 = "116.3.0"
        FIREFOX_117 = "117.!"
        FIREFOX_118 = "118.!"
        FIREFOX_118_0_1 = "118.0.1"
        FIREFOX_118_0_2 = "118.0.2"
        FIREFOX_119 = "119.!"
        FIREFOX_120 = "120.!"
        FIREFOX_121 = "121.!"
        FIREFOX_121_0_1 = "121.0.1"
        FIREFOX_122 = "122.!"
        FIREFOX_122_1_0 = "122.1.0"
        FIREFOX_122_2_0 = "122.2.0"
        FIREFOX_123 = "123.!"
        FIREFOX_123_0_1 = "123.0.1"
        FIREFOX_124 = "124.!"
        FIREFOX_124_2_0 = "124.2.0"
        FIREFOX_124_3_0 = "124.3.0"
        FIREFOX_125 = "125.!"
        FIREFOX_125_0_1 = "125.0.1"
        FIREFOX_125_0_2 = "125.0.2"
        FIREFOX_125_1_0 = "125.1.0"
        FIREFOX_125_2_0 = "125.2.0"
        FIREFOX_126 = "126.!"
        FIREFOX_126_1_0 = "126.1.0"
        FIREFOX_126_2_0 = "126.2.0"
        FIREFOX_127 = "127.!"
        FIREFOX_127_0_1 = "127.0.1"
        FIREFOX_127_0_2 = "127.0.2"
        FIREFOX_128 = "128.!"
        FIREFOX_129 = "129.!"
        FIREFOX_130 = "130.!"
        FIREFOX_130_0_1 = "130.0.1"
        FIREFOX_131 = "131.!"
        FIREFOX_131_B4 = "131.0b4"
        FIREFOX_131_0_3 = "131.0.3"
        FIREFOX_131_1_0 = "131.1.0"
        FIREFOX_131_2_0 = "131.2.0"
        FIREFOX_132 = "132.!"
        FIREFOX_132_B6 = "132.0b6"
        FIREFOX_133 = "133.!"
        FIREFOX_133_B8 = "133.0b8"
        FIREFOX_133_0_1 = "133.0.1"
        FIREFOX_134 = "134.!"
        FIREFOX_134_1_0 = "134.1.0"
        FIREFOX_135 = "135.!"
        FIREFOX_135_0_1 = "135.0.1"
        FIREFOX_135_1_0 = "135.1.0"
        FIREFOX_136 = "136.!"
        FIREFOX_137 = "137.!"
        FIREFOX_138 = "138.!"
        FIREFOX_139 = "139.!"
        FIREFOX_140 = "140.!"

    class EmailType(models.TextChoices):
        EXPERIMENT_END = "experiment end"
        ENROLLMENT_END = "enrollment end"

    class FirefoxLabsGroups(models.TextChoices):
        CUSTOMIZE_BROWSING = "experimental-features-group-customize-browsing"
        WEBPAGE_DISPLAY = "experimental-features-group-webpage-display"
        DEVELOPER_TOOLS = "experimental-features-group-developer-tools"

    EMAIL_EXPERIMENT_END_SUBJECT = "Action required: Please turn off your Experiment"
    EMAIL_ENROLLMENT_END_SUBJECT = "Action required: Please end experiment enrollment"

    LANGUAGES_APPLICATION_SUPPORTED_VERSION = {
        Application.FENIX: Version.FIREFOX_102,
        Application.FOCUS_ANDROID: Version.FIREFOX_102,
        Application.IOS: Version.FIREFOX_101,
        Application.FOCUS_IOS: Version.FIREFOX_101,
        Application.DEMO_APP: Version.NO_VERSION,
        Application.MONITOR: Version.NO_VERSION,
        Application.VPN: Version.NO_VERSION,
        Application.FXA: Version.NO_VERSION,
    }

    COUNTRIES_APPLICATION_SUPPORTED_VERSION = {
        Application.FENIX: Version.FIREFOX_102,
        Application.FOCUS_ANDROID: Version.FIREFOX_102,
        Application.IOS: Version.FIREFOX_101,
        Application.FOCUS_IOS: Version.FIREFOX_101,
        Application.DEMO_APP: Version.NO_VERSION,
        Application.MONITOR: Version.NO_VERSION,
        Application.VPN: Version.NO_VERSION,
        Application.FXA: Version.NO_VERSION,
    }

    FEATURE_ENABLED_MIN_UNSUPPORTED_VERSION = Version.FIREFOX_104
    ROLLOUT_LIVE_RESIZE_MIN_SUPPORTED_VERSION = {
        Application.DESKTOP: Version.FIREFOX_115,
        Application.FENIX: Version.FIREFOX_116,
        Application.FOCUS_ANDROID: Version.FIREFOX_116,
        Application.IOS: Version.FIREFOX_116,
        Application.FOCUS_IOS: Version.FIREFOX_116,
    }

    ROLLOUT_SUPPORT_VERSION = {
        Application.DESKTOP: Version.FIREFOX_105,
        Application.FENIX: Version.FIREFOX_105,
        Application.FOCUS_ANDROID: Version.FIREFOX_105,
        Application.IOS: Version.FIREFOX_105,
        Application.FOCUS_IOS: Version.FIREFOX_105,
    }

    LOCALIZATION_SUPPORTED_VERSION = {
        Application.DESKTOP: Version.FIREFOX_113,
    }

    MIN_VERSIONED_FEATURE_VERSION = {
        Application.DESKTOP: Version.FIREFOX_120,
        Application.FENIX: Version.FIREFOX_116,
        Application.FOCUS_ANDROID: Version.FIREFOX_116,
        Application.IOS: Version.FIREFOX_116,
        Application.FOCUS_IOS: Version.FIREFOX_116,
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
    ERROR_FIREFOX_VERSION_MIN_96 = "The minimum targetable Firefox version is 96"
    ERROR_FIREFOX_VERSION_MAX = (
        "Ensure this value is greater than or equal to the minimum version"
    )
    ERROR_BRANCH_SWAP = "You are trying to swap branch names. \
        Please choose another name for the branches."

    ERROR_BUCKET_EXISTS = "WARNING: A rollout already exists for this combination \
        of application, feature, channel, and advanced targeting! \
        If this rollout is launched, a client meeting the advanced targeting criteria \
        will be enrolled in one and not the other and \
        you will not be able to adjust the sizing for this rollout."

    ERROR_ROLLOUT_VERSION = (
        "WARNING: Adjusting the population size while the"
        "rollout is live is not supported for {application} versions under {version}."
    )

    ERROR_DESKTOP_LOCALIZATION_VERSION = (
        "Firefox version must be at least 113 for localized experiments."
    )

    ERROR_FIRST_RUN_RELEASE_DATE = (
        "This field is for first run experiments only. "
        "Are you missing your first run targeting?"
    )

    ERROR_NO_FLOATS_IN_FEATURE_VALUE = (
        "Feature values can not contain floats (ie numbers with decimal points)."
    )

    ERROR_EXCLUDED_REQUIRED_MUTUALLY_EXCLUSIVE = (
        "An experiment appears in both the list of required experiments and excluded "
        "experiments"
    )

    ERROR_EXCLUDED_REQUIRED_INCLUDES_SELF = (
        "This experiment cannot be included in the list of required or excluded "
        "experiments"
    )

    ERROR_EXCLUDED_REQUIRED_DIFFERENT_APPLICATION = (
        "'{slug}' is for a different application and cannot be required or excluded"
    )

    ERROR_EXCLUDED_REQUIRED_MIN_VERSION = (
        "Firefox version must be at least 116 for requiring or excluding other "
        "experiments"
    )

    ERROR_FML_VALIDATION = "Feature Manifest errors occurred during validation"

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

    L10N_MIN_STRING_ID_LEN = 9

    MIN_REQUIRED_VERSION = Version.FIREFOX_96

    EXCLUDED_REQUIRED_MIN_VERSION = Version.FIREFOX_116

    MULTIFEATURE_MAX_FEATURES = 20
    ERROR_MULTIFEATURE_TOO_MANY_FEATURES = (
        "Multi-feature experiments can only support up to 20 different features."
    )

    ERROR_FEATURE_CONFIG_UNSUPPORTED_IN_RANGE = (
        "Feature {feature_config} is not supported by any version in this range."
    )

    ERROR_FEATURE_CONFIG_UNSUPPORTED_IN_VERSIONS = (
        "In versions {versions}: Feature {feature_config} is not supported"
    )

    ERROR_FEATURE_VALUE_IN_VERSIONS = "In versions {versions}: {error}"
    WARNING_FEATURE_VALUE_IN_VERSIONS = "Warning: In versions {versions}: {warning}"

    WARNING_ROLLOUT_PREF_REENROLL = (
        "WARNING: One or more features of this rollouts sets prefs and this rollout is "
        "not configured to prevent pref conflicts. Users that change prefs set by this "
        "rollout will re-enroll in this rollout, which will result in overriding their "
        "changes."
    )

    # There is a maximum size for prefs that Desktop can write. It will warn at
    # 4KiB and hard error at 1MiB.
    # https://searchfox.org/mozilla-central/rev/6b8a3f804789fb865f42af54e9d2fef9dd3ec74d/modules/libpref/Preferences.cpp#161-164
    LARGE_PREF_WARNING_LEN = 4 * 1024
    LARGE_PREF_ERROR_LEN = 1024 * 1024

    WARNING_LARGE_PREF = (
        "The variable '{variable}' will cause Firefox to write a pref over "
        "4KB size because {reason}. This should be avoided if possible."
    )
    ERROR_LARGE_PREF = (
        "The variable '{variable}' will cause Firefox to write a pref over "
        "1MB in size because {reason}. This will cause errors in the client."
    )
    IS_EARLY_STARTUP_REASON = "the feature {feature} is marked isEarlyStartup"
    SET_PREF_REASON = "the variable is a setPref variable"

    ERROR_INCOMPATIBLE_FEATURES = (
        "These features are incompatible because this experiment would be "
        "published to multiple Remote Settings collections"
    )
    ERROR_FEATURE_TARGET_COLLECTION = (
        "Feature '{feature_id}' publishes to collection '{collection}'"
    )
    ERROR_CANNOT_PUBLISH_TO_PREVIEW = "This experiment cannot be published to preview."

    ERROR_DESKTOP_PREFFLIPS_CHANNEL_REQUIRED = (
        "A channel is required for using the prefFlips feature."
    )
    ERROR_DESKTOP_PREFFLIPS_128_ESR_ONLY = (
        "The prefFlips feature is only available on Firefox 128 on the ESR branch."
    )

    WARNING_PREF_FLIPS_PREF_CONTROLLED_BY_FEATURE = (
        "Pref '{pref}' is controlled by a variable in feature {feature_config_slug}'"
    )
    OBSERVATION = "Observation"
    ENROLLMENT = "Enrollment"


EXTERNAL_URLS = {
    "SIGNOFF_QA": "https://experimenter.info/qa-sign-off",
    "TRAINING_AND_PLANNING_DOC": "https://experimenter.info/for-product",
    "PREVIEW_LAUNCH_DOC": "https://mana.mozilla.org/wiki/display/FJT/Nimbus",
}


RISK_QUESTIONS = {
    "BRAND": (
        "If the public, users or press, were to discover this experiment and "
        "description, do you think it could negatively impact their perception "
        "of the brand?"
    ),
    "MESSAGE": ("Does your experiment include ANY messages? If yes, this requires the "),
    "PARTNER": (
        "Does this experiment rely on AI (e.g. ML, chatbot), impact or rely on a partner "
        "or outside company (e.g. Google, Amazon), or deliver any encryption or VPN?"
    ),
    "REVENUE": (
        "Does this experiment have a risk to negatively impact revenue "
        "(e.g. search, Pocket revenue)?"
    ),
}
