from rest_framework.generics import ListAPIView
from rest_framework_csv.renderers import CSVRenderer

from experimenter.experiments.api.v5.serializers import NimbusExperimentCsvSerializer
from experimenter.experiments.models import NimbusExperiment


class NimbusExperimentCsvRenderer(CSVRenderer):
    header = NimbusExperimentCsvSerializer.Meta.fields
    labels = dict(((field, field.replace("_", " ").title()) for field in header))


class NimbusExperimentCsvListView(ListAPIView):

    queryset = NimbusExperiment.objects.all().prefetch_related("feature_configs", "owner")

    def get_queryset(self):
        return sorted(
            super().get_queryset(),
            key=lambda experiment: str(experiment.start_date) or "",
        )

    serializer_class = NimbusExperimentCsvSerializer

    renderer_classes = (NimbusExperimentCsvRenderer,)
