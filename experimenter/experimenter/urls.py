from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, re_path
from django.views.generic.base import RedirectView

from experimenter.legacy.legacy_experiments.views import (
    ExperimentListView,
    PageNotFoundView,
)
from experimenter.nimbus_ui.views import (
    NimbusExperimentsHomeView,
    NimbusExperimentsListView,
)

urlpatterns = [
    re_path(r"^$", NimbusExperimentsHomeView.as_view(), name="nimbus-ui-home"),
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
    re_path(r"^api/v7/", include("experimenter.experiments.api.v7.urls")),
    re_path(r"^api/v8/", include("experimenter.experiments.api.v8.urls")),
    re_path(r"^admin/", admin.site.urls),
    re_path(r"^experiments/", include("experimenter.legacy.legacy_experiments.urls")),
    re_path(r"^nimbus/", include("experimenter.nimbus_ui.urls")),
    re_path(r"^nimbus/$", NimbusExperimentsListView.as_view(), name="nimbus-list"),
    re_path(r"^legacy/$", ExperimentListView.as_view(), name="home"),
    re_path(
        r"^$",
        RedirectView.as_view(pattern_name="nimbus-ui-home"),
        name="redirect-to-nimbus",
    ),
]

handler404 = PageNotFoundView.as_404_view()

if settings.DEBUG:
    urlpatterns.append(re_path(r"^404/", PageNotFoundView.as_view()))
    urlpatterns = (
        static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + urlpatterns
    )