from django.urls import re_path

from experimenter.visualization.api.v3.views import analysis_results_view

urlpatterns = [
    re_path(
        r"^visualization/(?P<slug>[\w-]+)/$",
        analysis_results_view,
        name="visualization-analysis-data",
    )
]
