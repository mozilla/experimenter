from django.urls import re_path

from experimenter.glean.views import AlertDismissedView, OptOutView

urlpatterns = [
    re_path(
        r"^alert-dismissed/$",
        AlertDismissedView.as_view(),
        name="glean-alert-dismissed",
    ),
    re_path(
        r"^opt-out/$",
        OptOutView.as_view(),
        name="glean-opt-out",
    ),
]
