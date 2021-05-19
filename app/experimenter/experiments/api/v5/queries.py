import graphene
from django.conf import settings

from experimenter.experiments.api.v5.types import (
    NimbusExperimentTargetingConfigSlugChoice,
    NimbusExperimentType,
    NimbusFeatureConfigType,
    NimbusLabelValueType,
    NimbusOutcomeType,
)
from experimenter.experiments.models.nimbus import NimbusExperiment, NimbusFeatureConfig
from experimenter.outcomes import Outcomes


class ApplicationChannel(graphene.ObjectType):
    label = graphene.String()
    channels = graphene.List(graphene.String)


class NimbusConfigurationType(graphene.ObjectType):
    application = graphene.List(NimbusLabelValueType)
    channel = graphene.List(NimbusLabelValueType)
    feature_config = graphene.List(NimbusFeatureConfigType)
    firefox_min_version = graphene.List(NimbusLabelValueType)
    outcomes = graphene.List(NimbusOutcomeType)
    targeting_config_slug = graphene.List(NimbusExperimentTargetingConfigSlugChoice)
    hypothesis_default = graphene.String()
    max_primary_outcomes = graphene.Int()
    documentation_link = graphene.List(NimbusLabelValueType)
    kinto_admin_url = graphene.String()

    def _text_choices_to_label_value_list(root, text_choices):
        return [
            NimbusLabelValueType(
                label=text_choices[name].label,
                value=name,
            )
            for name in text_choices.names
        ]

    def resolve_application(root, info):
        return root._text_choices_to_label_value_list(NimbusExperiment.Application)

    def resolve_channel(root, info):
        return root._text_choices_to_label_value_list(NimbusExperiment.Channel)

    def resolve_feature_config(root, info):
        return NimbusFeatureConfig.objects.all()

    def resolve_firefox_min_version(root, info):
        return root._text_choices_to_label_value_list(NimbusExperiment.Version)

    def resolve_outcomes(root, info):
        return Outcomes.all()

    def resolve_targeting_config_slug(root, info):
        return [
            NimbusExperimentTargetingConfigSlugChoice(
                label=choice.label,
                value=choice.name,
                application_values=NimbusExperiment.TARGETING_CONFIGS[
                    choice.value
                ].application_choice_names,
            )
            for choice in NimbusExperiment.TargetingConfig
        ]

    def resolve_hypothesis_default(root, info):
        return NimbusExperiment.HYPOTHESIS_DEFAULT

    def resolve_max_primary_outcomes(root, info):
        return NimbusExperiment.MAX_PRIMARY_OUTCOMES

    def resolve_documentation_link(root, info):
        return root._text_choices_to_label_value_list(NimbusExperiment.DocumentationLink)

    def resolve_kinto_admin_url(root, info):
        return settings.KINTO_ADMIN_URL


class Query(graphene.ObjectType):
    experiments = graphene.List(
        NimbusExperimentType,
        description="List Nimbus Experiments.",
    )
    experiment_by_slug = graphene.Field(
        NimbusExperimentType,
        description="Retrieve a Nimbus experiment by its slug.",
        slug=graphene.String(required=True),
    )

    nimbus_config = graphene.Field(
        NimbusConfigurationType,
        description="Nimbus Configuration Data for front-end usage.",
    )

    def resolve_experiments(root, info):
        return NimbusExperiment.objects.all()

    def resolve_experiment_by_slug(root, info, slug):
        try:
            return NimbusExperiment.objects.get(slug=slug)
        except NimbusExperiment.DoesNotExist:
            return None

    def resolve_nimbus_config(root, info):
        return NimbusConfigurationType()
