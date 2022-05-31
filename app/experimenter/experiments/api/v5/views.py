from rest_framework.generics import ListAPIView
from rest_framework_csv.renderers import CSVRenderer

from experimenter.experiments.api.v5.serializers import NimbusExperimentCsvSerializer
from experimenter.experiments.models.nimbus import NimbusExperiment


class NimbusExperimentCsvRenderer(CSVRenderer):
    header = NimbusExperimentCsvSerializer.Meta.fields
    labels = dict(((field, field.replace("_", " ").title()) for field in header))


class NimbusExperimentCsvListView(ListAPIView):
    # get all objects and sort by start_date if its not null
    queryset = sorted(
        NimbusExperiment.objects.all(),
        key=lambda experiment: str(experiment.start_date) or "",
    )

    serializer_class = NimbusExperimentCsvSerializer

    renderer_classes = (NimbusExperimentCsvRenderer,)
