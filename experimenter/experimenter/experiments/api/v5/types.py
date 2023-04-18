import json

import graphene
from django.contrib.auth.models import User
from graphene_django import DjangoListField
from graphene_django.types import DjangoObjectType

from experimenter.base.models import Country, Language, Locale
from experimenter.experiments.api.v5.serializers import (
    NimbusReviewSerializer,
    TransitionConstants,
)
from experimenter.experiments.api.v6.serializers import NimbusExperimentSerializer
from experimenter.experiments.constants import NimbusConstants
from experimenter.experiments.models import (
    NimbusBranch,
    NimbusBranchFeatureValue,
    NimbusBranchScreenshot,
    NimbusChangeLog,
    NimbusDocumentationLink,
    NimbusExperiment,
    NimbusFeatureConfig,
)
from experimenter.outcomes import Outcomes
from experimenter.projects.models import Project


class NimbusExperimentStatusEnum(graphene.Enum):
    class Meta:
        enum = NimbusConstants.Status


class NimbusExperimentPublishStatusEnum(graphene.Enum):
    class Meta:
        enum = NimbusConstants.PublishStatus


class NimbusExperimentFirefoxVersionEnum(graphene.Enum):
    class Meta:
        enum = NimbusConstants.Version


class NimbusExperimentApplicationEnum(graphene.Enum):
    class Meta:
        enum = NimbusConstants.Application


class NimbusTypeEnum(graphene.Enum):
    class Meta:
        enum = NimbusConstants.Type


class NimbusExperimentChannelEnum(graphene.Enum):
    class Meta:
        enum = NimbusConstants.Channel


class NimbusExperimentConclusionRecommendationEnum(graphene.Enum):
    class Meta:
        enum = NimbusConstants.ConclusionRecommendation


class NimbusExperimentDocumentationLinkEnum(graphene.Enum):
    class Meta:
        enum = NimbusConstants.DocumentationLink


class ObjectField(graphene.Scalar):
    """Utilized to serialize out Serializer errors"""

    @staticmethod
    def serialize(dt):
        return dt


class NimbusLabelValueType(graphene.ObjectType):
    label = graphene.String()
    value = graphene.String()


class NimbusCountryType(DjangoObjectType):
    id = graphene.String(required=True)
    code = graphene.String(required=True)
    name = graphene.String(required=True)

    class Meta:
        model = Country
        fields = ("id", "code", "name")


class NimbusLocaleType(DjangoObjectType):
    id = graphene.String(required=True)
    code = graphene.String(required=True)
    name = graphene.String(required=True)

    class Meta:
        model = Locale
        fields = ("id", "code", "name")


class NimbusProjectType(DjangoObjectType):
    id = graphene.String()
    slug = graphene.String()
    name = graphene.String()

    class Meta:
        model = Project


class NimbusLanguageType(DjangoObjectType):
    id = graphene.String(required=True)
    code = graphene.String(required=True)
    name = graphene.String(required=True)

    class Meta:
        model = Language
        fields = ("id", "code", "name")


class NimbusUserType(DjangoObjectType):
    class Meta:
        model = User
        fields = ("id", "username", "first_name", "last_name", "email")


class NimbusExperimentApplicationConfigType(graphene.ObjectType):
    application = NimbusExperimentApplicationEnum()
    channels = graphene.List(NimbusLabelValueType)


class NimbusExperimentTargetingConfigType(graphene.ObjectType):
    label = graphene.String()
    value = graphene.String()
    application_values = graphene.List(graphene.String)
    description = graphene.String()
    sticky_required = graphene.Boolean()
    is_first_run_required = graphene.Boolean()


class NimbusFeatureConfigType(DjangoObjectType):
    id = graphene.Int()
    application = NimbusExperimentApplicationEnum()
    sets_prefs = graphene.Boolean()

    class Meta:
        model = NimbusFeatureConfig
        fields = (
            "application",
            "description",
            "id",
            "name",
            "owner_email",
            "sets_prefs",
            "schema",
            "slug",
            "enabled",
        )

    def resolve_sets_prefs(self, info):
        return bool(self.sets_prefs)


