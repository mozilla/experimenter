from django.urls import re_path

from experimenter.nimbus_ui_new.views import (
    NimbusChangeLogsView,
    NimbusExperimentDetailView,
    NimbusExperimentsListTableView,
    NimbusExperimentsListView,
    QAStatusUpdateView,
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
        r"^(?P<slug>[\w-]+)/summary/$",
        NimbusExperimentDetailView.as_view(),
        name="nimbus-new-detail",
    ),
    re_path(
        r"^(?P<slug>[\w-]+)/update_qa_status/$",
        QAStatusUpdateView.as_view(),
        name="update-qa-status",
    ),
    re_path(
        r"^",
        NimbusExperimentsListView.as_view(),
        name="nimbus-new-list",
    ),
]
