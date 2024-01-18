from typing import Any, Dict

from django import forms
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.postgres import forms as pgforms
from django.utils.encoding import force_text
from import_export import fields, resources
from import_export.admin import ExportActionMixin, ImportMixin
from import_export.widgets import DecimalWidget, ForeignKeyWidget

from experimenter.experiments.changelog_utils import (
    NimbusBranchChangeLogSerializer,
    NimbusChangeLogSerializer,
)
from experimenter.experiments.constants import NimbusConstants
from experimenter.experiments.models import (
    NimbusBranch,
    NimbusBranchFeatureValue,
    NimbusBranchScreenshot,
    NimbusBucketRange,
    NimbusChangeLog,
    NimbusDocumentationLink,
    NimbusExperiment,
    NimbusFeatureConfig,
    NimbusFeatureVersion,
    NimbusIsolationGroup,
    NimbusVersionedSchema,
)
from experimenter.jetstream import tasks
from experimenter.settings import DEV_USER_EMAIL


@admin.action(description="Force jetstream data fetch.")
def force_fetch_jetstream_data(modeladmin, request, queryset):
    for experiment in queryset:
        tasks.fetch_experiment_data.delay(experiment.id)


# Monkeypatch DecimalWidget render fn to work around a bug exporting Decimal to YAML
# - https://github.com/django-import-export/django-import-export/issues/1324
def DecimalWidgetRender(self, value, obj=None):
    return str(value)


DecimalWidget.render = DecimalWidgetRender


class NimbusBranchForeignKeyWidget(ForeignKeyWidget):
    """
    override ForeignKeyWidget to filter NimbusBranch
    by experiment in addition to the passed field
    """

    def __init__(self, model, field="slug", *args, **kwargs):
        self.model = model
        self.field = field

    def get_queryset(self, value, row, *args, **kwargs):
        experiment = NimbusExperiment.objects.get(slug=row.get("slug"))
        return self.model.objects.filter(experiment=experiment)


class NimbusExperimentResource(resources.ModelResource):
    changes = fields.Field()
    branches = fields.Field()
    reference_branch_slug = fields.Field(
        column_name="reference_branch_slug",
        widget=NimbusBranchForeignKeyWidget(NimbusBranch, "slug"),
    )
    # special cases for enums that can be null
    # - the default handling for these turns nulls into empty strings,
    #   which breaks the Nimbus UI type validation
    status_next = fields.Field()
    conclusion_recommendation = fields.Field()

    def get_diff_headers(self):
        skip_list = ["reference_branch_slug"]
        return [
            force_text(field.column_name)
            for field in self.get_export_fields()
            if force_text(field.column_name) not in skip_list
        ]

    class Meta:
        model = NimbusExperiment
        exclude = ("id", "reference_branch", "parent")
        import_id_fields = ("slug",)

    def dehydrate_changes(self, experiment):
        return [dict(NimbusChangeLogSerializer(c).data) for c in experiment.changes.all()]

    def dehydrate_branches(self, experiment):
        return [
            dict(NimbusBranchChangeLogSerializer(b).data)
            for b in experiment.branches.all()
        ]

    def dehydrate_reference_branch_slug(self, experiment: NimbusExperiment):
        if experiment.reference_branch is not None:
            return experiment.reference_branch.slug
        return None

    def dehydrate_status_next(self, experiment):
        """Return None instead of empty string for nullable enums"""
        if experiment.status_next not in dict(NimbusConstants.Status.choices):
            return None
        return experiment.status_next

    def dehydrate_conclusion_recommendation(self, experiment):
        """Return None instead of empty string for nullable enums"""
        if experiment.conclusion_recommendation not in dict(
            NimbusConstants.ConclusionRecommendation.choices
        ):
            return None
        return experiment.conclusion_recommendation

    def before_import_row(self, row: Dict[str, Any], row_number=None, **kwargs):
        owner_id = row.get("owner")

        try:
            User.objects.get(id=owner_id)
        except User.DoesNotExist:
            # use dev testing user as default
            (dev_user, _) = User.objects.get_or_create(email=DEV_USER_EMAIL)
            row["owner"] = dev_user.id

    def after_import_row(self, row, row_result, row_number=None, **kwargs):
        experiment = NimbusExperiment.objects.get(slug=row.get("slug"))

        # create branches
        branch_slug = row.get("reference_branch_slug")
        branches = row.get("branches")

        for branch in branches:
            if branch.get("slug") == branch_slug:
                (ref_branch, _) = NimbusBranch.objects.get_or_create(
                    slug=branch_slug,
                    name=branch.get("name"),
                    description=branch.get("description"),
                    ratio=branch.get("ratio"),
                    experiment=experiment,
                )

                experiment.reference_branch = ref_branch
                experiment.save()
            else:
                NimbusBranch.objects.get_or_create(
                    slug=branch.get("slug"),
                    name=branch.get("name"),
                    description=branch.get("description"),
                    ratio=branch.get("ratio"),
                    experiment=experiment,
                )

        # create change logs
        import_changes = row.get("changes")

        for change in import_changes:
            NimbusChangeLog.objects.get_or_create(
                changed_on=change.get("changed_on"),
                old_status=change.get("old_status"),
                old_status_next=change.get("old_status_next"),
                old_publish_status=change.get("old_publish_status"),
                new_status=change.get("new_status"),
                new_status_next=change.get("new_status_next"),
                new_publish_status=change.get("new_publish_status"),
                message=change.get("message"),
                experiment_data=change.get("experiment_data"),
                published_dto_changed=change.get("published_dto_changed"),
                changed_by=experiment.owner,
                experiment=experiment,
            )


