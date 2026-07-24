from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Optional

import packaging.version
from django.conf import settings
from django.db import models
from mozilla_nimbus_schemas.experimenter_apis.experiments import RandomizationUnit
from typing_extensions import sentinel

from experimenter.experiments.versions import Version

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
class FirefoxLabs:
    """Information about Firefox Labs support for a given application."""

    class Groups(models.TextChoices):
        CUSTOMIZE_BROWSING = "experimental-features-group-customize-browsing"
        WEBPAGE_DISPLAY = "experimental-features-group-webpage-display"
        DEVELOPER_TOOLS = "experimental-features-group-developer-tools"
        PRODUCTIVITY = "experimental-features-group-productivity"
        NEWTAB_WIDGETS = "experimental-features-group-newtab-widgets"

    #: This value indicates support for arbitrary description links.
    ARBITRARY_KEYS = sentinel("ARBITRARY_KEYS")

    #: The set of description links keys available to nimbus-sdk-based
    #: applications.
    SDK_DESCRIPTION_LINKS = ("feedback",)

    #: The minimum application version that supports Firefox Labs.
    min_supported_version: packaging.version.Version

    #: The available Firefox Labs groups for this application.
    #:
    #: A value of `None` indicates that the application does not support groups.
    #:
    #: Each group maps to the first version that it was available in.
    groups: dict[str, packaging.version.Version] | None

    #: The supported keys for `firefox_labs_description_keys`.
    #:
    #: Firefox Desktop supports arbitrary description links, but nimbus-sdk
    # based applications are limited to `SDK_DESCRIPTION_LINKS`.
    supported_description_links: tuple[str] | ARBITRARY_KEYS

    #: The `min_supported_version` field, but unparsed.
    #:
    #: It only exists for tests.
    _unparsed_min_supported_version: str

    #: This `groups` field, but unparsed.
    #:
    #: It only exists for tests.
    _unparsed_groups: dict[str, str] | None

    def __init__(
        self,
        *,
        min_supported_version: str,
        groups: dict[str, str] | None = None,
        supported_description_links: tuple[str] | ARBITRARY_KEYS = ARBITRARY_KEYS,
    ):
        self._unparsed_min_supported_version = min_supported_version
        self.min_supported_version = Version.parse(min_supported_version)

        if groups is None:
            self._unparsed_groups = self.groups = None
        else:
            self._unparsed_groups = groups
            self.groups = {
                group: Version.parse(min_supported_version)
                for (group, min_supported_version) in groups.items()
            }

        self.supported_description_links = supported_description_links

    @property
    def supports_groups(self) -> bool:
        """Whether this application supports the firefox_labs_groups field."""
        return self.groups is not None

    @property
    def required_fields(self) -> list[str]:
        """The required Firefox Labs fields for this application."""
        required_fields = ["firefox_labs_title", "firefox_labs_description"]

        if self.supports_groups:
            required_fields.append("firefox_labs_group")

        return required_fields

    @property
    def group_choices(self) -> list[tuple[str, str]]:
        """The available group choices for this application.

        If the application does not support groups, this will be an empty list.
        """
        if self.groups is None:  # pragma: no cover
            return []

        return [
            choice for choice in FirefoxLabs.Groups.choices if choice[0] in self.groups
        ]

    def available_groups_in_version(
        self,
        version: packaging.version.Version,
    ) -> list[str]:
        """Return the groups available in a given version."""
        if self.groups is None:  # pragma: no cover
            return []

        return [
            group
            for (group, min_required_version) in self.groups.items()
            if min_required_version <= version
        ]


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
    targeting_context_file_name: Optional[str] = field(default=None)

    #: The Firefox Labs configuration for the application.
    #:
    #: If None, this application will not support Firefox Labs.
    firefox_labs: FirefoxLabs | None = field(default=None)

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
DESKTOP_NEWTAB_TRAINHOP_SLUG = "newtabTrainhop"
DESKTOP_NEWTAB_ADDON_VERSION_ATTR = "newtabAddonVersion"

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
    targeting_context_file_name="TargetingContextRecorder.sys.mjs",
    firefox_labs=FirefoxLabs(
        min_supported_version=Version.FIREFOX_137,
        groups={
            FirefoxLabs.Groups.CUSTOMIZE_BROWSING: Version.FIREFOX_137,
            FirefoxLabs.Groups.WEBPAGE_DISPLAY: Version.FIREFOX_137,
            FirefoxLabs.Groups.DEVELOPER_TOOLS: Version.FIREFOX_137,
            FirefoxLabs.Groups.PRODUCTIVITY: Version.FIREFOX_143_B3,
            FirefoxLabs.Groups.NEWTAB_WIDGETS: Version.FIREFOX_151,
        },
    ),
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
    targeting_context_file_name="RecordedNimbusContext.kt",
    firefox_labs=FirefoxLabs(
        min_supported_version=Version.FIREFOX_154,
        supported_description_links=FirefoxLabs.SDK_DESCRIPTION_LINKS,
    ),
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
    targeting_context_file_name="RecordedNimbusContext.swift",
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
    "no-feature-ios",
    "no-feature-fenix",
    "no-feature-firefox-desktop",
    "no-feature-monitor",
]


