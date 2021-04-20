from django import forms
from django.contrib import admin
from django.contrib.postgres.forms import SimpleArrayField

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


class NimbusExperimentChangeLogInlineAdmin(admin.StackedInline):
    model = NimbusChangeLog
    extra = 1


class NimbusExperimentAdminForm(forms.ModelForm):
    channel = forms.ChoiceField(choices=NimbusExperiment.Channel.choices)
    public_description = forms.CharField(required=False, widget=forms.Textarea())
    firefox_min_version = forms.ChoiceField(
        choices=NimbusExperiment.Version.choices, required=False
    )
    channel = forms.ChoiceField(choices=NimbusExperiment.Channel.choices, required=False)
    primary_outcomes = SimpleArrayField(forms.CharField(), required=False)
    secondary_outcomes = SimpleArrayField(forms.CharField(), required=False)
    targeting_config_slug = forms.ChoiceField(
        choices=NimbusExperiment.TargetingConfig.choices, required=False
    )

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
    list_display = (
        "name",
        "status",
        "publish_status",
        "application",
        "channel",
        "firefox_min_version",
    )
    list_filter = ("status", "publish_status", "application")
    prepopulated_fields = {"slug": ("name",)}
    form = NimbusExperimentAdminForm


class NimbusFeatureConfigAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}


admin.site.register(NimbusExperiment, NimbusExperimentAdmin)
admin.site.register(NimbusFeatureConfig, NimbusFeatureConfigAdmin)
admin.site.register(NimbusDocumentationLink)
