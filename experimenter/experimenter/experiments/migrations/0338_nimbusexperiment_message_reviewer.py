import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def create_permissions(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    NimbusExperiment = apps.get_model("experiments", "NimbusExperiment")
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    content_type = ContentType.objects.get_for_model(NimbusExperiment)

    omc = Group.objects.create(name="OMC")
    can_perform_message_review = Permission.objects.create(
        codename="can_perform_message_review",
        name="Can perform message review",
        content_type=content_type,
    )
    omc.permissions.add(can_perform_message_review)


def delete_permissions(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    NimbusExperiment = apps.get_model("experiments", "NimbusExperiment")
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    content_type = ContentType.objects.get_for_model(NimbusExperiment)

    Group.objects.filter(name="OMC").delete()
    Permission.objects.filter(
        content_type=content_type, codename="can_perform_message_review"
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("experiments", "0337_nimbusexperiment_sizing_data"),
        ("contenttypes", "0002_remove_content_type_name"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="nimbusexperiment",
            name="message_reviewer",
            field=models.ForeignKey(
                blank=True,
                default=None,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RunPython(create_permissions, delete_permissions),
    ]