class NoDeleteAdminMixin:
    def has_delete_permission(self, request, obj=None):
        return False


class ReadOnlyAdminMixin(NoDeleteAdminMixin):
    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class NimbusBucketRangeInlineAdmin(
    ReadOnlyAdminMixin, admin.StackedInline[NimbusBucketRange]
):
    model = NimbusBucketRange
    extra = 0


class NimbusIsolationGroupAdmin(
    ReadOnlyAdminMixin, admin.ModelAdmin[NimbusIsolationGroup]
):
    inlines = (NimbusBucketRangeInlineAdmin,)

    class Meta:
        model = NimbusIsolationGroup
        exclude = ("id",)


class NimbusBranchInlineAdmin(NoDeleteAdminMixin, admin.StackedInline[NimbusBranch]):
    model = NimbusBranch
    extra = 0


class NimbusDocumentationLinkInlineAdmin(
    NoDeleteAdminMixin, admin.TabularInline[NimbusDocumentationLink]
):
    model = NimbusDocumentationLink
    extra = 1


class NimbusExperimentChangeLogInlineAdmin(
    NoDeleteAdminMixin, admin.StackedInline[NimbusChangeLog]
):
    model = NimbusChangeLog
    extra = 1


class NimbusExperimentBucketRangeInlineAdmin(
    ReadOnlyAdminMixin, admin.StackedInline[NimbusBucketRange]
):
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
    public_description = forms.CharField(required=False, widget=forms.Textarea())
    firefox_min_version = forms.ChoiceField(
        choices=NimbusExperiment.Version.choices, required=False
    )
    firefox_max_version = forms.ChoiceField(
        choices=NimbusExperiment.Version.choices, required=False
    )
    channel = forms.ChoiceField(choices=NimbusExperiment.Channel.choices, required=False)
    primary_outcomes = pgforms.SimpleArrayField(forms.CharField(), required=False)
    secondary_outcomes = pgforms.SimpleArrayField(forms.CharField(), required=False)
    targeting_config_slug = forms.ChoiceField(
        choices=NimbusExperiment.TargetingConfig.choices, required=False
    )
    conclusion_recommendation = forms.ChoiceField(
        choices=NimbusExperiment.ConclusionRecommendation.choices, required=False
    )
    qa_status = forms.ChoiceField(
        choices=NimbusExperiment.QAStatus.choices,
        required=False,
        initial=NimbusExperiment.QAStatus.NOT_SET,
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


class NimbusExperimentAdmin(
    NoDeleteAdminMixin, ImportMixin, ExportActionMixin, admin.ModelAdmin[NimbusExperiment]
):
    inlines = (
        NimbusDocumentationLinkInlineAdmin,
        NimbusBranchInlineAdmin,
        NimbusExperimentBucketRangeInlineAdmin,
        NimbusExperimentChangeLogInlineAdmin,
    )
    list_display = (
        "name",
        "slug",
        "is_rollout",
        "status",
        "publish_status",
        "status_next",
        "application",
        "channel",
        "firefox_min_version",
    )
    list_filter = (
        "status",
        "publish_status",
        "is_rollout",
        "application",
        "channel",
        "feature_configs",
    )
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    form = NimbusExperimentAdminForm
    actions = [force_fetch_jetstream_data]
    resource_class = NimbusExperimentResource
    filter_horizontal = ("excluded_experiments", "required_experiments")


class NimbusFeatureVersionAdmin(
    ReadOnlyAdminMixin, admin.ModelAdmin[NimbusFeatureVersion]
):
    pass


class NimbusVersionedSchemaApplicationFilter(admin.SimpleListFilter):
    title = "application"
    parameter_name = "application"

    def lookups(self, request, model_admin):
        return NimbusExperiment.Application.choices

    def queryset(self, request, queryset):
        if self.value():
            queryset = queryset.filter(feature_config__application=self.value())

        return queryset


class NimbusVersionedSchemaAdmin(
    ReadOnlyAdminMixin, admin.ModelAdmin[NimbusVersionedSchema]
):
    @staticmethod
    def get_application(obj: NimbusVersionedSchema):
        return obj.feature_config.application

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("feature_config")

    get_application.short_description = "Application"

    list_filter = (NimbusVersionedSchemaApplicationFilter,)
    list_display = (
        "__str__",
        get_application,
    )


class NimbusVersionedSchemaInlineAdmin(
    ReadOnlyAdminMixin, admin.TabularInline[NimbusVersionedSchema]
):
    model = NimbusVersionedSchema


class NimbusFeatureConfigAdmin(ReadOnlyAdminMixin, admin.ModelAdmin[NimbusFeatureConfig]):
    prepopulated_fields = {"slug": ("name",)}
    list_filter = ("application",)
    list_display = ("name", "application")
    inlines = (NimbusVersionedSchemaInlineAdmin,)


class NimbusBranchScreenshotInlineAdmin(
    NoDeleteAdminMixin, admin.TabularInline[NimbusBranchScreenshot]
):
    model = NimbusBranchScreenshot
    extra = 0


class NimbusBranchFeatureValueInlineAdmin(
    NoDeleteAdminMixin, admin.TabularInline[NimbusBranchFeatureValue]
):
    model = NimbusBranchFeatureValue
    extra = 0


class NimbusBranchAdmin(NoDeleteAdminMixin, admin.ModelAdmin[NimbusBranch]):
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
admin.site.register(NimbusVersionedSchema, NimbusVersionedSchemaAdmin)
admin.site.register(NimbusBranch, NimbusBranchAdmin)
admin.site.register(NimbusFeatureVersion, NimbusFeatureVersionAdmin)
admin.site.register(NimbusDocumentationLink)
