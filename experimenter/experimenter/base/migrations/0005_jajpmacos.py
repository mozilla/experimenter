from django.db import migrations


def update_ja_jp_mac_locale(apps, schema_editor):
    Locale = apps.get_model("base", "Locale")

    Locale.objects.filter(code="ja-JP-mac").update(
        code="ja-JP-macos", name="Japanese (macOS)"
    )


class Migration(migrations.Migration):
    dependencies = [
        ("base", "0004_language"),
    ]

    operations = [
        migrations.RunPython(update_ja_jp_mac_locale),
    ]
