from django.conf.urls import url

from experimenter.experiments.views import (
    ExperimentCommentCreateView,
    ExperimentCreateView,
    ExperimentDetailView,
    ExperimentObjectivesUpdateView,
    ExperimentOverviewUpdateView,
    ExperimentReviewUpdateView,
    ExperimentRisksUpdateView,
    ExperimentStatusUpdateView,
    ExperimentVariantsUpdateView,
)


urlpatterns = [
    url(r"^new/$", ExperimentCreateView.as_view(), name="experiments-create"),
    url(
        r"^(?P<slug>[a-zA-Z0-9-]+)/edit/$",
        ExperimentOverviewUpdateView.as_view(),
        name="experiments-overview-update",
    ),
    url(
        r"^(?P<slug>[a-zA-Z0-9-]+)/edit-variants/$",
        ExperimentVariantsUpdateView.as_view(),
        name="experiments-variants-update",
    ),
    url(
        r"^(?P<slug>[a-zA-Z0-9-]+)/edit-objectives/$",
        ExperimentObjectivesUpdateView.as_view(),
        name="experiments-objectives-update",
    ),
    url(
        r"^(?P<slug>[a-zA-Z0-9-]+)/edit-risks/$",
        ExperimentRisksUpdateView.as_view(),
        name="experiments-risks-update",
    ),
    url(
        r"^(?P<slug>[a-zA-Z0-9-]+)/status-update/$",
        ExperimentStatusUpdateView.as_view(),
        name="experiments-status-update",
    ),
    url(
        r"^(?P<slug>[a-zA-Z0-9-]+)/review-update/$",
        ExperimentReviewUpdateView.as_view(),
        name="experiments-review-update",
    ),
    url(
        r"^(?P<slug>[a-zA-Z0-9-]+)/comment/$",
        ExperimentCommentCreateView.as_view(),
        name="experiments-comment-create",
    ),
    url(
        r"^(?P<slug>[a-zA-Z0-9-]+)/$",
        ExperimentDetailView.as_view(),
        name="experiments-detail",
    ),
]
