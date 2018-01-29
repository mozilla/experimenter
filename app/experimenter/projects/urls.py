from django.conf.urls import url

from experimenter.projects.views import (
    ProjectCreateView,
    ProjectListView,
    ProjectDetailView,
    ProjectUpdateView,
)


urlpatterns = [
    url(
        r'^projects/new/$',
        ProjectCreateView.as_view(),
        name='projects-create',
    ),
    url(
        r'^projects/(?P<slug>[a-zA-Z0-9-]+)/edit/$',
        ProjectUpdateView.as_view(),
        name='projects-update',
    ),
    url(
        r'^projects/(?P<slug>[a-zA-Z0-9-]+)/$',
        ProjectDetailView.as_view(),
        name='projects-detail',
    ),
    url(r'^$', ProjectListView.as_view(), name='projects-list'),
]
