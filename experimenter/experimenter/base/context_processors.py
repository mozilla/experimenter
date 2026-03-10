from django.utils.functional import SimpleLazyObject

from experimenter.base.models import SiteFlag, SiteFlagNameChoices


def _make_site_flag_getter(request, name):
    def get():
        site_flag = SiteFlag.objects.get_cached(request, name)
        return site_flag is not None and site_flag.value

    return get


def site_flag_enabled(request):
    return {
        "site_flag_enabled": {
            name: SimpleLazyObject(_make_site_flag_getter(request, name))
            for name in SiteFlagNameChoices
        }
    }
