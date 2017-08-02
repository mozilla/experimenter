from django.conf.urls import url

from experimenter.experiments.views import ExperimentListView


urlpatterns = [
    url(
        r'^$',
        ExperimentListView.as_view(),
        name='experiments-list',
    ),
]
