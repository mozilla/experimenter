from django.conf import settings
from django.conf.urls import include, re_path
from django.conf.urls.static import static
from django.contrib import admin

from experimenter.experiments.views import ExperimentListView

urlpatterns = [
    re_path(r"^api/v1/experiments/", include("experimenter.experiments.api.v1.urls")),
    re_path(r"^api/v2/experiments/", include("experimenter.experiments.api.v2.urls")),
    re_path(r"^api/v3/", include("experimenter.experiments.api.v3.urls")),
    re_path(r"^api/v3/", include("experimenter.visualization.api.v3.urls")),
    re_path(r"^api/v4/", include("experimenter.experiments.api.v4.urls")),
    re_path(r"^api/v5/", include("experimenter.experiments.api.v5.urls")),
    re_path(r"^api/v6/", include("experimenter.experiments.api.v6.urls")),
    re_path(r"^admin/", admin.site.urls),
    re_path(r"^experiments/", include("experimenter.experiments.urls")),
    re_path(r"^$", ExperimentListView.as_view(), name="home"),
]

if settings.DEBUG:
    urlpatterns = (
        static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + urlpatterns
    )