class Application(models.TextChoices):
    DESKTOP = (APPLICATION_CONFIG_DESKTOP.slug, APPLICATION_CONFIG_DESKTOP.name)
    FENIX = (APPLICATION_CONFIG_FENIX.slug, APPLICATION_CONFIG_FENIX.name)
    IOS = (APPLICATION_CONFIG_IOS.slug, APPLICATION_CONFIG_IOS.name)
    MONITOR = (
        APPLICATION_CONFIG_MONITOR_WEB.slug,
        APPLICATION_CONFIG_MONITOR_WEB.name,
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
    def is_sdk(slug: str):
        return slug != Application.DESKTOP

    @staticmethod
    def is_mobile(slug: str):
        return slug in (
            Application.FENIX,
            Application.IOS,
        )

    @staticmethod
    def is_web(slug: str):
        return slug in (
            Application.DEMO_APP,
            Application.MONITOR,
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

        # This status applies only to rollouts, and indicates that the rollout has been
        # disabled. It is not a valid status for experiments.
        DISABLED = "Disabled"

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

    CHANGELOG_MESSAGE_ADMIN_EDIT = "Modified by an administrator."

    class ProjectImpact(models.TextChoices):
        HIGH = "HIGH"
        MODERATE = "MODERATE"
        TARGETED = "TARGETED"

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

    APPLICATION_CONFIGS = {
        Application.DESKTOP: APPLICATION_CONFIG_DESKTOP,
        Application.FENIX: APPLICATION_CONFIG_FENIX,
        Application.IOS: APPLICATION_CONFIG_IOS,
        Application.MONITOR: APPLICATION_CONFIG_MONITOR_WEB,
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
    DESKTOP_NEWTAB_TRAINHOP_SLUG = DESKTOP_NEWTAB_TRAINHOP_SLUG
    DESKTOP_NEWTAB_ADDON_VERSION_ATTR = DESKTOP_NEWTAB_ADDON_VERSION_ATTR

    MOBILE_MESSAGING_SLUG = "messaging"
    MOBILE_MESSAGING_MESSAGES_FIELD = "messages"
    MOBILE_MESSAGING_MESSAGE_EXPERIMENT_FIELD = "experiment"

    # https://searchfox.org/mozilla-mobile/rev/7d8e9f43399a128c5b31b306ef62d160d12bf525/application-services/components/nimbus/src/lib.rs#44
    MOBILE_MESSAGING_EXPERIMENT_PLACEHOLDER = "{experiment}"

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

    Version = Version

    class EmailType(models.TextChoices):
        EXPERIMENT_END = "experiment end"
        ENROLLMENT_END = "enrollment end"

    class AlertType(models.TextChoices):
        ANALYSIS_ERROR = "analysis_error", "Analysis Error"
        ANALYSIS_READY_DAILY = "analysis_ready_daily", "Daily Analysis Ready"
        ANALYSIS_READY_WEEKLY = "analysis_ready_weekly", "Weekly Analysis Ready"
        ANALYSIS_READY_OVERALL = "analysis_ready_overall", "Overall Analysis Ready"
        EXPERIMENT_LAUNCHED = "experiment_launched", "Experiment Launched"
        ENROLLMENT_HEALTHY = "enrollment_healthy", "Enrollment Healthy"
        LAUNCH_REQUEST = "launch_request", "Launch Request"
        UPDATE_REQUEST = "update_request", "Update Request"
        END_ENROLLMENT_REQUEST = "end_enrollment_request", "End Enrollment Request"
        END_EXPERIMENT_REQUEST = "end_experiment_request", "End Experiment Request"
        UNENROLLMENT_SPIKE = "unenrollment_spike", "Unenrollment Spike"
        SRM_MISMATCH = "srm_mismatch", "SRM Mismatch"
        ZERO_ENROLLMENT = "zero_enrollment", "Zero Enrollment"
        FEATURE_CONFLICT = "feature_conflict", "Feature Conflict"

    # Error types from Jetstream that are expected for non-analysis reasons and
    # don't want alerting
    IGNORABLE_ANALYSIS_ERROR_TYPES = {
        "EndedException",
        "NoEnrollmentPeriodException",
        "HighPopulationException",
        "EnrollmentLongerThanAnalysisException",
        "ExplicitSkipException",
        "NoStartDateException",
        "RolloutSkipException",
        "EnrollmentNotCompleteException",
        "PreconditionFailed",
        "UnsupportedApplicationException",
    }

    class AnalysisWindow(models.TextChoices):
        WEEKLY = "weekly", "Weekly"
        OVERALL = "overall", "Overall"

    FirefoxLabs = FirefoxLabs

    EMAIL_EXPERIMENT_END_SUBJECT = "Action required: Please turn off your Experiment"
    EMAIL_ENROLLMENT_END_SUBJECT = "Action required: Please end experiment enrollment"

    LANGUAGES_APPLICATION_SUPPORTED_VERSION = {
        Application.FENIX: Version.FIREFOX_102,
        Application.IOS: Version.FIREFOX_101,
        Application.DEMO_APP: Version.NO_VERSION,
        Application.MONITOR: Version.NO_VERSION,
        Application.FXA: Version.NO_VERSION,
        Application.EXPERIMENTER: Version.NO_VERSION,
        Application.SUBPLAT: Version.NO_VERSION,
    }

    COUNTRIES_APPLICATION_SUPPORTED_VERSION = {
        Application.FENIX: Version.FIREFOX_102,
        Application.IOS: Version.FIREFOX_101,
        Application.DEMO_APP: Version.NO_VERSION,
        Application.MONITOR: Version.NO_VERSION,
        Application.FXA: Version.NO_VERSION,
        Application.EXPERIMENTER: Version.NO_VERSION,
        Application.SUBPLAT: Version.NO_VERSION,
    }

    FEATURE_ENABLED_MIN_UNSUPPORTED_VERSION = Version.FIREFOX_104
    ROLLOUT_LIVE_RESIZE_MIN_SUPPORTED_VERSION = {
        Application.DESKTOP: Version.FIREFOX_115,
        Application.FENIX: Version.FIREFOX_116,
        Application.IOS: Version.FIREFOX_116,
    }

    LOCALIZATION_SUPPORTED_VERSION = {
        Application.DESKTOP: Version.FIREFOX_113,
    }

    MIN_VERSIONED_FEATURE_VERSION = {
        Application.DESKTOP: Version.FIREFOX_120,
        Application.FENIX: Version.FIREFOX_116,
        Application.IOS: Version.FIREFOX_116,
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
    RETENTION_3_DAYS = "active_in_last_3_days"
    RETENTION_3_DAYS_DESKTOP = "active_in_last_3_days_legacy"
    SEARCH_COUNT = "search_count"

    DAU_METRIC = {
        "group": "other_metrics",
        "slug": DAILY_ACTIVE_USERS,
    }

    DOU_METRIC = {
        "group": "other_metrics",
        "slug": DAYS_OF_USE,
    }

    KPI_METRICS = [
        {
            "group": "other_metrics",
            "slug": RETENTION,
            "display_type": "percentage",
        },
        {
            "group": "other_metrics",
            "friendly_name": "3-Day Retention",
            "slug": RETENTION_3_DAYS,
            "description": "Users who returned to Firefox within 3 days after enrollment.",  # noqa
            "display_type": "percentage",
        },
        {
            "group": "search_metrics",
            "slug": SEARCH_COUNT,
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
    ERROR_POPULATION_PERCENT_MIN = "Ensure this value is greater than or equal to 0.0001."
    ERROR_ROLLOUT_NO_PHASES = "Add at least one rollout phase to the schedule."
    ERROR_ROLLOUT_FIRST_PHASE_ZERO = (
        "The first rollout phase must have a population percent greater than 0."
    )
    ERROR_FIREFOX_VERSION_MIN = (
        "Ensure this value is less than or equal to the maximum version"
    )
    ERROR_FIREFOX_VERSION_MIN_SUPPORTED = "The minimum targetable Firefox version is 105"
    ERROR_FIREFOX_VERSION_MIN_148_FOR_AI_RISK = (
        "Experiments using AI features require Firefox version 148 or higher"
    )
    ERROR_FIREFOX_VERSION_MIN_151_FOR_AI_RISK_MOBILE = (
        "Mobile experiments using AI features require version 151 or higher"
    )
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

    MIN_REQUIRED_VERSION = Version.FIREFOX_105

    EXCLUDED_REQUIRED_MIN_VERSION = Version.FIREFOX_116

    AI_RISK_MIN_VERSION = Version.FIREFOX_148

    AI_RISK_MIN_VERSION_MOBILE = Version.FIREFOX_151

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

    ERROR_TARGETING_FIELD_UNSUPPORTED_IN_RANGE = (
        "Targeting field {field} is not supported by any version in this range."
    )

    ERROR_TARGETING_FIELD_UNSUPPORTED_IN_VERSIONS = (
        "In versions {versions}: Targeting field {field} is not supported"
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
    ERROR_NEWTAB_TRAINHOP_TARGETING_REQUIRES_FEATURE = (
        "Targeting the newtab addon version requires the "
        f"{DESKTOP_NEWTAB_TRAINHOP_SLUG} feature. You must select it from the "
        "feature configuration drop down on the Branches page."
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

    ERROR_FIREFOX_LABS_MIN_VERSION = (
        "Firefox Labs requires at least version "
        "{version.major}.{version.minor}.{version.micro}."
    )

    ERROR_FIREFOX_LABS_GROUP_MIN_VERSION = (
        "This group was added in Firefox version {version.major}.{version.minor}."
        "{version.micro}"
    )

    ERROR_FIREFOX_LABS_GROUPS_UNSUPPORTED = (
        "This application does not support Firefox Labs groups."
    )

    ERROR_FIREFOX_LABS_UNSUPPORTED_APPLICATION = (
        "This application does not support Firefox Labs."
    )

    ERROR_FIREFOX_LABS_UNKNOWN_GROUP = "This group is not supported"

    ERROR_FIREFOX_LABS_DESCRIPTION_LINKS_JSON = (
        "Firefox Labs description links must be a JSON object or null."
    )
    ERROR_FIREFOX_LABS_DESCRIPTION_LINKS_HTTP_URLS = (
        "Firefox Labs description links values must be HTTP(S) URLs."
    )
    ERROR_FIREFOX_LABS_DESCRIPTION_LINKS_UNSUPPORTED_KEYS = (
        "Firefox Labs only supports the following description links for this "
        "application: {keys}"
    )
    ERROR_FIREFOX_LABS_REQUIRED_FIELD = "This field is requried for Firefox Labs Opt-Ins."
    ERROR_FIREFOX_LABS_ROLLOUT_REQUIRED = "Firefox Labs opt-ins must be rollouts."

    ERROR_CANNOT_PAUSE_NOT_LIVE = "Cannot end enrollment: experiment is not live"
    ERROR_CANNOT_PAUSE_UNPUBLISHED = (
        "Cannot end enrollment: there are unpublished changes"
    )
    ERROR_CANNOT_PAUSE_PAUSED = "Cannot end enrollment: enrollment has already ended"
    ERROR_CANNOT_PAUSE_ROLLOUT = (
        "Cannot end enrollment: rollouts do not support this behaviour"
    )
    ERROR_CANNOT_PAUSE_INVALID = "Cannot end enrollment at this time"

    ERROR_CANNOT_PARSE_TARGETING = "Cannot parse targeting expression"

    ERROR_MOBILE_MESSAGING_EXPERIMENT_FIELD = (
        'The message "{message_id}" requires a "experiment" key with the '
        'value "{{experiment}}"'
    )

    # Analysis window to alert type mappings
    ANALYSIS_WINDOW_TO_ALERT_TYPE = {
        AnalysisWindow.WEEKLY: AlertType.ANALYSIS_READY_WEEKLY,
        AnalysisWindow.OVERALL: AlertType.ANALYSIS_READY_OVERALL,
    }

    EXPOSURE_CLIENT_CUTOFF = 10

    MONITORING_ALERT_MINIMUM_DAYS = 1
    ZERO_ENROLLMENT_DAYS_THRESHOLD = 3
    ZERO_ENROLLMENT_CLIENT_THRESHOLD = 1000
    FEATURE_CONFLICT_THRESHOLD = 0.25

    OVERALL_WINDOW_INDEX = "1"

    class FunnelStatus(models.TextChoices):
        ENROLLED = "Enrolled", "Enrolled"
        NOT_ENROLLED = "NotEnrolled", "Not Enrolled"
        DISQUALIFIED = "Disqualified", "Disqualified"
        WAS_ENROLLED = "WasEnrolled", "Graduated"

    class FunnelReason(models.TextChoices):
        QUALIFIED = "Qualified", "Qualified"
        OPT_IN = "OptIn", "Opt-In"
        NOT_TARGETED = "NotTargeted", "Not Targeted"
        ENROLLMENTS_PAUSED = "EnrollmentsPaused", "Enrollments Paused"
        OPT_OUT = "OptOut", "Opted Out"
        FEATURE_CONFLICT = "FeatureConflict", "Feature Conflict"
        NOT_SELECTED = "NotSelected", "Not Selected"
        UNENROLLED_IN_ANOTHER_PROFILE = (
            "UnenrolledInAnotherProfile",
            "Unenrolled in Another Profile",
        )
        ERROR = "Error", "Error"
        CHANGED_PREF = "ChangedPref", "Changed Pref"
        FORCE_ENROLLMENT = "ForceEnrollment", "Force Enrollment"
        MIGRATION = "Migration", "Migration"
        GRADUATED = "", "Graduated"

    class FunnelBgColor(models.TextChoices):
        SUCCESS = "success"
        SECONDARY = "secondary"
        WARNING = "warning"
        DANGER = "danger"
        DARK = "dark"

    class FunnelTextColor(models.TextChoices):
        WHITE = "white"
        DARK = "dark"


EXTERNAL_URLS = {
    "SIGNOFF_QA": "https://experimenter.info/workflow/risk-mitigation#qa-sign-off",
    "TRAINING_AND_PLANNING_DOC": "https://experimenter.info/getting-started/for-experiment-owners",
    "PREVIEW_LAUNCH_DOC": "https://experimenter.info/platform-guides/desktop/preview",
    "FEATURE_MONITORING_DOC": "https://experimenter.info/feature-monitoring",
    "METRIC_HUB_FEATMON_CONFIG": "https://github.com/mozilla/metric-hub/blob/main/featmon/firefox_desktop.toml",
    "FEATURE_MONITORING_EXAMPLE": "https://yardstick.mozilla.org/d/dtfz7xv/nimbus-feature-monitoring?orgId=1&var-feature_slug=newtabSponsoredContent&var-application=firefox_desktop&var-metric=All",
}


_S = NimbusConstants.FunnelStatus
_R = NimbusConstants.FunnelReason
_BG = NimbusConstants.FunnelBgColor
_TC = NimbusConstants.FunnelTextColor

# Maps (status, reason) → (label, bg_color, text_color). Insertion order defines display
# order. Statuses/reasons mirror Nimbus SDK enrollment.rs enums.
ENROLLMENT_FUNNEL_STAGES = {
    (_S.ENROLLED, _R.QUALIFIED): (_S.ENROLLED.label, _BG.SUCCESS, _TC.WHITE),
    (_S.ENROLLED, _R.OPT_IN): (
        f"{_S.ENROLLED.label} ({_R.OPT_IN.label})",
        _BG.SUCCESS,
        _TC.WHITE,
    ),
    (_S.NOT_ENROLLED, _R.NOT_TARGETED): (_R.NOT_TARGETED.label, _BG.SECONDARY, _TC.WHITE),
    (_S.NOT_ENROLLED, _R.ENROLLMENTS_PAUSED): (
        _R.ENROLLMENTS_PAUSED.label,
        _BG.SECONDARY,
        _TC.WHITE,
    ),
    (_S.NOT_ENROLLED, _R.OPT_OUT): (_R.OPT_OUT.label, _BG.WARNING, _TC.DARK),
    (_S.NOT_ENROLLED, _R.FEATURE_CONFLICT): (
        _R.FEATURE_CONFLICT.label,
        _BG.DANGER,
        _TC.WHITE,
    ),
    (_S.NOT_ENROLLED, _R.NOT_SELECTED): (_R.NOT_SELECTED.label, _BG.SECONDARY, _TC.WHITE),
    (_S.NOT_ENROLLED, _R.UNENROLLED_IN_ANOTHER_PROFILE): (
        _R.UNENROLLED_IN_ANOTHER_PROFILE.label,
        _BG.DARK,
        _TC.WHITE,
    ),
    (_S.DISQUALIFIED, _R.ERROR): (
        f"{_S.DISQUALIFIED.label} — {_R.ERROR.label}",
        _BG.DANGER,
        _TC.WHITE,
    ),
    (_S.DISQUALIFIED, _R.OPT_OUT): (
        f"{_S.DISQUALIFIED.label} — {_R.OPT_OUT.label}",
        _BG.WARNING,
        _TC.DARK,
    ),
    (_S.DISQUALIFIED, _R.CHANGED_PREF): (
        f"{_S.DISQUALIFIED.label} — {_R.CHANGED_PREF.label}",
        _BG.WARNING,
        _TC.DARK,
    ),
    (_S.DISQUALIFIED, _R.NOT_TARGETED): (
        f"{_S.DISQUALIFIED.label} — {_R.NOT_TARGETED.label}",
        _BG.SECONDARY,
        _TC.WHITE,
    ),
    (_S.DISQUALIFIED, _R.NOT_SELECTED): (
        f"{_S.DISQUALIFIED.label} — {_R.NOT_SELECTED.label}",
        _BG.SECONDARY,
        _TC.WHITE,
    ),
    (_S.DISQUALIFIED, _R.UNENROLLED_IN_ANOTHER_PROFILE): (
        f"{_S.DISQUALIFIED.label} — {_R.UNENROLLED_IN_ANOTHER_PROFILE.label}",
        _BG.DARK,
        _TC.WHITE,
    ),
    (_S.DISQUALIFIED, _R.FORCE_ENROLLMENT): (
        f"{_S.DISQUALIFIED.label} — {_R.FORCE_ENROLLMENT.label}",
        _BG.SECONDARY,
        _TC.WHITE,
    ),
    (_S.WAS_ENROLLED, _R.GRADUATED): (_S.WAS_ENROLLED.label, _BG.SECONDARY, _TC.WHITE),
    (_S.WAS_ENROLLED, _R.MIGRATION): (
        f"{_S.WAS_ENROLLED.label} — {_R.MIGRATION.label}",
        _BG.SECONDARY,
        _TC.WHITE,
    ),
}

RISK_QUESTIONS = {
    "BRAND": (
        "If the public, users or press, were to discover this experiment and "
        "description, do you think it could negatively impact their perception "
        "of the brand?"
    ),
    "MESSAGE": ("Does your experiment include ANY messages? If yes, this requires the "),
    "PARTNER": (
        "Does this experiment impact or rely on a partner "
        "or outside company (e.g. Google, Amazon), or deliver any encryption or VPN?"
    ),
    "REVENUE": (
        "Does this experiment have a risk to negatively impact revenue "
        "(e.g. search, Pocket revenue)?"
    ),
    "AI": "Does this experiment use any AI features/functionality?",
}
