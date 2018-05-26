from django.core.urlresolvers import reverse
from django.views.generic import CreateView, ListView, DetailView, UpdateView

from experimenter.projects.forms import ProjectForm
from experimenter.projects.models import Project


class ProjectEditMixin(object):
    model = Project
    form_class = ProjectForm
    template_name = "projects/edit.html"

    def get_success_url(self):
        return reverse("projects-detail", kwargs={"slug": self.object.slug})


class ProjectCreateView(ProjectEditMixin, CreateView):
    pass


class ProjectUpdateView(ProjectEditMixin, UpdateView):
    pass


class ProjectListView(ListView):
    model = Project
    template_name = "projects/list.html"


class ProjectDetailView(DetailView):
    model = Project
    template_name = "projects/detail.html"
