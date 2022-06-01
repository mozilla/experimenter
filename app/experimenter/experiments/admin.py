from django import forms
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.postgres.forms import SimpleArrayField
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
    NimbusIsolationGroup,
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
        headers = []
        for field in self.get_export_fields():
            if force_text(field.column_name) in skip_list:
                continue
            headers.append(force_text(field.column_name))
        return headers

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

    def before_import_row(self, row: dict, row_number=None, **kwargs):
        owner_id = row.get("owner")
        user_model = get_user_model()

        try:
            user_model.objects.get(id=owner_id)
        except user_model.DoesNotExist:
            # use dev testing user as default
            (dev_user, _) = user_model.objects.get_or_create(email=DEV_USER_EMAIL)
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
    firefox_max_version = forms.ChoiceField(
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


class NimbusExperimentAdmin(
    NoDeleteAdminMixin, ImportMixin, ExportActionMixin, admin.ModelAdmin
):
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

    resource_class = NimbusExperimentResource


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
