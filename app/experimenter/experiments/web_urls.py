from django.conf.urls import url

from experimenter.experiments.views import (
    ExperimentDetailView,
)


urlpatterns = [
    url(
        r'^(?P<slug>[a-zA-Z0-9-]+)/$',
        ExperimentDetailView.as_view(),
        name='experiments-detail',
    ),
]
