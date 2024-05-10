from collections import defaultdict

from django.views.generic import DetailView, ListView

from experimenter.experiments.models import NimbusExperiment


class NimbusChangeLogsView(DetailView):
    model = NimbusExperiment
    context_object_name = "experiment"
    template_name = "changelog/overview.html"


class NimbusExperimentsListView(ListView):
    model = NimbusExperiment
    queryset = NimbusExperiment.objects.with_owner_features()
    context_object_name = "experiments"
    template_name = "nimbus_experiments/list.html"

    def get_context_data(self, **kwargs):
        queryset = self.get_queryset()
        status_counts = defaultdict(int)
        for experiment in queryset:
            status_counts[experiment.status] += 1
            if experiment.is_archived:
                status_counts["Archived"] += 1
            if experiment.owner == self.request.user:
                status_counts["MyExperiments"] += 1
            if experiment.publish_status != NimbusExperiment.PublishStatus.IDLE:
                status_counts["Review"] += 1

        return super().get_context_data(status_counts=status_counts, **kwargs)
