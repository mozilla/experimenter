from django.contrib import admin
from django import forms

from experimenter.experiments.models import Experiment, ExperimentVariant


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
            if db_obj.is_begun:
                readonly_fields = self.fields

        return readonly_fields

    def has_delete_permission(self, request, obj=None):
        return False


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
    fields = ('name', 'slug', 'description', 'value')

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_control=True)


class ExperimentVariantInlineAdmin(BaseVariantInlineAdmin):
    verbose_name = 'Experiment Variant'
    verbose_name_plural = 'Experiment Variant'
    fields = ('name', 'slug', 'threshold', 'description', 'value')

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_control=False)


class ExperimentAdmin(SlugPrepopulatedMixin, admin.ModelAdmin):
    inlines = (ControlVariantInlineAdmin, ExperimentVariantInlineAdmin,)
    list_display = (
        'name', 'project', 'status', 'created_date', 'start_date', 'end_date')

    fieldsets = (
        ('Overview', {
            'fields': ('project', 'name', 'slug'),
        }),
        ('Notes', {
            'fields': ('objectives', 'success_criteria', 'analysis'),
        }),
    )

    readonly_fields = ('created_date', 'start_date', 'end_date')

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj=obj)

        if obj is not None:
            fieldsets = (('Status', {
                'fields': (
                    'status', ('created_date', 'start_date', 'end_date')),
            }),) + fieldsets

        return fieldsets

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj=obj)

        if obj is not None:
            db_obj = Experiment.objects.get(pk=obj.pk)

            if db_obj.is_complete:
                readonly_fields += ('status',)

            if db_obj.is_begun:
                readonly_fields += ('project', 'name', 'slug')

        return readonly_fields


admin.site.register(Experiment, ExperimentAdmin)
