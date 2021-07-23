from django.conf.urls import url

from experimenter.reporting.api.v7.views import ReportDataView

urlpatterns = [
    url(
        r"^(?P<start_date>\d{4}-\d{2}-\d{2})/(?P<end_date>\d{4}-\d{2}-\d{2})$",
        ReportDataView.as_view(),
        name="reporting-rest",
    )
]