class NimbusBranchScreenshotType(DjangoObjectType):
    id = graphene.Int()
    description = graphene.String()
    image = graphene.String()

    class Meta:
        model = NimbusBranchScreenshot
        fields = ("id", "description", "image")

    def resolve_image(self, info):
        if self.image and self.image.name:
            return self.image.url


class NimbusBranchFeatureValueType(DjangoObjectType):
    id = graphene.Int()
    feature_config = graphene.Field(NimbusFeatureConfigType)
    value = graphene.String()

    class Meta:
        model = NimbusBranchFeatureValue
        fields = ("id", "feature_config", "value")


class NimbusBranchType(DjangoObjectType):
    id = graphene.Int(required=False)
    feature_value = graphene.String(required=False)
    feature_values = graphene.List(NimbusBranchFeatureValueType)
    screenshots = DjangoListField(NimbusBranchScreenshotType)

    class Meta:
        model = NimbusBranch
        fields = (
            "description",
            "feature_value",
            "feature_values",
            "id",
            "name",
            "ratio",
            "screenshots",
            "slug",
        )

    def resolve_feature_values(self, info):
        return self.feature_values.all()

    def resolve_feature_value(self, info):
        return (
            self.feature_values.exists()
            and self.feature_values.all().order_by("feature_config__slug").first().value
        ) or ""


class NimbusDocumentationLinkType(DjangoObjectType):
    title = NimbusExperimentDocumentationLinkEnum()

    class Meta:
        model = NimbusDocumentationLink
        fields = ("title", "link")


class NimbusOutcomeMetricType(graphene.ObjectType):
    slug = graphene.String()
    friendly_name = graphene.String()
    description = graphene.String()


class NimbusOutcomeType(graphene.ObjectType):
    friendly_name = graphene.String()
    slug = graphene.String()
    application = NimbusExperimentApplicationEnum()
    description = graphene.String()
    is_default = graphene.Boolean()
    metrics = graphene.List(NimbusOutcomeMetricType)


class NimbusReviewType(graphene.ObjectType):
    message = ObjectField()
    warnings = ObjectField()
    ready = graphene.Boolean()


class NimbusChangeLogType(DjangoObjectType):
    old_status = NimbusExperimentStatusEnum()
    old_status_next = NimbusExperimentStatusEnum()
    new_status = NimbusExperimentStatusEnum()
    new_status_next = NimbusExperimentStatusEnum()

    class Meta:
        model = NimbusChangeLog
        fields = (
            "changed_by",
            "changed_on",
            "experiment_data",
            "message",
            "new_status_next",
            "new_status",
            "old_status_next",
            "old_status",
        )


class NimbusSignoffRecommendationsType(graphene.ObjectType):
    qa_signoff = graphene.Boolean()
    vp_signoff = graphene.Boolean()
    legal_signoff = graphene.Boolean()


class NimbusStatusUpdateExemptFieldsType(graphene.ObjectType):
    all = graphene.Field(graphene.List(graphene.String))
    experiments = graphene.Field(graphene.List(graphene.String))
    rollouts = graphene.Field(graphene.List(graphene.String))

    def resolve_all(self, info):
        return TransitionConstants.STATUS_UPDATE_EXEMPT_FIELDS["all"]

    def resolve_experiments(self, info):
        return TransitionConstants.STATUS_UPDATE_EXEMPT_FIELDS["experiments"]

    def resolve_rollouts(self, info):
        return TransitionConstants.STATUS_UPDATE_EXEMPT_FIELDS["rollouts"]


