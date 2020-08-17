from django.conf.urls import url

from experimenter.visualization.api.v1.views import (
    VisualizationView
)


urlpatterns = [
    url(
        r"^(?P<slug>[\w-]+)/$",
        VisualizationView.as_view(),
        name="visualization",
    )
]
