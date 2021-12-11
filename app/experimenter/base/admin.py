from django import forms
from django.contrib import admin

from experimenter.base.models import SiteFlag, SiteFlagNameChoices


class SiteFlagAdminForm(forms.ModelForm):
    name = forms.ChoiceField(required=True, choices=SiteFlagNameChoices.choices)
    value = forms.BooleanField(required=False)

    class Meta:
        model = SiteFlag
        exclude = ("id",)


class SiteFlagAdmin(admin.ModelAdmin):
    form = SiteFlagAdminForm
    list_display = ("value", "description", "modified_on", "created_on")
    list_display_links = ("description",)


admin.site.register(SiteFlag, SiteFlagAdmin)
