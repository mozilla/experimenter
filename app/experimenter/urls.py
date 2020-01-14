from django.conf import settings
from django.conf.urls import re_path, include
from django.conf.urls.static import static
from django.contrib import admin
from rest_framework.schemas import get_schema_view
from django.views.generic import TemplateView

from experimenter.experiments.views import ExperimentListView


urlpatterns = [
    re_path(r"^api/v1/experiments/", include("experimenter.experiments.api_urls")),
    re_path(r"^admin/", admin.site.urls),
    re_path(r"^experiments/", include("experimenter.experiments.web_urls")),
    re_path(r"^$", ExperimentListView.as_view(), name="home"),
    re_path(
        r"^openapi",
        get_schema_view(
            title="Experimenter", description="Experimenter API", version="1.0.0"
        ),
        name="openapi-schema",
    ),
    re_path(
        r"^docs/",
        TemplateView.as_view(
            template_name="swagger-ui.html",
            extra_context={"schema_url": "openapi-schema"},
        ),
        name="swagger-ui",
    ),
]

if settings.DEBUG:
    urlpatterns = (
        static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + urlpatterns
    )
