from django.core.management.base import BaseCommand
from django_countries import countries
from experimenter.base.models import Country


class Command(BaseCommand):
    help = "Insert all necessary countries"

    def handle(self, **options):
        self.ensure_all_countries()

    @staticmethod
    def ensure_all_countries():
        new = []
        existing = {
            code: name for code, name in Country.objects.all().values_list("code", "name")
        }
        for code, name in countries:
            if code not in existing:
                new.append(Country(code=code, name=name))
            elif name != existing[code]:
                Country.objects.filter(code=code).update(name=name)
        if new:
            Country.objects.bulk_create(new)
