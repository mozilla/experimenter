import graphene

from experimenter.experiments.api.v5.types import (
    NimbusExperimentType,
    NimbusFeatureConfigType,
    NimbusLabelValueType,
    NimbusProbeSetType,
)
from experimenter.experiments.models.nimbus import (
    NimbusExperiment,
    NimbusFeatureConfig,
    NimbusProbeSet,
)


class ApplicationChannel(graphene.ObjectType):
    label = graphene.String()
    channels = graphene.List(graphene.String)


class NimbusConfigurationType(graphene.ObjectType):
    application = graphene.List(NimbusLabelValueType)
    channel = graphene.List(NimbusLabelValueType)
    feature_config = graphene.List(NimbusFeatureConfigType)
    firefox_min_version = graphene.List(NimbusLabelValueType)
    probe_sets = graphene.List(NimbusProbeSetType)
    targeting_config_slug = graphene.List(NimbusLabelValueType)
    hypothesis_default = graphene.String()
    max_primary_probe_sets = graphene.Int()
    documentation_link = graphene.List(NimbusLabelValueType)

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

    def resolve_probe_sets(root, info):
        return NimbusProbeSet.objects.all()

    def resolve_targeting_config_slug(root, info):
        return root._text_choices_to_label_value_list(NimbusExperiment.TargetingConfig)

    def resolve_hypothesis_default(root, info):
        return NimbusExperiment.HYPOTHESIS_DEFAULT

    def resolve_max_primary_probe_sets(root, info):
        return NimbusExperiment.MAX_PRIMARY_PROBE_SETS

    def resolve_documentation_link(root, info):
        return root._text_choices_to_label_value_list(NimbusExperiment.DocumentationLink)


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
