from django.db import migrations

from experimenter.base.models import Language
from experimenter.experiments.models import NimbusExperiment


def update_languages_field_for_mobile_client(apps, schema_editor):
    NimbusExperiments = apps.get_model("experiments", "NimbusExperiment")

    for experiment in NimbusExperiments.objects.all():
        if experiment.application != NimbusExperiment.Application.DESKTOP:
            for locale in experiment.locales.all():
                locale_code = locale.code[:2]
                language = Language.objects.filter(code=locale_code).first()
                if language:

                    experiment.languages.add(language.id)
            experiment.locales.clear()
            experiment.save()


class Migration(migrations.Migration):

    dependencies = [
        ("experiments", "0211_alter_nimbusexperiment_targeting_config_slug"),
    ]

    operations = [
        migrations.RunPython(update_languages_field_for_mobile_client),
    ]
