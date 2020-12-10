import json

import jsonschema
from django import forms
from django.contrib import admin

from experimenter.experiments.models import (
    NimbusBranch,
    NimbusChangeLog,
    NimbusExperiment,
    NimbusExperimentProbeSets,
    NimbusFeatureConfig,
    NimbusProbe,
    NimbusProbeSet,
)


class NimbusBranchAdminForm(forms.ModelForm):
    class Meta:
        model = NimbusBranch
        exclude = ("id",)

    def clean_feature_value(self):
        feature_value = self.cleaned_data["feature_value"]
        feature_config = self.cleaned_data["experiment"].feature_config

        if feature_value and feature_config:
            feature_schema = json.loads(
                self.cleaned_data["experiment"].feature_config.schema
            )

            try:
                json_value = json.loads(feature_value)
            except json.JSONDecodeError as e:
                raise forms.ValidationError(f"Invaid JSON: {e}")

            if json_value:
                try:
                    jsonschema.validate(json_value, feature_schema)
                except jsonschema.ValidationError as e:
                    raise forms.ValidationError(f"Does not match feature schema: {e}")

        return feature_value


class NimbusBranchInlineAdmin(admin.StackedInline):
    model = NimbusBranch
    extra = 0
    form = NimbusBranchAdminForm


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


class NimbusProbeSetInlineAdmin(admin.TabularInline):
    model = NimbusExperimentProbeSets
    extra = 0


class NimbusExperimentAdmin(admin.ModelAdmin):
    inlines = (
        NimbusBranchInlineAdmin,
        NimbusProbeSetInlineAdmin,
        NimbusExperimentChangeLogInlineAdmin,
    )
    list_display = ("name", "status", "application", "channel", "firefox_min_version")
    list_filter = ("status", "application")
    prepopulated_fields = {"slug": ("name",)}
    form = NimbusExperimentAdminForm


class NimbusFeatureConfigAdminForm(forms.ModelForm):
    class Meta:
        model = NimbusFeatureConfig
        exclude = ("id",)

    def clean_schema(self):
        schema = self.cleaned_data["schema"]

        try:
            json.loads(schema)
        except json.JSONDecodeError as e:
            raise forms.ValidationError(f"Invaid JSON: {e}")

        return schema


class NimbusFeatureConfigAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    form = NimbusFeatureConfigAdminForm


admin.site.register(NimbusExperiment, NimbusExperimentAdmin)
admin.site.register(NimbusFeatureConfig, NimbusFeatureConfigAdmin)
admin.site.register(NimbusProbe)
admin.site.register(NimbusProbeSet)
