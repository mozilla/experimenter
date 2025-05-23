# Generated by Django 3.2.5 on 2021-08-05 20:41

from django.db import migrations


def remove_non_ldap_emails(apps, schema_editor):
    User = apps.get_model("auth", "User")
    User.objects.filter(
        analyzed_experiments__isnull=True,
        experimentchangelog__isnull=True,
        experimentcomment__isnull=True,
        nimbuschangelog__isnull=True,
        notifications__isnull=True,
        owned_experiments__isnull=True,
        owned_nimbusexperiments__isnull=True,
        subscribed_experiments__isnull=True,
    ).exclude(email__icontains="mozilla").exclude(email__icontains="getpocket").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("experiments", "0180_auto_20210803_1832"),
        ("notifications", "0003_auto_20190103_1849"),
    ]

    operations = [
        migrations.RunPython(remove_non_ldap_emails),
    ]
