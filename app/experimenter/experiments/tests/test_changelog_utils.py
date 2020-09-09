from django.test import TestCase

from experimenter.base.tests.factories import CountryFactory, LocaleFactory
from experimenter.experiments.models import ExperimentCore, ExperimentRapid
from experimenter.experiments.tests.factories import (
    ExperimentCoreFactory,
    ExperimentRapidFactory,
    ExperimentVariantFactory,
    UserFactory,
    VariantPreferencesFactory,
)
from experimenter.experiments.changelog_utils import (
    generate_change_log,
    CoreChangeLogSerializer,
    RapidChangeLogSerializer,
)
from experimenter.projects.tests.factories import ProjectFactory


class TestCoreChangeLogSerializer(TestCase):
    def test_serializer_outputs_expected_schema(self):
        country1 = CountryFactory(code="CA", name="Canada")
        locale1 = LocaleFactory(code="da", name="Danish")
        project = ProjectFactory.create()
        experiment = ExperimentCoreFactory.create(
            locales=[locale1], countries=[country1], projects=[project]
        )

        related_exp = ExperimentCoreFactory.create()
        experiment.related_to.add(related_exp)

        serializer = CoreChangeLogSerializer(experiment)

        risk_tech_description = experiment.risk_technical_description

        expected_data = {
            "addon_experiment_id": experiment.addon_experiment_id,
            "addon_release_url": experiment.addon_release_url,
            "analysis_owner": experiment.analysis_owner.id,
            "analysis": experiment.analysis,
            "bugzilla_id": experiment.bugzilla_id,
            "client_matching": experiment.client_matching,
            "countries": [{"code": "CA", "name": "Canada"}],
            "data_science_issue_url": experiment.data_science_issue_url,
            "design": experiment.design,
            "engineering_owner": experiment.engineering_owner,
            "feature_bugzilla_url": experiment.feature_bugzilla_url,
            "firefox_channel": experiment.firefox_channel,
            "firefox_max_version": experiment.firefox_max_version,
            "firefox_min_version": experiment.firefox_min_version,
            "locales": [{"code": "da", "name": "Danish"}],
            "message_template": experiment.message_template,
            "message_type": experiment.message_type,
            "name": experiment.name,
            "normandy_id": experiment.normandy_id,
            "objectives": experiment.objectives,
            "other_normandy_ids": experiment.other_normandy_ids,
            "owner": experiment.owner.id,
            "platforms": experiment.platforms,
            "population_percent": "{0:.4f}".format(experiment.population_percent),
            "pref_branch": experiment.pref_branch,
            "pref_name": experiment.pref_name,
            "pref_type": experiment.pref_type,
            "profile_age": experiment.profile_age,
            "projects": [{"slug": project.slug}],
            "proposed_duration": experiment.proposed_duration,
            "proposed_enrollment": experiment.proposed_enrollment,
            "proposed_start_date": str(experiment.proposed_start_date),
            "public_description": experiment.public_description,
            "qa_status": experiment.qa_status,
            "recipe_slug": experiment.recipe_slug,
            "related_to": [related_exp.id],
            "related_work": experiment.related_work,
            "results_changes_to_firefox": experiment.results_changes_to_firefox,
            "results_confidence": experiment.results_confidence,
            "results_data_for_hypothesis": experiment.results_data_for_hypothesis,
            "results_early_end": experiment.results_early_end,
            "results_fail_to_launch": experiment.results_fail_to_launch,
            "results_failures_notes": experiment.results_failures_notes,
            "results_impact_notes": experiment.results_impact_notes,
            "results_initial": experiment.results_initial,
            "results_lessons_learned": experiment.results_lessons_learned,
            "results_low_enrollment": experiment.results_low_enrollment,
            "results_measure_impact": experiment.results_measure_impact,
            "results_no_usable_data": experiment.results_no_usable_data,
            "results_recipe_errors": experiment.results_recipe_errors,
            "results_restarts": experiment.results_restarts,
            "results_url": experiment.results_url,
            "review_advisory": experiment.review_advisory,
            "review_bugzilla": experiment.review_bugzilla,
            "review_comms": experiment.review_comms,
            "review_data_steward": experiment.review_data_steward,
            "review_engineering": experiment.review_engineering,
            "review_impacted_teams": experiment.review_impacted_teams,
            "review_intent_to_ship": experiment.review_intent_to_ship,
            "review_legal": experiment.review_legal,
            "review_qa_requested": experiment.review_qa_requested,
            "review_qa": experiment.review_qa,
            "review_relman": experiment.review_relman,
            "review_science": experiment.review_science,
            "review_security": experiment.review_security,
            "review_ux": experiment.review_ux,
            "review_vp": experiment.review_vp,
            "risk_brand": experiment.risk_brand,
            "risk_confidential": experiment.risk_confidential,
            "risk_data_category": experiment.risk_data_category,
            "risk_external_team_impact": experiment.risk_external_team_impact,
            "risk_fast_shipped": experiment.risk_fast_shipped,
            "risk_partner_related": experiment.risk_partner_related,
            "risk_release_population": experiment.risk_release_population,
            "risk_revenue": experiment.risk_revenue,
            "risk_revision": experiment.risk_revision,
            "risk_security": experiment.risk_security,
            "risk_technical_description": risk_tech_description,
            "risk_technical": experiment.risk_technical,
            "risk_telemetry_data": experiment.risk_telemetry_data,
            "risk_ux": experiment.risk_ux,
            "risks": experiment.risks,
            "rollout_playbook": experiment.rollout_playbook,
            "rollout_type": experiment.rollout_type,
            "short_description": experiment.short_description,
            "survey_instructions": experiment.survey_instructions,
            "survey_required": experiment.survey_required,
            "survey_urls": experiment.survey_urls,
            "test_builds": experiment.test_builds,
            "testing": experiment.testing,
            "total_enrolled_clients": experiment.total_enrolled_clients,
            "type": experiment.type,
            "windows_versions": experiment.windows_versions,
            "variants": [
                {
                    "description": variant.description,
                    "is_control": variant.is_control,
                    "name": variant.name,
                    "ratio": variant.ratio,
                    "slug": variant.slug,
                    "value": variant.value,
                    "addon_release_url": variant.addon_release_url,
                    "preferences": [
                        {
                            "pref_name": preference.pref_name,
                            "pref_type": preference.pref_type,
                            "pref_branch": preference.pref_branch,
                            "pref_value": preference.pref_value,
                        }
                        for preference in variant.preferences.all()
                    ],
                    "message_targeting": variant.message_targeting,
                    "message_threshold": variant.message_threshold,
                    "message_triggers": variant.message_triggers,
                }
                for variant in experiment.variants.all()
            ],
        }

        self.assertDictEqual(serializer.data, expected_data)


