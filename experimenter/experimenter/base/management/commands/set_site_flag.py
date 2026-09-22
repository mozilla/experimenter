from django.core.management.base import BaseCommand

from experimenter.base.models import SiteFlag, SiteFlagNameChoices


class Command(BaseCommand):
    help = "Set the value of a site flag"

    def add_arguments(self, parser):
        parser.add_argument("name", choices=SiteFlagNameChoices.names)
        parser.add_argument("value", choices=["true", "false"])

    def handle(self, *args, **options):
        SiteFlag.objects.update_or_create(
            name=options["name"],
            defaults={"value": options["value"] == "true"},
        )
