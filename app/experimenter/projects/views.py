from django.views.generic import ListView

from experimenter.projects.models import Project


class ProjectListView(ListView):
    model = Project
    template_name = 'projects/list.html'
