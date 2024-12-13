from django.urls import re_path

from experimenter.nimbus_ui_new.views import (
    AudienceUpdateView,
    DocumentationLinkCreateView,
    DocumentationLinkDeleteView,
    MetricsUpdateView,
    NimbusChangeLogsView,
    NimbusExperimentDetailView,
    NimbusExperimentsCreateView,
    NimbusExperimentsListTableView,
    OverviewUpdateView,
    QAStatusUpdateView,
    SignoffUpdateView,
    SubscribeView,
    TakeawaysUpdateView,
    UnsubscribeView,
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
        r"^(?P<slug>[\w-]+)/update_takeaways/$",
        TakeawaysUpdateView.as_view(),
        name="update-takeaways",
    ),
    re_path(
        r"^(?P<slug>[\w-]+)/update_signoff/$",
        SignoffUpdateView.as_view(),
        name="update-signoff",
    ),
    re_path(
        r"^(?P<slug>[\w-]+)/update_overview/$",
        OverviewUpdateView.as_view(),
        name="nimbus-new-update-overview",
    ),
    re_path(
        r"^(?P<slug>[\w-]+)/create_documentation_link/$",
        DocumentationLinkCreateView.as_view(),
        name="nimbus-new-create-documentation-link",
    ),
    re_path(
        r"^(?P<slug>[\w-]+)/delete_documentation_link/$",
        DocumentationLinkDeleteView.as_view(),
        name="nimbus-new-delete-documentation-link",
    ),
    re_path(
        r"^(?P<slug>[\w-]+)/update_metrics/$",
        MetricsUpdateView.as_view(),
        name="nimbus-new-update-metrics",
    ),
    re_path(
        r"^(?P<slug>[\w-]+)/update_audience/$",
        AudienceUpdateView.as_view(),
        name="nimbus-new-update-audience",
    ),
    re_path(
        r"^create/",
        NimbusExperimentsCreateView.as_view(),
        name="nimbus-new-create",
    ),
    re_path(
        r"^(?P<slug>[\w-]+)/subscribe/",
        SubscribeView.as_view(),
        name="nimbus-new-subscribe",
    ),
    re_path(
        r"^(?P<slug>[\w-]+)/unsubscribe/",
        UnsubscribeView.as_view(),
        name="nimbus-new-unsubscribe",
    ),
]
