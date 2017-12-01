from django.conf.urls import url

from experimenter.projects.views import ProjectListView, ProjectDetailView


urlpatterns = [
    url(
        r'^projects/(?P<slug>[a-zA-Z0-9-]+)/$',
        ProjectDetailView.as_view(),
        name='projects-detail',
    ),
    url(r'^$', ProjectListView.as_view(), name='projects-list'),
]
