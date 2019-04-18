from django.urls import re_path

from experimenter.experiments.views import (
    ExperimentArchiveUpdateView,
    ExperimentCommentCreateView,
    ExperimentCreateView,
    ExperimentDetailView,
    ExperimentNormandyUpdateView,
    ExperimentObjectivesUpdateView,
    ExperimentOverviewUpdateView,
    ExperimentReviewUpdateView,
    ExperimentRisksUpdateView,
    ExperimentStatusUpdateView,
    ExperimentVariantsUpdateView,
)


urlpatterns = [
    re_path(
        r"^new/$", ExperimentCreateView.as_view(), name="experiments-create"
    ),
    re_path(
        r"^(?P<slug>[\w-]+)/edit/$",
        ExperimentOverviewUpdateView.as_view(),
        name="experiments-overview-update",
    ),
    re_path(
        r"^(?P<slug>[\w-]+)/edit-variants/$",
        ExperimentVariantsUpdateView.as_view(),
        name="experiments-variants-update",
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
        r"^(?P<slug>[\w-]+)/archive-update/$",
        ExperimentArchiveUpdateView.as_view(),
        name="experiments-archive-update",
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
        r"^(?P<slug>[\w-]+)/$",
        ExperimentDetailView.as_view(),
        name="experiments-detail",
    ),
]
