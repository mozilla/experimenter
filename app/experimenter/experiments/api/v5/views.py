from rest_framework.generics import ListAPIView
from rest_framework_csv.renderers import CSVRenderer

from experimenter.experiments.api.v5.serializers import NimbusExperimentCSVSerializer
from experimenter.experiments.models.nimbus import NimbusExperiment


class NimbusExperimentCSVRenderer(CSVRenderer):
    header = NimbusExperimentCSVSerializer.Meta.fields
    labels = dict(((field, field.replace("_", " ").title()) for field in header))


class NimbusExperimentCSVListView(ListAPIView):
    queryset = NimbusExperiment.objects.all()
    serializer_class = NimbusExperimentCSVSerializer

    renderer_classes = (NimbusExperimentCSVRenderer,)
