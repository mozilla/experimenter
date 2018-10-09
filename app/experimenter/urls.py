from django.conf import settings
from django.conf.urls import re_path, include
from django.conf.urls.static import static
from django.contrib import admin

from experimenter.experiments.views import ExperimentListView


urlpatterns = [
    re_path(
        r"^api/v1/experiments/", include("experimenter.experiments.api_urls")
    ),
    re_path(r"^admin/", admin.site.urls),
    re_path(r"^experiments/", include("experimenter.experiments.web_urls")),
    re_path(r"^projects/", include("experimenter.projects.urls")),
    re_path(r"^$", ExperimentListView.as_view(), name="home"),
]

if settings.DEBUG:  # pragma: no cover
    urlpatterns = (
        static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
        + urlpatterns
    )
