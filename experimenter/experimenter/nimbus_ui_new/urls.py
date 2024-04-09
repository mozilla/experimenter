from django.urls import re_path

from experimenter.nimbus_ui_new.views import NimbusChangeLogsView

urlpatterns = [
    re_path(
        r"^(?P<slug>[\w-]+)/history/$",
        NimbusChangeLogsView.as_view(),
        name="nimbus-history",
    ),
]
