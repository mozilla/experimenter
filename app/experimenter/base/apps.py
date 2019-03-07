from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django_countries import countries
from product_details import product_details


def ensure_all_locales(sender, **kwargs):
    Locale = kwargs["apps"].get_model("base", "Locale")
    new = []
    existing = {
        code: name
        for code, name in Locale.objects.all().values_list("code", "name")
    }
    # It's important to use .items() here or else it will trigger
    # product_details.ProductDetails.__getattr__ for each key lookup.
    for code, data in product_details.languages.items():
        name = data["English"]
        if code not in existing:
            new.append(Locale(code=code, name=name))
        elif name != existing[code]:
            Locale.objects.filter(code=code).update(name=name)
    if new:
        Locale.objects.bulk_create(new)


def ensure_all_countries(sender, **kwargs):
    Country = kwargs["apps"].get_model("base", "Country")
    new = []
    existing = {
        code: name
        for code, name in Country.objects.all().values_list("code", "name")
    }
    for code, name in countries:
        if code not in existing:
            new.append(Country(code=code, name=name))
        elif name != existing[code]:
            Country.objects.filter(code=code).update(name=name)
    if new:
        Country.objects.bulk_create(new)


class BaseAppConfig(AppConfig):
    name = "experimenter.base"

    def ready(self):
        post_migrate.connect(ensure_all_locales, sender=self)
        post_migrate.connect(ensure_all_countries, sender=self)
