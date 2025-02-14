from django import forms
from django.contrib import admin

from experimenter.base.models import (
    Country,
    Language,
    Locale,
    SiteFlag,
    SiteFlagNameChoices,
)


class CreateOnlyAdminMixin:
    def has_add_permission(self, request, obj=None):
        return True

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class SiteFlagAdminForm(forms.ModelForm):
    name = forms.ChoiceField(required=True, choices=SiteFlagNameChoices.choices)
    value = forms.BooleanField(required=False)

    class Meta:
        model = SiteFlag
        exclude = ("id",)


@admin.register(SiteFlag)
class SiteFlagAdmin(admin.ModelAdmin[SiteFlag]):
    form = SiteFlagAdminForm
    list_display = ("value", "description", "modified_on", "created_on")
    list_display_links = ("description",)


@admin.register(Locale)
class LocaleAdmin(CreateOnlyAdminMixin, admin.ModelAdmin[Locale]):
    pass


@admin.register(Language)
class LanguageAdmin(CreateOnlyAdminMixin, admin.ModelAdmin[Language]):
    pass


@admin.register(Country)
class CountryAdmin(CreateOnlyAdminMixin, admin.ModelAdmin[Country]):
    pass
