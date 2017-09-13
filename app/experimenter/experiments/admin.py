from django import forms
from django.contrib import admin
from django.utils.html import format_html

from experimenter.experiments.models import (
    Experiment,
    ExperimentVariant,
    ExperimentChangeLog,
)


class SlugPrepopulatedMixin(object):

    def get_prepopulated_fields(self, request, obj=None):
        prepopulated_fields = dict(
            super().get_prepopulated_fields(request, obj=obj))
        readonly_fields = self.get_readonly_fields(request, obj=obj)

        if 'slug' not in readonly_fields:
            prepopulated_fields['slug'] = ('name',)

        return prepopulated_fields


class BaseVariantInlineAdmin(SlugPrepopulatedMixin, admin.StackedInline):
    max_num = 1
    model = ExperimentVariant

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj=obj)

        if obj is not None:
            db_obj = Experiment.objects.get(pk=obj.pk)
            if db_obj.is_readonly:
                readonly_fields = self.fields

        return readonly_fields

    def has_delete_permission(self, request, obj=None):
        return False

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj=obj)

        if obj is not None and obj.is_readonly:
            fieldsets = (
                (None, {
                    'fields': (
                        self.get_readonly_fields(request, obj=obj),
                    ),
                }),
            )

        return fieldsets


class ControlVariantModelForm(forms.ModelForm):

    def save(self, commit=True):
        self.instance.is_control = True
        return super().save(commit=commit)

    class Meta:
        model = ExperimentVariant
        exclude = []


class ControlVariantInlineAdmin(BaseVariantInlineAdmin):
    form = ControlVariantModelForm
    verbose_name = 'Control Variant'
    verbose_name_plural = 'Control Variant'
    fields = ('name', 'slug', 'ratio', 'description', 'value')

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_control=True)


class ExperimentVariantInlineAdmin(BaseVariantInlineAdmin):
    verbose_name = 'Experiment Variant'
    verbose_name_plural = 'Experiment Variant'
    fields = ('name', 'slug', 'ratio', 'description', 'value')

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_control=False)


class ExperimentChangeLogInlineAdmin(admin.TabularInline):
    model = ExperimentChangeLog
    readonly_fields = (
        'changed_by',
        'changed_on',
        'experiment',
        'message',
        'new_status',
        'old_status',
    )

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ExperimentAdmin(SlugPrepopulatedMixin, admin.ModelAdmin):
    inlines = (
        ControlVariantInlineAdmin,
        ExperimentVariantInlineAdmin,
        ExperimentChangeLogInlineAdmin,
    )
    list_display = (
        'name', 'project', 'status')

    fieldsets = (
        ('Overview', {
            'fields': (
                'project',
                'name',
                'slug',
                'pref_key',
                'pref_type',
                'firefox_channel',
                'firefox_version',
                'population_percent',
                'client_matching',
            ),
        }),
        ('Notes', {
            'fields': ('objectives', 'analysis'),
        }),
    )

    readonly_fields = ('show_dashboard_url',)

    def get_actions(self, request):
        return []

    def has_delete_permission(self, request, obj=None):
        return False

    def show_dashboard_url(self, obj):
        return format_html(
            '<a href="{url}" target="_blank">{url}</a>'.format(
                url=obj.dashboard_url))

    show_dashboard_url.short_description = 'Dashboard URL'

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj=obj)

        if obj is not None:
            fieldsets = (
                ('Status', {
                    'fields': (
                        ('status', 'project', 'name', 'slug'),
                        ('firefox_version', 'firefox_channel'),
                        'client_matching',
                    ),
                }),
                ('Notes', {
                    'fields': (
                        ('objectives', 'analysis'),
                    ),
                }),
            )

        return fieldsets

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj=obj)

        if obj is not None:
            db_obj = Experiment.objects.get(pk=obj.pk)

            if db_obj.is_readonly:
                readonly_fields += (
                    'client_matching',
                    'firefox_channel',
                    'firefox_version',
                    'name',
                    'project',
                    'slug',
                )

        return readonly_fields


admin.site.register(Experiment, ExperimentAdmin)
