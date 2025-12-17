from django.urls import re_path

from experimenter.legacy.legacy_experiments.views import ExperimentDetailView

urlpatterns = [
    re_path(
        r"^(?P<slug>[\w-]+)/$", ExperimentDetailView.as_view(), name="experiments-detail"
    ),
]
