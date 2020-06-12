from django.urls import re_path

from experimenter.experiments.views import (
    ExperimentArchiveUpdateView,
    ExperimentCommentCreateView,
    ExperimentCreateView,
    ExperimentDesignUpdateView,
    ExperimentDetailView,
    ExperimentNormandyUpdateView,
    ExperimentObjectivesUpdateView,
    ExperimentOverviewUpdateView,
    ExperimentRapidView,
    ExperimentResultsUpdateView,
    ExperimentReviewUpdateView,
    ExperimentRisksUpdateView,
    ExperimentStatusUpdateView,
    ExperimentSubscribedUpdateView,
    ExperimentTimelinePopulationUpdateView,
)


urlpatterns = [
    re_path(r"^rapid/", ExperimentRapidView.as_view(), name="experiments-rapid"),
    re_path(r"^rapid/new/", ExperimentRapidView.as_view(), name="experiments-rapid-create"),
    re_path(r"^new/$", ExperimentCreateView.as_view(), name="experiments-create"),
    re_path(
        r"^(?P<slug>[\w-]+)/edit/$",
        ExperimentOverviewUpdateView.as_view(),
        name="experiments-overview-update",
    ),
    re_path(
        r"^(?P<slug>[\w-]+)/edit-timeline-population/$",
        ExperimentTimelinePopulationUpdateView.as_view(),
        name="experiments-timeline-pop-update",
    ),
    re_path(
        r"^(?P<slug>[\w-]+)/edit-design/$",
        ExperimentDesignUpdateView.as_view(),
        name="experiments-design-update",
    ),
    re_path(
        r"^(?P<slug>[\w-]+)/edit-objectives/$",
        ExperimentObjectivesUpdateView.as_view(),
        name="experiments-objectives-update",
    ),
    re_path(
        r"^(?P<slug>[\w-]+)/edit-risks/$",
        ExperimentRisksUpdateView.as_view(),
        name="experiments-risks-update",
    ),
    re_path(
        r"^(?P<slug>[\w-]+)/edit-results/$",
        ExperimentResultsUpdateView.as_view(),
        name="experiments-results-update",
    ),
    re_path(
        r"^(?P<slug>[\w-]+)/archive-update/$",
        ExperimentArchiveUpdateView.as_view(),
        name="experiments-archive-update",
    ),
    re_path(
        r"^(?P<slug>[\w-]+)/subscribed-update/$",
        ExperimentSubscribedUpdateView.as_view(),
        name="experiments-subscribed-update",
    ),
    re_path(
        r"^(?P<slug>[\w-]+)/status-update/$",
        ExperimentStatusUpdateView.as_view(),
        name="experiments-status-update",
    ),
    re_path(
        r"^(?P<slug>[\w-]+)/review-update/$",
        ExperimentReviewUpdateView.as_view(),
        name="experiments-review-update",
    ),
    re_path(
        r"^(?P<slug>[\w-]+)/normandy-update/$",
        ExperimentNormandyUpdateView.as_view(),
        name="experiments-normandy-update",
    ),
    re_path(
        r"^(?P<slug>[\w-]+)/comment/$",
        ExperimentCommentCreateView.as_view(),
        name="experiments-comment-create",
    ),
    re_path(
        r"^(?P<slug>[\w-]+)/$", ExperimentDetailView.as_view(), name="experiments-detail"
    ),
]
