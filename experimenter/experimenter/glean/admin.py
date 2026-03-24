from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from experimenter.glean.models import Prefs


# pyright incorrectly determines StackedInline to be a generic type
class PrefsInline(admin.StackedInline):  # type: ignore
    model = Prefs
    can_delete = False


class UserAdmin(BaseUserAdmin):
    inlines = [PrefsInline]


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
