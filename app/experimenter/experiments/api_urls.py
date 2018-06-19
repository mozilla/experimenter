from django.conf.urls import url

from experimenter.experiments.api_views import (
    ExperimentAcceptView,
    ExperimentDetailView,
    ExperimentListView,
    ExperimentRejectView,
)


urlpatterns = [
    url(
        r"^(?P<slug>[\w-]+)/accept/$",
        ExperimentAcceptView.as_view(),
        name="experiments-api-accept",
    ),
    url(
        r"^(?P<slug>[\w-]+)/reject/$",
        ExperimentRejectView.as_view(),
        name="experiments-api-reject",
    ),
    url(
        r"^(?P<slug>[\w-]+)/$",
        ExperimentDetailView.as_view(),
        name="experiments-api-detail",
    ),
    url(r"^$", ExperimentListView.as_view(), name="experiments-api-list"),
]
