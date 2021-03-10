from django import forms
from django.contrib import admin

from experimenter.experiments.models import (
    NimbusBranch,
    NimbusChangeLog,
    NimbusDocumentationLink,
    NimbusExperiment,
    NimbusFeatureConfig,
)


class NimbusBranchInlineAdmin(admin.StackedInline):
    model = NimbusBranch
    extra = 0


class NimbusDocumentationLinkInlineAdmin(admin.TabularInline):
    model = NimbusDocumentationLink
    extra = 1
    fields = ("title", "link")


class NimbusExperimentChangeLogInlineAdmin(admin.TabularInline):
    model = NimbusChangeLog
    extra = 1

    fields = (
        "changed_by",
        "changed_on",
        "old_status",
        "new_status",
        "message",
    )


class NimbusExperimentAdminForm(forms.ModelForm):
    channel = forms.ChoiceField(choices=NimbusExperiment.Channel.choices)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "instance" in kwargs:
            instance = kwargs["instance"]
            self.fields["reference_branch"].queryset = self.fields[
                "reference_branch"
            ].queryset.filter(experiment=instance)
        else:
            self.fields["reference_branch"].queryset = self.fields[
                "reference_branch"
            ].queryset.none()

    class Meta:
        model = NimbusExperiment
        exclude = ("id",)


class NimbusExperimentAdmin(admin.ModelAdmin):
    inlines = (
        NimbusDocumentationLinkInlineAdmin,
        NimbusBranchInlineAdmin,
        NimbusExperimentChangeLogInlineAdmin,
    )
    list_display = ("name", "status", "application", "channel", "firefox_min_version")
    list_filter = ("status", "application")
    prepopulated_fields = {"slug": ("name",)}
    form = NimbusExperimentAdminForm


class NimbusFeatureConfigAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}


admin.site.register(NimbusExperiment, NimbusExperimentAdmin)
admin.site.register(NimbusFeatureConfig, NimbusFeatureConfigAdmin)
admin.site.register(NimbusDocumentationLink)
