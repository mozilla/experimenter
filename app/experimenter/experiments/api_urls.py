from django.conf.urls import url

from experimenter.experiments.api_views import (
    ExperimentAcceptView,
    ExperimentListView,
    ExperimentRejectView,
)


urlpatterns = [
    url(r"^$", ExperimentListView.as_view(), name="experiments-api-list"),
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
]
