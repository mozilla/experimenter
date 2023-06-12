from django.urls import re_path

from experimenter.changelog.views import NimbusChangeLogsView

urlpatterns = [
    re_path(
        r"^(?P<slug>[\w-]+)/$", NimbusChangeLogsView.as_view(), name="changelogs-by-slug"
    ),
]
