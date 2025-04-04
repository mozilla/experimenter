# Generated by Django 3.2.13 on 2022-06-21 20:01

from django.db import migrations


def migrate_sticky_experiments(apps, schema_editor):
    NimbusExperiment = apps.get_model("experiments", "NimbusExperiment")

    NimbusExperiment.objects.filter(
        targeting_config_slug__in=[
            "first_run",
            "first_run_chrome",
            "first_run_win1903",
            "not_tcp_study_first_run",
            "windows_userchoice_first_run",
            "infrequent_user_uris",
            "infrequent_user_need_pin",
            "infrequent_user_need_default",
            "infrequent_user_need_default_has_pin",
            "infrequent_user_has_default_need_pin",
            "infrequent_windows_user_need_pin",
            "infrequent_win_user_uris",
            "infrequent_user_5_bookmarks",
            "casual_user_uris",
            "casual_user_need_pin",
            "casual_user_need_default",
            "casual_user_need_default_has_pin",
            "casual_user_has_default_need_pin",
            "regular_user_uris",
            "regular_user_need_pin",
            "regular_user_need_default",
            "regular_user_need_default_has_pin",
            "regular_user_has_default_need_pin",
            "regular_user_uses_fxa",
            "core_user_uris",
            "pip_never_used_sticky",
            "mobile_new_users",
            "mobile_recently_updated_users",
        ]
    ).update(is_sticky=True)

    NimbusExperiment.objects.filter(targeting_config_slug="pip_never_used_sticky").update(
        targeting_config_slug="pip_never_used"
    )


class Migration(migrations.Migration):
    dependencies = [
        ("experiments", "0213_alter_nimbusexperiment_languages_field_for_mobile_client"),
    ]

    operations = [
        migrations.RunPython(migrate_sticky_experiments),
    ]
