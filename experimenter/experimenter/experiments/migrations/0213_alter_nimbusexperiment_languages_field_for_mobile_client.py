from django.db import migrations


def update_languages_field_for_mobile_client(apps, schema_editor):
    NimbusExperiment = apps.get_model("experiments", "NimbusExperiment")
    Language = apps.get_model("base", "Language")

    for experiment in NimbusExperiment.objects.filter(status="Draft").exclude(
        application="firefox-desktop"
    ):
        for locale in experiment.locales.all():
            locale_code = locale.code[:2]
            language = Language.objects.filter(code=locale_code).first()
            if language:

                experiment.languages.add(language.id)
        experiment.locales.clear()


class Migration(migrations.Migration):

    dependencies = [
        ("experiments", "0212_nimbusexperiment_is_sticky"),
    ]

    operations = [
        migrations.RunPython(update_languages_field_for_mobile_client),
    ]
