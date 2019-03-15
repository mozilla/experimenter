from django.core.management.base import BaseCommand
from django_countries import countries
from product_details import product_details

from experimenter.base.models import Country, Locale


class Command(BaseCommand):
    help = "Insert all necessary locales and countries"

    def handle(self, **options):
        self.ensure_all_locales()
        self.ensure_all_countries()

    @staticmethod
    def ensure_all_locales():
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

    @staticmethod
    def ensure_all_countries():
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
