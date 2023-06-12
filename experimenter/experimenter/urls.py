from django.conf import settings
from django.conf.urls import include, re_path
from django.conf.urls.static import static
from django.contrib import admin
from django.views.generic.base import RedirectView

from experimenter.legacy.legacy_experiments.views import (
    ExperimentListView,
    NimbusUIView,
    PageNotFoundView,
)

urlpatterns = [
    re_path(
        r"^api/v1/experiments/",
        include("experimenter.legacy.legacy_experiments.api.v1.urls"),
    ),
    re_path(
        r"^api/v2/experiments/",
        include("experimenter.legacy.legacy_experiments.api.v2.urls"),
    ),
    re_path(r"^api/v3/", include("experimenter.visualization.api.v3.urls")),
    re_path(r"^api/v5/", include("experimenter.experiments.api.v5.urls")),
    re_path(r"^api/v6/", include("experimenter.experiments.api.v6.urls")),
    re_path(r"^admin/", admin.site.urls),
    re_path(r"^history/", include("experimenter.changelog.urls")),
    re_path(r"^experiments/", include("experimenter.legacy.legacy_experiments.urls")),
    re_path(r"^nimbus/", NimbusUIView.as_view(), name="nimbus-list"),
    re_path(r"^nimbus/(?P<slug>[\w-]+)/", NimbusUIView.as_view(), name="nimbus-detail"),
    re_path(r"^legacy/$", ExperimentListView.as_view(), name="home"),
    re_path(
        r"^$",
        RedirectView.as_view(pattern_name="nimbus-list"),
        name="redirect-to-nimbus",
    ),
]

handler404 = PageNotFoundView.as_404_view()

if settings.DEBUG:
    urlpatterns.append(re_path(r"^404/", PageNotFoundView.as_view()))
    urlpatterns = (
        static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + urlpatterns
    )
