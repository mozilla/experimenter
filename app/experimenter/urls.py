from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin

from experimenter.experiments.views import ExperimentListView


urlpatterns = [
    url(r"^api/v1/experiments/", include("experimenter.experiments.api_urls")),
    url(r"^admin/", admin.site.urls),
    url(r"^experiments/", include("experimenter.experiments.web_urls")),
    url(r"^projects/", include("experimenter.projects.urls")),
    url(r"^$", ExperimentListView.as_view(), name="home"),
]

if settings.DEBUG:  # pragma: no cover
    urlpatterns = (
        static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
        + urlpatterns
    )
