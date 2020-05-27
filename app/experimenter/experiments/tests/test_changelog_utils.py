from django.test import TestCase
from experimenter.experiments.models import Experiment
from experimenter.experiments.tests.factories import (
    ExperimentFactory,
    ExperimentVariantFactory,
    UserFactory,
    VariantPreferencesFactory,
)
from experimenter.experiments.changelog_utils import (
    generate_change_log,
    ChangeLogSerializer,
)


class TestChangeLogUtils(TestCase):
    def test_generate_change_log_gives_correct_output(self):
        experiment = ExperimentFactory.create_with_status(
            target_status=Experiment.STATUS_REVIEW,
            num_variants=0,
            short_description="description",
            qa_status="pretty good",
            firefox_min_version="55.0",
        )
        variant1 = ExperimentVariantFactory.create(
            experiment=experiment,
            ratio=75,
            description="variant1 description",
            name="variant1",
            slug="variant1-slug",
        )
        variant1.save()
        old_serialized_val = ChangeLogSerializer(experiment).data

        experiment.short_description = "changing the description"
        experiment.qa_status = "good"
        experiment.firefox_min_version = "56.0"
        variant2 = ExperimentVariantFactory.create(
            experiment=experiment,
            ratio=25,
            description="variant2 description",
            name="variant2",
            slug="variant2-slug",
        )
        variant2.save()

        VariantPreferencesFactory.create(
            variant=variant2,
            pref_name="p1",
            pref_type=Experiment.PREF_TYPE_INT,
            pref_branch=Experiment.PREF_BRANCH_DEFAULT,
            pref_value="5",
        )

        experiment.save()
        new_serialized_val = ChangeLogSerializer(experiment).data
        changed_variant_pref = {
            "pref_name": "p1",
            "pref_type": "integer",
            "pref_branch": "default",
            "pref_value": "5",
        }
        changed_data = {
            "short_description": "changing the description",
            "qa_status": "good",
            "firefox_min_version": "56.0",
            "variants": [
                {
                    "ratio": 25,
                    "description": "variant2 description",
                    "name": "variant2",
                    "slug": "variant2-slug",
                    "preferences": [changed_variant_pref],
                }
            ],
        }

        user = UserFactory.create()

        generate_change_log(
            old_serialized_val, new_serialized_val, experiment, changed_data, user
        )

        changed_value = experiment.changes.latest().changed_values
        expected_changed_value = {
            "firefox_min_version": {
                "display_name": "Firefox Min Version",
                "new_value": "56.0",
                "old_value": "55.0",
            },
            "qa_status": {
                "display_name": "Qa Status",
                "new_value": "good",
                "old_value": "pretty good",
            },
            "short_description": {
                "display_name": "Short Description",
                "new_value": "changing the description",
                "old_value": "description",
            },
            "variants": {
                "display_name": "Branches",
                "new_value": [
                    {
                        "ratio": 25,
                        "description": "variant2 description",
                        "name": "variant2",
                        "slug": "variant2-slug",
                    },
                    {
                        "ratio": 75,
                        "description": "variant1 description",
                        "name": "variant1",
                        "slug": "variant1-slug",
                    },
                ],
                "old_value": [
                    {
                        "ratio": 75,
                        "description": "variant1 description",
                        "name": "variant1",
                        "slug": "variant1-slug",
                    }
                ],
            },
        }
        self.assertEqual(
            expected_changed_value["firefox_min_version"],
            changed_value["firefox_min_version"],
        )
        self.assertEqual(expected_changed_value["qa_status"], changed_value["qa_status"])
        self.assertEqual(
            expected_changed_value["short_description"],
            changed_value["short_description"],
        )
        self.assertCountEqual(
            expected_changed_value["variants"], changed_value["variants"]
        )

    def test_generate_change_log_is_empty_when_no_change(self):
        experiment = ExperimentFactory.create()
        old_serialized_val = ChangeLogSerializer(experiment).data
        new_serialized_val = ChangeLogSerializer(experiment).data
        changed_data = {}
        user = UserFactory.create()
        generate_change_log(
            old_serialized_val, new_serialized_val, experiment, changed_data, user
        )
        changed_values = experiment.changes.latest().changed_values
        self.assertEqual(changed_values, {})