class NimbusConfigurationType(graphene.ObjectType):
    application_configs = graphene.List(NimbusExperimentApplicationConfigType)
    applications = graphene.List(NimbusLabelValueType)
    channels = graphene.List(NimbusLabelValueType)
    countries = graphene.List(NimbusCountryType)
    documentation_link = graphene.List(NimbusLabelValueType)
    all_feature_configs = graphene.List(NimbusFeatureConfigType)
    firefox_versions = graphene.List(NimbusLabelValueType)
    hypothesis_default = graphene.String()
    locales = graphene.List(NimbusLocaleType)
    languages = graphene.List(NimbusLanguageType)
    projects = graphene.List(NimbusProjectType)
    max_primary_outcomes = graphene.Int()
    outcomes = graphene.List(NimbusOutcomeType)
    owners = graphene.List(NimbusUserType)
    targeting_configs = graphene.List(NimbusExperimentTargetingConfigType)
    conclusion_recommendations = graphene.List(NimbusLabelValueType)
    types = graphene.List(NimbusLabelValueType)
    status_update_exempt_fields = graphene.List(NimbusStatusUpdateExemptFieldsType)

    def _text_choices_to_label_value_list(self, text_choices):
        return [
            NimbusLabelValueType(
                label=text_choices[name].label,
                value=name,
            )
            for name in text_choices.names
        ]

    def resolve_applications(self, info):
        return self._text_choices_to_label_value_list(NimbusExperiment.Application)

    def resolve_channels(self, info):
        return self._text_choices_to_label_value_list(NimbusExperiment.Channel)

    def resolve_application_configs(self, info):
        configs = []
        for application in NimbusExperiment.Application:
            application_config = NimbusExperiment.APPLICATION_CONFIGS[application]
            configs.append(
                NimbusExperimentApplicationConfigType(
                    application=application,
                    channels=[
                        NimbusLabelValueType(label=channel.label, value=channel.name)
                        for channel in NimbusExperiment.Channel
                        if channel in application_config.channel_app_id
                    ],
                )
            )
        return configs

    def resolve_all_feature_configs(self, info):
        return NimbusFeatureConfig.objects.all().order_by("name")

    def resolve_firefox_versions(self, info):
        return NimbusConfigurationType.sort_version_choices(NimbusExperiment.Version)

    def resolve_conclusion_recommendations(self, info):
        return self._text_choices_to_label_value_list(
            NimbusExperiment.ConclusionRecommendation
        )

    @staticmethod
    def sort_version_choices(choices):
        sorted_versions = list(choices)[::-1]
        sorted_versions = [
            NimbusLabelValueType(
                label=name.label,
                value=name.label.replace(" ", "_").upper(),
            )
            for name in sorted_versions
        ]
        no_version_option = sorted_versions.pop()
        sorted_versions.insert(0, no_version_option)

        return sorted_versions

    def resolve_outcomes(self, info):
        return Outcomes.all()

    def resolve_owners(self, info):
        return (
            User.objects.filter(owned_nimbusexperiments__isnull=False)
            .distinct()
            .order_by("email")
        )

    def resolve_targeting_configs(self, info):
        return [
            NimbusExperimentTargetingConfigType(
                label=choice.label,
                value=choice.value,
                application_values=NimbusExperiment.TARGETING_CONFIGS[
                    choice.value
                ].application_choice_names,
                description=NimbusExperiment.TARGETING_CONFIGS[choice.value].description,
                sticky_required=NimbusExperiment.TARGETING_CONFIGS[
                    choice.value
                ].sticky_required,
                is_first_run_required=NimbusExperiment.TARGETING_CONFIGS[
                    choice.value
                ].is_first_run_required,
            )
            for choice in NimbusExperiment.TargetingConfig
        ]

    def resolve_hypothesis_default(self, info):
        return NimbusExperiment.HYPOTHESIS_DEFAULT

    def resolve_max_primary_outcomes(self, info):
        return NimbusExperiment.MAX_PRIMARY_OUTCOMES

    def resolve_documentation_link(self, info):
        return self._text_choices_to_label_value_list(NimbusExperiment.DocumentationLink)

    def resolve_locales(self, info):
        return Locale.objects.all().order_by("name")

    def resolve_countries(self, info):
        return Country.objects.all().order_by("name")

    def resolve_languages(self, info):
        return Language.objects.all().order_by("name")

    def resolve_projects(self, info):
        return Project.objects.all().order_by("name")

    def resolve_types(self, info):
        return self._text_choices_to_label_value_list(NimbusExperiment.Type)

    def resolve_status_update_exempt_fields(self, info):
        return [
            NimbusStatusUpdateExemptFieldsType(
                all=TransitionConstants.STATUS_UPDATE_EXEMPT_FIELDS["all"],
                experiments=TransitionConstants.STATUS_UPDATE_EXEMPT_FIELDS[
                    "experiments"
                ],
                rollouts=TransitionConstants.STATUS_UPDATE_EXEMPT_FIELDS["rollouts"],
            )
        ]


