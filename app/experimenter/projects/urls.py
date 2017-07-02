from django.conf.urls import url

from experimenter.projects.views import ProjectListView


urlpatterns = [
    url(r'', ProjectListView.as_view(), name='projects-list'),
]
