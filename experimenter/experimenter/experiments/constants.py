from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Optional

from django.conf import settings
from django.db import models
from mozilla_nimbus_schemas.experimenter_apis.experiments import RandomizationUnit
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
    AURORA = ("aurora", "Developer Edition")
    DEVELOPER = "developer"
    STAGING = "staging"
    PRODUCTION = "production"

    @staticmethod
    def get_icon_info(channel):
        from experimenter.nimbus_ui.constants import CHANNEL_ICON_MAP

        return CHANNEL_ICON_MAP.get(channel, CHANNEL_ICON_MAP[Channel.NO_CHANNEL])


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

    # A mapping of collections to features.
    target_collections: dict[str, str]

    def __init__(self, target_collections):
        super().__init__("Experiment targets multiple collections")
        self.target_collections = target_collections


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

    def get_kinto_collection_for_experiment(self, experiment: NimbusExperiment) -> str:
        if self.kinto_collections_by_feature_id is not None:
            return self.get_kinto_collection_for_feature_ids(
                [fc.slug for fc in experiment.feature_configs.all()],
                experiment.firefox_min_version,
            )

        return self.default_kinto_collection

    def get_kinto_collection_for_feature_ids(
        self, feature_ids: list[str], min_version: str | None
    ) -> str:
        if self.kinto_collections_by_feature_id is not None:
            target_collections = defaultdict(list)
            for feature_id in feature_ids:
                collection = self.kinto_collections_by_feature_id.get(
                    feature_id, self.default_kinto_collection
                )
                target_collections[collection].append(feature_id)

            if (
                len(target_collections) == 2
                and self.default_kinto_collection in target_collections
                and min_version
            ):
                min_required_ride_along_version = (
                    NimbusConstants
                    .MIN_ALTERNATE_COLLECTION_RIDE_ALONG_FEATURES_VERSION
                    .get(self.slug)
                )  # fmt: skip
                if (
                    min_required_ride_along_version is not None
                    and NimbusConstants.Version.parse(min_version)
                    >= NimbusConstants.Version.parse(min_required_ride_along_version)
                ):
                    del target_collections[self.default_kinto_collection]

            if len(target_collections) == 1:
                return next(iter(target_collections))
            elif len(target_collections) > 1:
                raise TargetingMultipleKintoCollectionsError(target_collections)

        return self.default_kinto_collection

    @property
    def kinto_collections(self) -> set[str]:
        collections = {self.default_kinto_collection}
        if self.kinto_collections_by_feature_id is not None:
            collections.update(self.kinto_collections_by_feature_id.values())

        return collections


DESKTOP_PREFFLIPS_SLUG = "prefFlips"
DESKTOP_NEWTAB_ADDON_SLUG = "newtabTrainhopAddon"

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
        DESKTOP_NEWTAB_ADDON_SLUG: settings.KINTO_COLLECTION_NIMBUS_SECURE,
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
        Channel.STAGING: "accounts.cirrus",
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

APPLICATION_CONFIG_EXPERIMENTER = ApplicationConfig(
    name="Experimenter",
    slug="experimenter",
    app_name="experimenter",
    channel_app_id={
        Channel.DEVELOPER: "experimenter.cirrus",
        Channel.STAGING: "experimenter.cirrus",
        Channel.PRODUCTION: "experimenter.cirrus",
    },
    default_kinto_collection=settings.KINTO_COLLECTION_NIMBUS_WEB,
    randomization_unit=BucketRandomizationUnit.USER_ID,
    is_web=True,
    preview_collection=settings.KINTO_COLLECTION_NIMBUS_WEB_PREVIEW,
)

