from django.views.generic import ListView, DetailView

from experimenter.projects.models import Project


class ProjectListView(ListView):
    model = Project
    template_name = 'projects/list.html'


class ProjectDetailView(DetailView):
    model = Project
    template_name = 'projects/detail.html'
