from django.conf.urls import url

from experimenter.experiments.views import ExperimentListView


urlpatterns = [
    url(
        r'^(?P<project_slug>.+)/experiments.json',
        ExperimentListView.as_view(),
        name='experiments-list',
    ),
]
