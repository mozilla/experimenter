from django.urls import re_path

from experimenter.nimbus_ui_new.views import (
    NimbusChangeLogsView,
    NimbusExperimentsListTableView,
    NimbusExperimentsListView,
)

urlpatterns = [
    re_path(
        r"^(?P<slug>[\w-]+)/history/$",
        NimbusChangeLogsView.as_view(),
        name="nimbus-new-history",
    ),
    re_path(
        r"^table/",
        NimbusExperimentsListTableView.as_view(),
        name="nimbus-new-table",
    ),
    re_path(
        r"^",
        NimbusExperimentsListView.as_view(),
        name="nimbus-new-list",
    ),
]
