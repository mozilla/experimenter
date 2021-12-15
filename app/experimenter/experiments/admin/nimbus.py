from django import forms
from django.contrib import admin
from django.contrib.postgres.forms import SimpleArrayField

from experimenter.experiments.models import (
    NimbusBranch,
    NimbusBranchScreenshot,
    NimbusBucketRange,
    NimbusChangeLog,
    NimbusDocumentationLink,
    NimbusExperiment,
    NimbusFeatureConfig,
    NimbusIsolationGroup,
)
from experimenter.experiments.models.nimbus import NimbusBranchFeatureValue
from experimenter.jetstream import tasks


@admin.action(description="Force jetstream data fetch.")
def force_fetch_jetstream_data(modeladmin, request, queryset):
    for experiment in queryset:
        tasks.fetch_experiment_data.delay(experiment.id)


class NoDeleteAdminMixin:
    def has_delete_permission(self, request, obj=None):
        return False


class ReadOnlyAdminMixin(NoDeleteAdminMixin):
    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class NimbusBucketRangeInlineAdmin(ReadOnlyAdminMixin, admin.StackedInline):
    model = NimbusBucketRange
    extra = 0


class NimbusIsolationGroupAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    inlines = (NimbusBucketRangeInlineAdmin,)

    class Meta:
        model = NimbusIsolationGroup
        exclude = ("id",)


class NimbusBranchInlineAdmin(NoDeleteAdminMixin, admin.StackedInline):
    model = NimbusBranch
    extra = 0


class NimbusDocumentationLinkInlineAdmin(NoDeleteAdminMixin, admin.TabularInline):
    model = NimbusDocumentationLink
    extra = 1


class NimbusExperimentChangeLogInlineAdmin(NoDeleteAdminMixin, admin.StackedInline):
    model = NimbusChangeLog
    extra = 1


class NimbusExperimentBucketRangeInlineAdmin(ReadOnlyAdminMixin, admin.StackedInline):
    model = NimbusBucketRange
    extra = 0
    fields = (
        "isolation_group_name",
        "isolation_group_instance",
        "isolation_group_total",
        "start",
        "count",
    )
    readonly_fields = (
        "isolation_group_name",
        "isolation_group_instance",
        "isolation_group_total",
        "start",
        "count",
    )

    @admin.display(description="Isolation Group Name")
    def isolation_group_name(self, instance):
        return instance.isolation_group.name

    @admin.display(description="Isolation Group Instance")
    def isolation_group_instance(self, instance):
        return instance.isolation_group.instance

    @admin.display(description="Isolation Group Total")
    def isolation_group_total(self, instance):
        return instance.isolation_group.total


class NimbusExperimentAdminForm(forms.ModelForm):
    application = forms.ChoiceField(choices=NimbusExperiment.Application.choices)
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
    conclusion_recommendation = forms.ChoiceField(
        choices=NimbusExperiment.ConclusionRecommendation.choices, required=False
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


class NimbusExperimentAdmin(NoDeleteAdminMixin, admin.ModelAdmin):
    inlines = (
        NimbusDocumentationLinkInlineAdmin,
        NimbusBranchInlineAdmin,
        NimbusExperimentBucketRangeInlineAdmin,
        NimbusExperimentChangeLogInlineAdmin,
    )
    list_display = (
        "name",
        "is_rollout",
        "status",
        "publish_status",
        "status_next",
        "application",
        "channel",
        "firefox_min_version",
    )
    list_filter = ("status", "publish_status", "application")
    prepopulated_fields = {"slug": ("name",)}
    form = NimbusExperimentAdminForm
    actions = [force_fetch_jetstream_data]


class NimbusFeatureConfigAdmin(NoDeleteAdminMixin, admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_filter = ("application", "read_only")
    list_display = ("name", "application", "read_only")
    exclude = ("read_only",)

    def has_change_permission(self, request, obj=None):
        return obj and not obj.read_only


class NimbusBranchScreenshotInlineAdmin(NoDeleteAdminMixin, admin.TabularInline):
    model = NimbusBranchScreenshot
    extra = 0


class NimbusBranchFeatureValueInlineAdmin(NoDeleteAdminMixin, admin.TabularInline):
    model = NimbusBranchFeatureValue
    extra = 0


class NimbusBranchAdmin(NoDeleteAdminMixin, admin.ModelAdmin):
    inlines = (
        NimbusBranchFeatureValueInlineAdmin,
        NimbusBranchScreenshotInlineAdmin,
    )
    list_display = (
        "name",
        "slug",
        "experiment",
    )
    list_display_links = ("name", "slug")
    list_filter = ("experiment",)
    prepopulated_fields = {"slug": ("name",)}


admin.site.register(NimbusIsolationGroup, NimbusIsolationGroupAdmin)
admin.site.register(NimbusExperiment, NimbusExperimentAdmin)
admin.site.register(NimbusFeatureConfig, NimbusFeatureConfigAdmin)
admin.site.register(NimbusBranch, NimbusBranchAdmin)
admin.site.register(NimbusDocumentationLink)
