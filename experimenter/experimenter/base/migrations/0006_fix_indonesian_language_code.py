from django.db import migrations


def fix_indonesian_language_code(apps, schema_editor):
    Language = apps.get_model("base", "Language")

    Language.objects.filter(code="pk").update(code="id")


class Migration(migrations.Migration):
    dependencies = [
        ("base", "0005_jajpmacos"),
    ]

    operations = [
        migrations.RunPython(fix_indonesian_language_code),
    ]
