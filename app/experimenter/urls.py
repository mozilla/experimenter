from django.conf import settings
from django.conf.urls import include, re_path
from django.conf.urls.static import static
from django.contrib import admin

from experimenter.experiments.views import (
    ExperimentListView,
    ExperimentReportView,
    NimbusUIView,
    PageNotFoundView,
)

urlpatterns = [
    re_path(r"^api/v1/experiments/", include("experimenter.experiments.api.v1.urls")),
    re_path(r"^api/v2/experiments/", include("experimenter.experiments.api.v2.urls")),
    re_path(r"^api/v3/", include("experimenter.visualization.api.v3.urls")),
    re_path(r"^api/v5/", include("experimenter.experiments.api.v5.urls")),
    re_path(r"^api/v6/", include("experimenter.experiments.api.v6.urls")),
    re_path(r"^api/v7/", include("experimenter.reporting.api.v7.urls")),
    re_path(r"^admin/", admin.site.urls),
    re_path(r"^experiments/", include("experimenter.experiments.urls")),
    re_path(r"^nimbus/", NimbusUIView.as_view(), name="nimbus-list"),
    re_path(r"^nimbus/(?P<slug>[\w-]+)/", NimbusUIView.as_view(), name="nimbus-detail"),
    re_path(r"^reporting/", ExperimentReportView.as_view(), name="reporting"),
    re_path(r"^$", ExperimentListView.as_view(), name="home"),
]

handler404 = PageNotFoundView.as_404_view()

if settings.DEBUG:
    urlpatterns.append(re_path(r"^404/", PageNotFoundView.as_view()))
    urlpatterns = (
        static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + urlpatterns
    )