class TestRapidChangeLogSerializer(TestCase):
    def test_serializer_outputs_expected_schema(self):
        experiment = ExperimentRapidFactory.create_with_status(
            ExperimentRapid.STATUS_DRAFT
        )
        serializer = RapidChangeLogSerializer(experiment)

        self.maxDiff = None
        expected_data = {
            "archived": experiment.archived,
            "audience": experiment.audience,
            "bugzilla_id": experiment.bugzilla_id,
            "features": experiment.features,
            "firefox_channel": experiment.firefox_channel,
            "firefox_max_version": experiment.firefox_max_version,
            "firefox_min_version": experiment.firefox_min_version,
            "is_paused": experiment.is_paused,
            "name": experiment.name,
            "objectives": experiment.objectives,
            "owner": experiment.owner.id,
            "proposed_duration": experiment.proposed_duration,
            "proposed_enrollment": experiment.proposed_enrollment,
            "proposed_start_date": experiment.proposed_start_date,
            "public_description": experiment.public_description,
            "rapid_type": experiment.rapid_type,
            "recipe_slug": experiment.recipe_slug,
            "short_description": experiment.short_description,
            "slug": experiment.slug,
            "status": experiment.status,
            "variants": [
                {
                    "description": variant.description,
                    "is_control": variant.is_control,
                    "name": variant.name,
                    "ratio": variant.ratio,
                    "slug": variant.slug,
                    "value": variant.value,
                    "addon_release_url": None,
                    "preferences": [],
                    "message_targeting": None,
                    "message_threshold": None,
                    "message_triggers": None,
                }
                for variant in experiment.variants.all()
            ],
        }

        self.assertDictEqual(serializer.data, expected_data)


class TestChangeLogUtils(TestCase):
    def test_generate_change_log_gives_correct_output(self):
        experiment = ExperimentCoreFactory.create_with_status(
            target_status=ExperimentCore.STATUS_REVIEW,
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
        old_serialized_val = CoreChangeLogSerializer(experiment).data

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
            pref_type=ExperimentCore.PREF_TYPE_INT,
            pref_branch=ExperimentCore.PREF_BRANCH_DEFAULT,
            pref_value="5",
        )

        experiment.save()
        new_serialized_val = CoreChangeLogSerializer(experiment).data
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
        experiment = ExperimentCoreFactory.create()
        old_serialized_val = CoreChangeLogSerializer(experiment).data
        new_serialized_val = CoreChangeLogSerializer(experiment).data
        changed_data = {}
        user = UserFactory.create()
        generate_change_log(
            old_serialized_val, new_serialized_val, experiment, changed_data, user
        )
        changed_values = experiment.changes.latest().changed_values
        self.assertEqual(changed_values, {})