class NimbusExperimentType(DjangoObjectType):
    application = NimbusExperimentApplicationEnum()
    can_archive = graphene.Boolean()
    can_edit = graphene.Boolean()
    can_review = graphene.Boolean()
    changes = graphene.List(NimbusChangeLogType)
    channel = NimbusExperimentChannelEnum()
    computed_duration_days = graphene.Int()
    computed_end_date = graphene.DateTime()
    computed_enrollment_days = graphene.Int()
    computed_enrollment_end_date = graphene.DateTime()
    conclusion_recommendation = graphene.Field(
        NimbusExperimentConclusionRecommendationEnum
    )
    countries = graphene.List(graphene.NonNull(NimbusCountryType), required=True)
    documentation_links = DjangoListField(NimbusDocumentationLinkType)
    enrollment_end_date = graphene.DateTime()
    feature_config = graphene.Field(NimbusFeatureConfigType)
    feature_configs = graphene.List(NimbusFeatureConfigType)
    firefox_max_version = NimbusExperimentFirefoxVersionEnum()
    firefox_min_version = NimbusExperimentFirefoxVersionEnum()
    hypothesis = graphene.String()
    id = graphene.Int()
    is_archived = graphene.Boolean()
    is_rollout_dirty = graphene.Boolean()
    is_enrollment_pause_pending = graphene.Boolean()
    is_enrollment_paused = graphene.Boolean()
    is_rollout = graphene.Boolean()
    is_sticky = graphene.Boolean()
    jexl_targeting_expression = graphene.String()
    languages = graphene.List(graphene.NonNull(NimbusLanguageType), required=True)
    locales = graphene.List(graphene.NonNull(NimbusLocaleType), required=True)
    monitoring_dashboard_url = graphene.String()
    name = graphene.String(required=True)
    owner = graphene.Field(graphene.NonNull(NimbusUserType))
    parent = graphene.Field(lambda: NimbusExperimentType)
    population_percent = graphene.String()
    prevent_pref_conflicts = graphene.Boolean()
    primary_outcomes = graphene.List(graphene.String)
    projects = graphene.List(NimbusProjectType)
    public_description = graphene.String()
    publish_status = NimbusExperimentPublishStatusEnum()
    ready_for_review = graphene.Field(NimbusReviewType)
    recipe_json = graphene.String()
    reference_branch = graphene.Field(NimbusBranchType)
    rejection = graphene.Field(NimbusChangeLogType)
    results_expected_date = graphene.DateTime()
    results_ready = graphene.Boolean()
    review_request = graphene.Field(NimbusChangeLogType)
    review_url = graphene.String()
    risk_mitigation_link = graphene.String()
    rollout_monitoring_dashboard_url = graphene.String()
    secondary_outcomes = graphene.List(graphene.String)
    show_results_url = graphene.Boolean()
    signoff_recommendations = graphene.Field(NimbusSignoffRecommendationsType)
    slug = graphene.String(required=True)
    start_date = graphene.DateTime()
    status = NimbusExperimentStatusEnum()
    status_next = NimbusExperimentStatusEnum()
    targeting_config = graphene.List(NimbusExperimentTargetingConfigType)
    targeting_config_slug = graphene.String()
    timeout = graphene.Field(NimbusChangeLogType)
    treatment_branches = graphene.List(NimbusBranchType)
    warn_feature_schema = graphene.Boolean()

    class Meta:
        model = NimbusExperiment
        fields = (
            "application",
            "can_archive",
            "can_edit",
            "can_review",
            "changes",
            "channel",
            "computed_duration_days",
            "computed_end_date",
            "computed_enrollment_days",
            "computed_enrollment_end_date",
            "conclusion_recommendation",
            "countries",
            "documentation_links",
            "enrollment_end_date",
            "feature_config",
            "feature_configs",
            "firefox_max_version",
            "firefox_min_version",
            "hypothesis",
            "id",
            "is_archived",
            "is_rollout_dirty",
            "is_enrollment_pause_pending",
            "is_enrollment_paused",
            "is_first_run",
            "is_localized",
            "is_rollout",
            "is_sticky",
            "jexl_targeting_expression",
            "languages",
            "locales",
            "localized_content",
            "monitoring_dashboard_url",
            "name",
            "owner",
            "parent",
            "population_percent",
            "prevent_pref_conflicts",
            "primary_outcomes",
            "projects",
            "proposed_duration",
            "proposed_enrollment",
            "public_description",
            "publish_status",
            "ready_for_review",
            "recipe_json",
            "reference_branch",
            "rejection",
            "results_expected_date",
            "results_ready",
            "review_request",
            "review_url",
            "risk_brand",
            "risk_mitigation_link",
            "risk_partner_related",
            "risk_revenue",
            "rollout_monitoring_dashboard_url",
            "secondary_outcomes",
            "show_results_url",
            "signoff_recommendations",
            "slug",
            "start_date",
            "status_next",
            "status",
            "takeaways_summary",
            "targeting_config_slug",
            "targeting_config",
            "timeout",
            "total_enrolled_clients",
            "treatment_branches",
            "warn_feature_schema",
        )

    def resolve_feature_config(self, info):
        if self.feature_configs.exists():
            return sorted(
                self.feature_configs.all(),
                key=lambda feature_config: (feature_config.slug),
            )[0]

    def resolve_feature_configs(self, info):
        return self.feature_configs.all()

    def resolve_projects(self, info):
        return self.projects.all()

    def resolve_reference_branch(self, info):
        return self.reference_branch or NimbusBranch(
            name=NimbusConstants.DEFAULT_REFERENCE_BRANCH_NAME
        )

    def resolve_treatment_branches(self, info):
        if self.branches.exists():
            return self.treatment_branches
        return [NimbusBranch(name=NimbusConstants.DEFAULT_TREATMENT_BRANCH_NAME)]

    def resolve_ready_for_review(self, info):
        serializer = NimbusReviewSerializer(
            self,
            data=NimbusReviewSerializer(self).data,
        )
        ready = serializer.is_valid()
        return NimbusReviewType(
            message=serializer.errors,
            warnings=serializer.warnings,
            ready=ready,
        )

    def resolve_targeting_config_slug(self, info):
        if self.targeting_config_slug in self.TargetingConfig:
            return self.TargetingConfig(self.targeting_config_slug).value
        return self.targeting_config_slug

    def resolve_targeting_config(self, info):

        if self.targeting_config_slug in self.TargetingConfig:

            return [
                NimbusExperimentTargetingConfigType(
                    label=NimbusExperiment.TARGETING_CONFIGS[
                        self.targeting_config_slug
                    ].name,
                    value=self.targeting_config_slug,
                    description=NimbusExperiment.TARGETING_CONFIGS[
                        self.targeting_config_slug
                    ].description,
                    application_values=NimbusExperiment.TARGETING_CONFIGS[
                        self.targeting_config_slug
                    ].application_choice_names,
                    sticky_required=NimbusExperiment.TARGETING_CONFIGS[
                        self.targeting_config_slug
                    ].sticky_required,
                    is_first_run_required=NimbusExperiment.TARGETING_CONFIGS[
                        self.targeting_config_slug
                    ].is_first_run_required,
                )
            ]
        return []

    def resolve_jexl_targeting_expression(self, info):
        return self.targeting

    def resolve_is_enrollment_paused(self, info):
        return self.is_paused_published

    def resolve_enrollment_end_date(self, info):
        return self.proposed_enrollment_end_date

    def resolve_can_edit(self, info):
        return self.can_edit

    def resolve_can_archive(self, info):
        return self.can_archive

    def resolve_can_review(self, info):
        return self.can_review(info.context.user)

    def resolve_review_request(self, info):
        return self.changes.latest_review_request()

    def resolve_rejection(self, info):
        return self.changes.latest_rejection()

    def resolve_timeout(self, info):
        return self.changes.latest_timeout()

    def resolve_recipe_json(self, info):
        return json.dumps(
            self.published_dto or NimbusExperimentSerializer(self).data,
            indent=2,
            sort_keys=True,
        )

    def resolve_locales(self, info):
        return self.locales.all().order_by("name")

    def resolve_countries(self, info):
        return self.countries.all().order_by("name")

    def resolve_languages(self, info):
        return self.languages.all().order_by("name")

    def resolve_changes(self, info):
        return self.changes.all().order_by("changed_on")
