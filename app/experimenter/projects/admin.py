from django.contrib import admin

from experimenter.projects.models import Project


class ProjectAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(Project, ProjectAdmin)
