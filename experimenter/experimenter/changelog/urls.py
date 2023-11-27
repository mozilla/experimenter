from django.urls import path, re_path

from experimenter.changelog.views import NimbusChangeLogsView, update_qa_status

urlpatterns = [
    re_path(
        r"^(?P<slug>[\w-]+)/$", NimbusChangeLogsView.as_view(), name="changelogs-by-slug"
    ),
    path(r"<slug:slug>/update-qa-status/", update_qa_status, name="update_qa_status"),
]
