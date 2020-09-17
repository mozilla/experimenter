from django.conf.urls import url

from experimenter.visualization.api.v3.views import analysis_results_view

urlpatterns = [
    url(
        r"^visualization/(?P<slug>[\w-]+)/$",
        analysis_results_view,
        name="visualization-analysis-data",
    )
]
