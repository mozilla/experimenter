import graphene
from django.db.models import Field
from graphene_django.forms.mutation import DjangoModelFormMutation

from experimenter.experiments.api.v5.forms import CreateExperimentForm
from experimenter.experiments.api.v5.types import NimbusExperimentType


class CreateExperimentMutation(DjangoModelFormMutation):
    experiment = Field(NimbusExperimentType)

    class Meta:
        form_class = CreateExperimentForm


class Mutation(graphene.ObjectType):
    create_experiment = CreateExperimentMutation.Field(
        description="Create a new Nimbus Experiment."
    )
