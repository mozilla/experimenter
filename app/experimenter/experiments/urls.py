from django.conf.urls import url

from experimenter.experiments.views import (
    ExperimentListView,
    ExperimentAcceptView,
    ExperimentRejectView,
)


urlpatterns = [
    url(
        r'^$',
        ExperimentListView.as_view(),
        name='experiments-list',
    ),
    url(
        r'^(?P<slug>[\w-]+)/accept$',
        ExperimentAcceptView.as_view(),
        name='experiments-accept',
    ),
    url(
        r'^(?P<slug>[\w-]+)/reject$',
        ExperimentRejectView.as_view(),
        name='experiments-reject',
    ),
]