APPLICATION_CONFIG_SUBPLAT = ApplicationConfig(
    name="Subplat Web",
    slug="subplat-web",
    app_name="subplat_cirrus",
    channel_app_id={
        Channel.DEVELOPER: "subscription.platform.backend.cirrus",
        Channel.STAGING: "subscription.platform.backend.cirrus",
        Channel.PRODUCTION: "subscription.platform.backend.cirrus",
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
    EXPERIMENTER = (
        APPLICATION_CONFIG_EXPERIMENTER.slug,
        APPLICATION_CONFIG_EXPERIMENTER.name,
    )
    SUBPLAT = (
        APPLICATION_CONFIG_SUBPLAT.slug,
        APPLICATION_CONFIG_SUBPLAT.name,
    )

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
            Application.EXPERIMENTER,
            Application.SUBPLAT,
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
        RED = "RED", "QA: Red"
        YELLOW = "YELLOW", "QA: Yellow"
        GREEN = "GREEN", "QA: Green"
        SELF_RED = "SELF RED", "Self QA: Red"
        SELF_YELLOW = "SELF YELLOW", "Self QA: Yellow"
        SELF_GREEN = "SELF GREEN", "Self QA: Green"
        NOT_SET = "NOT SET", "Not Set"

        @staticmethod
        def get_icon_info(status):
            from experimenter.nimbus_ui.constants import QA_STATUS_ICON_MAP

            return QA_STATUS_ICON_MAP.get(
                status, QA_STATUS_ICON_MAP[NimbusConstants.QAStatus.NOT_SET]
            )

    class QATestType(models.TextChoices):
        FULL = "FULL", "Full"
        SMOKE = "SMOKE", "Smoke"
        SELF = "SELF", "Self"
        REGRESSION = "REGRESSION", "Regression"

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
        Application.EXPERIMENTER: APPLICATION_CONFIG_EXPERIMENTER,
        Application.SUBPLAT: APPLICATION_CONFIG_SUBPLAT,
    }

    ApplicationNameMap = models.TextChoices(
        "ApplicationNameMap", [(a.slug, a.app_name) for a in APPLICATION_CONFIGS.values()]
    )

    DESKTOP_PREFFLIPS_SLUG = DESKTOP_PREFFLIPS_SLUG
    DESKTOP_NEWTAB_ADDON_SLUG = DESKTOP_NEWTAB_ADDON_SLUG

    Channel = Channel

    class DocumentationLink(models.TextChoices):
        DS_JIRA = "DS_JIRA", "Data Science Jira Ticket"
        DESIGN_DOC = "DESIGN_DOC", "Experiment Design Document"
        ENG_TICKET = "ENG_TICKET", "Engineering Ticket (Bugzilla/Jira/GitHub)"
        QA_TICKET = "QA_TICKET", "QA Testing Ticket (Bugzilla/Jira/Github)"
        OTHER = "OTHER", "Other"

    class HomeTypeChoices(models.TextChoices):
        ROLLOUT = "Rollout", "📈 Rollout"
        EXPERIMENT = "Experiment", "🔬 Experiment"
        LABS = "Labs", "🧪 Labs"

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
        FIREFOX_115_25 = "115.25.0"
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
        FIREFOX_128_12 = "128.12.0"
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
        FIREFOX_136_0_2 = "136.0.2"
        FIREFOX_137 = "137.!"
        FIREFOX_137_1_0 = "137.1.0"
        FIREFOX_137_2_0 = "137.2.0"
        FIREFOX_138 = "138.!"
        FIREFOX_138_B3 = "138.0b3"
        FIREFOX_138_1_0 = "138.1.0"
        FIREFOX_138_2_0 = "138.2.0"
        FIREFOX_138_0_3 = "138.0.3"
        FIREFOX_139 = "139.!"
        FIREFOX_139_1_0 = "139.1.0"
        FIREFOX_139_2_0 = "139.2.0"
        FIREFOX_139_0_4 = "139.0.4"
        FIREFOX_140 = "140.!"
        FIREFOX_140_0_1 = "140.0.1"
        FIREFOX_140_0_2 = "140.0.2"
        FIREFOX_140_0_3 = "140.0.3"
        FIREFOX_140_0_4 = "140.0.4"
        FIREFOX_140_1_0 = "140.1.0"
        FIREFOX_140_2_0 = "140.2.0"
        FIREFOX_140_3_0 = "140.3.0"
        FIREFOX_140_4_0 = "140.4.0"
        FIREFOX_141 = "141.!"
        FIREFOX_141_0_1 = "141.0.1"
        FIREFOX_141_0_2 = "141.0.2"
        FIREFOX_141_0_3 = "141.0.3"
        FIREFOX_141_0_4 = "141.0.4"
        FIREFOX_141_1_0 = "141.1.0"
        FIREFOX_141_2_0 = "141.2.0"
        FIREFOX_141_3_0 = "141.3.0"
        FIREFOX_141_4_0 = "141.4.0"
        FIREFOX_142 = "142.!"
        FIREFOX_142_0_1 = "142.0.1"
        FIREFOX_142_0_2 = "142.0.2"
        FIREFOX_142_0_3 = "142.0.3"
        FIREFOX_142_0_4 = "142.0.4"
        FIREFOX_142_1_0 = "142.1.0"
        FIREFOX_142_2_0 = "142.2.0"
        FIREFOX_142_3_0 = "142.3.0"
        FIREFOX_142_4_0 = "142.4.0"
        FIREFOX_143 = "143.!"
        FIREFOX_143_B3 = "143.0b3"
        FIREFOX_143_B4 = "143.0b4"
        FIREFOX_143_0_1 = "143.0.1"
        FIREFOX_143_0_2 = "143.0.2"
        FIREFOX_143_0_3 = "143.0.3"
        FIREFOX_143_0_4 = "143.0.4"
        FIREFOX_143_1_0 = "143.1.0"
        FIREFOX_143_1_1 = "143.1.1"
        FIREFOX_143_2_0 = "143.2.0"
        FIREFOX_143_3_0 = "143.3.0"
        FIREFOX_143_4_0 = "143.4.0"
        FIREFOX_144 = "144.!"
        FIREFOX_144_0_1 = "144.0.1"
        FIREFOX_144_0_2 = "144.0.2"
        FIREFOX_144_0_3 = "144.0.3"
        FIREFOX_144_0_4 = "144.0.4"
        FIREFOX_144_1_0 = "144.1.0"
        FIREFOX_144_2_0 = "144.2.0"
        FIREFOX_144_3_0 = "144.3.0"
        FIREFOX_144_4_0 = "144.4.0"
        FIREFOX_145 = "145.!"
        FIREFOX_145_0_1 = "145.0.1"
        FIREFOX_145_0_2 = "145.0.2"
        FIREFOX_145_0_3 = "145.0.3"
        FIREFOX_145_0_4 = "145.0.4"
        FIREFOX_145_1_0 = "145.1.0"
        FIREFOX_145_2_0 = "145.2.0"
        FIREFOX_145_3_0 = "145.3.0"
        FIREFOX_145_4_0 = "145.4.0"
        FIREFOX_146 = "146.!"
        FIREFOX_146_0_1 = "146.0.1"
        FIREFOX_146_0_2 = "146.0.2"
        FIREFOX_146_0_3 = "146.0.3"
        FIREFOX_146_0_4 = "146.0.4"
        FIREFOX_146_1_0 = "146.1.0"
        FIREFOX_146_2_0 = "146.2.0"
        FIREFOX_146_3_0 = "146.3.0"
        FIREFOX_146_4_0 = "146.4.0"
        FIREFOX_147 = "147.!"
        FIREFOX_147_0_1 = "147.0.1"
        FIREFOX_147_0_2 = "147.0.2"
        FIREFOX_147_0_3 = "147.0.3"
        FIREFOX_147_0_4 = "147.0.4"
        FIREFOX_147_1_0 = "147.1.0"
        FIREFOX_147_2_0 = "147.2.0"
        FIREFOX_147_3_0 = "147.3.0"
        FIREFOX_147_4_0 = "147.4.0"
        FIREFOX_148 = "148.!"
        FIREFOX_148_0_1 = "148.0.1"
        FIREFOX_148_0_2 = "148.0.2"
        FIREFOX_148_0_3 = "148.0.3"
        FIREFOX_148_0_4 = "148.0.4"
        FIREFOX_148_1_0 = "148.1.0"
        FIREFOX_148_2_0 = "148.2.0"
        FIREFOX_148_3_0 = "148.3.0"
        FIREFOX_148_4_0 = "148.4.0"
        FIREFOX_149 = "149.!"
        FIREFOX_149_0_1 = "149.0.1"
        FIREFOX_149_0_2 = "149.0.2"
        FIREFOX_149_0_3 = "149.0.3"
        FIREFOX_149_0_4 = "149.0.4"
        FIREFOX_149_1_0 = "149.1.0"
        FIREFOX_149_2_0 = "149.2.0"
        FIREFOX_149_3_0 = "149.3.0"
        FIREFOX_149_4_0 = "149.4.0"
        FIREFOX_150 = "150.!"
        FIREFOX_150_0_1 = "150.0.1"
        FIREFOX_150_0_2 = "150.0.2"
        FIREFOX_150_0_3 = "150.0.3"
        FIREFOX_150_0_4 = "150.0.4"
        FIREFOX_150_1_0 = "150.1.0"
        FIREFOX_150_2_0 = "150.2.0"
        FIREFOX_150_3_0 = "150.3.0"
        FIREFOX_150_4_0 = "150.4.0"
        FIREFOX_151 = "151.!"
        FIREFOX_151_0_1 = "151.0.1"
        FIREFOX_151_0_2 = "151.0.2"
        FIREFOX_151_0_3 = "151.0.3"
        FIREFOX_151_0_4 = "151.0.4"
        FIREFOX_151_1_0 = "151.1.0"
        FIREFOX_151_2_0 = "151.2.0"
        FIREFOX_151_3_0 = "151.3.0"
        FIREFOX_151_4_0 = "151.4.0"
        FIREFOX_152 = "152.!"
        FIREFOX_152_0_1 = "152.0.1"
        FIREFOX_152_0_2 = "152.0.2"
        FIREFOX_152_0_3 = "152.0.3"
        FIREFOX_152_0_4 = "152.0.4"
        FIREFOX_152_1_0 = "152.1.0"
        FIREFOX_152_2_0 = "152.2.0"
        FIREFOX_152_3_0 = "152.3.0"
        FIREFOX_152_4_0 = "152.4.0"
        FIREFOX_153 = "153.!"
        FIREFOX_153_0_1 = "153.0.1"
        FIREFOX_153_0_2 = "153.0.2"
        FIREFOX_153_0_3 = "153.0.3"
        FIREFOX_153_0_4 = "153.0.4"
        FIREFOX_153_1_0 = "153.1.0"
        FIREFOX_153_2_0 = "153.2.0"
        FIREFOX_153_3_0 = "153.3.0"
        FIREFOX_153_4_0 = "153.4.0"
        FIREFOX_154 = "154.!"
        FIREFOX_154_0_1 = "154.0.1"
        FIREFOX_154_0_2 = "154.0.2"
        FIREFOX_154_0_3 = "154.0.3"
        FIREFOX_154_0_4 = "154.0.4"
        FIREFOX_154_1_0 = "154.1.0"
        FIREFOX_154_2_0 = "154.2.0"
        FIREFOX_154_3_0 = "154.3.0"
        FIREFOX_154_4_0 = "154.4.0"
        FIREFOX_155 = "155.!"
        FIREFOX_155_0_1 = "155.0.1"
        FIREFOX_155_0_2 = "155.0.2"
        FIREFOX_155_0_3 = "155.0.3"
        FIREFOX_155_0_4 = "155.0.4"
        FIREFOX_155_1_0 = "155.1.0"
        FIREFOX_155_2_0 = "155.2.0"
        FIREFOX_155_3_0 = "155.3.0"
        FIREFOX_155_4_0 = "155.4.0"
        FIREFOX_156 = "156.!"
        FIREFOX_156_0_1 = "156.0.1"
        FIREFOX_156_0_2 = "156.0.2"
        FIREFOX_156_0_3 = "156.0.3"
        FIREFOX_156_0_4 = "156.0.4"
        FIREFOX_156_1_0 = "156.1.0"
        FIREFOX_156_2_0 = "156.2.0"
        FIREFOX_156_3_0 = "156.3.0"
        FIREFOX_156_4_0 = "156.4.0"
        FIREFOX_157 = "157.!"
        FIREFOX_157_0_1 = "157.0.1"
        FIREFOX_157_0_2 = "157.0.2"
        FIREFOX_157_0_3 = "157.0.3"
        FIREFOX_157_0_4 = "157.0.4"
        FIREFOX_157_1_0 = "157.1.0"
        FIREFOX_157_2_0 = "157.2.0"
        FIREFOX_157_3_0 = "157.3.0"
        FIREFOX_157_4_0 = "157.4.0"
        FIREFOX_158 = "158.!"
        FIREFOX_158_0_1 = "158.0.1"
        FIREFOX_158_0_2 = "158.0.2"
        FIREFOX_158_0_3 = "158.0.3"
        FIREFOX_158_0_4 = "158.0.4"
        FIREFOX_158_1_0 = "158.1.0"
        FIREFOX_158_2_0 = "158.2.0"
        FIREFOX_158_3_0 = "158.3.0"
        FIREFOX_158_4_0 = "158.4.0"
        FIREFOX_159 = "159.!"
        FIREFOX_159_0_1 = "159.0.1"
        FIREFOX_159_0_2 = "159.0.2"
        FIREFOX_159_0_3 = "159.0.3"
        FIREFOX_159_0_4 = "159.0.4"
        FIREFOX_159_1_0 = "159.1.0"
        FIREFOX_159_2_0 = "159.2.0"
        FIREFOX_159_3_0 = "159.3.0"
        FIREFOX_159_4_0 = "159.4.0"
        FIREFOX_160 = "160.!"
        FIREFOX_160_0_1 = "160.0.1"
        FIREFOX_160_0_2 = "160.0.2"
        FIREFOX_160_0_3 = "160.0.3"
        FIREFOX_160_0_4 = "160.0.4"
        FIREFOX_160_1_0 = "160.1.0"
        FIREFOX_160_2_0 = "160.2.0"
        FIREFOX_160_3_0 = "160.3.0"
        FIREFOX_160_4_0 = "160.4.0"

    class EmailType(models.TextChoices):
        EXPERIMENT_END = "experiment end"
        ENROLLMENT_END = "enrollment end"

    class FirefoxLabsGroups(models.TextChoices):
        CUSTOMIZE_BROWSING = "experimental-features-group-customize-browsing"
        WEBPAGE_DISPLAY = "experimental-features-group-webpage-display"
        DEVELOPER_TOOLS = "experimental-features-group-developer-tools"
        PRODUCTIVITY = "experimental-features-group-productivity"

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
        Application.EXPERIMENTER: Version.NO_VERSION,
        Application.SUBPLAT: Version.NO_VERSION,
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
        Application.EXPERIMENTER: Version.NO_VERSION,
        Application.SUBPLAT: Version.NO_VERSION,
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

    # As of Firefox 142, experiments that publish to alternate collections can
    # include features that are not exclusive to that collection. i.e., a
    # rollout can contain a newtabTrainhopAddon feature config and a messaging
    # feature config.
    MIN_ALTERNATE_COLLECTION_RIDE_ALONG_FEATURES_VERSION = {
        Application.DESKTOP: Version.FIREFOX_142,
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

    DAILY_ACTIVE_USERS = "client_level_daily_active_users_v2"
    DAYS_OF_USE = "days_of_use"
    RETENTION = "retained"
    SEARCH_COUNT = "search_count"

    DAU_METRIC = {
        "group": "other_metrics",
        "friendly_name": "Daily Active Users",
        "slug": DAILY_ACTIVE_USERS,
        "description": "Average number of client that sent a main ping per day.",
    }

    DOU_METRIC = {
        "group": "other_metrics",
        "friendly_name": "Days of Use",
        "slug": DAYS_OF_USE,
        "description": "Average number of days each client sent a main ping.",
    }

    KPI_METRICS = [
        {
            "group": "other_metrics",
            "friendly_name": "Retention",
            "slug": RETENTION,
            "description": "Percentage of users who returned to Firefox two weeks later.",
            "display_type": "percentage",
        },
        {
            "group": "search_metrics",
            "friendly_name": "Search Count",
            "slug": SEARCH_COUNT,
            "description": "Daily mean number of searches per user.",
        },
    ]

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
        "WARNING: Adjusting the population size while the "
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

    ERROR_PRIMARY_SECONDARY_OUTCOMES_INTERSECTION = (
        "Primary outcomes cannot overlap with secondary outcomes."
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

    ERROR_DESKTOP_PREFFLIPS_128_ESR_ONLY = (
        "The prefFlips feature is only available on Firefox 128 on the ESR branch."
    )
    ERROR_FEATURE_VALUE_DIFFERENT_VARIABLES = (
        "The same variables must be used in all branches for a feature. "
        "This branch is missing: {variables}"
    )

    WARNING_PREF_FLIPS_PREF_CONTROLLED_BY_FEATURE = (
        "Pref '{pref}' is controlled by a variable in feature {feature_config_slug}'"
    )
    OBSERVATION = "Observation"
    ENROLLMENT = "Enrollment"
    WHAT_TRAIN_IS_IT_NOW_URL = "https://whattrainisitnow.com/api/firefox/releases/"

    FIREFOX_LABS_MIN_VERSION = {
        Application.DESKTOP: Version.FIREFOX_137,
    }

    FIREFOX_LABS_GROUP_AVAILABILITY = {
        Application.DESKTOP: {
            FirefoxLabsGroups.CUSTOMIZE_BROWSING: Version.FIREFOX_137,
            FirefoxLabsGroups.WEBPAGE_DISPLAY: Version.FIREFOX_137,
            FirefoxLabsGroups.DEVELOPER_TOOLS: Version.FIREFOX_137,
            FirefoxLabsGroups.PRODUCTIVITY: Version.FIREFOX_143_B3,
        },
    }

    ERROR_FIREFOX_LABS_MIN_VERSION = (
        "Firefox Labs requires at least version "
        "{version.major}.{version.minor}.{version.micro}."
    )

    ERROR_FIREFOX_LABS_GROUP_MIN_VERSION = (
        "This group was added in Firefox version {version.major}.{version.minor}."
        "{version.micro}"
    )

    ERROR_FIREFOX_LABS_UNSUPPORTED_APPLICATION = (
        "This application does not support Firefox Labs."
    )

    ERROR_FIREFOX_LABS_DESCRIPTION_LINKS_JSON = (
        "Firefox Labs description links must be a JSON object or null."
    )
    ERROR_FIREFOX_LABS_DESCRIPTION_LINKS_HTTP_URLS = (
        "Firefox Labs description links values must be HTTP(S) URLs."
    )
    ERROR_FIREFOX_LABS_REQUIRED_FIELD = "This field is requried for Firefox Labs Opt-Ins."
    ERROR_FIREFOX_LABS_ROLLOUT_REQUIRED = "Firefox Labs opt-ins must be rollouts."


EXTERNAL_URLS = {
    "SIGNOFF_QA": "https://experimenter.info/qa-sign-off",
    "TRAINING_AND_PLANNING_DOC": "https://experimenter.info/for-product",
    "PREVIEW_LAUNCH_DOC": "https://experimenter.info/previewing-experiments",
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
