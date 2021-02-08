import datetime

from django.test import TestCase

from experimenter.base.tests.factories import CountryFactory, LocaleFactory
from experimenter.experiments.api.v1.serializers import (
    ExperimentChangeLogSerializer,
    ExperimentSerializer,
    ExperimentVariantSerializer,
    JSTimestampField,
    PrefTypeField,
)
from experimenter.experiments.models import Experiment
from experimenter.experiments.tests.factories import (
    ExperimentChangeLogFactory,
    ExperimentFactory,
    ExperimentVariantFactory,
)
from experimenter.normandy.serializers import ExperimentRecipeVariantSerializer
from experimenter.projects.tests.factories import ProjectFactory


class TestJSTimestampField(TestCase):
    def test_field_serializes_to_js_time_format(self):
        field = JSTimestampField()
        example_datetime = datetime.datetime(2000, 1, 1, 1, 1, 1, 1)
        self.assertEqual(field.to_representation(example_datetime), 946688461000.0)

    def test_field_returns_none_if_no_datetime_passed_in(self):
        field = JSTimestampField()
        self.assertEqual(field.to_representation(None), None)


class TestPrefTypeField(TestCase):
    def test_non_json_field(self):
        field = PrefTypeField()
        self.assertEqual(
            field.to_representation(Experiment.PREF_TYPE_INT), Experiment.PREF_TYPE_INT
        )

    def test_json_field(self):
        field = PrefTypeField()
        self.assertEqual(
            field.to_representation(Experiment.PREF_TYPE_JSON_STR),
            Experiment.PREF_TYPE_STR,
        )


class TestExperimentVariantSerializer(TestCase):
    def test_serializer_outputs_expected_bool(self):
        experiment = ExperimentFactory(pref_type=Experiment.PREF_TYPE_BOOL)
        variant = ExperimentVariantFactory.create(experiment=experiment, value="true")
        serializer = ExperimentRecipeVariantSerializer(variant)

        self.assertEqual(type(serializer.data["value"]), bool)
        self.assertEqual(
            serializer.data, {"ratio": variant.ratio, "slug": variant.slug, "value": True}
        )

    def test_serializer_outputs_expected_int_val(self):
        experiment = ExperimentFactory(pref_type=Experiment.PREF_TYPE_INT)
        variant = ExperimentVariantFactory.create(experiment=experiment, value="28")
        serializer = ExperimentRecipeVariantSerializer(variant)

        self.assertEqual(type(serializer.data["value"]), int)
        self.assertEqual(
            serializer.data, {"ratio": variant.ratio, "slug": variant.slug, "value": 28}
        )

    def test_serializer_outputs_expected_str_val(self):
        experiment = ExperimentFactory(pref_type=Experiment.PREF_TYPE_STR)
        variant = ExperimentVariantFactory.create(experiment=experiment)
        serializer = ExperimentRecipeVariantSerializer(variant)

        self.assertEqual(type(serializer.data["value"]), str)
        self.assertEqual(
            serializer.data,
            {"ratio": variant.ratio, "slug": variant.slug, "value": variant.value},
        )


class TestExperimentSerializer(TestCase):
    def test_serializer_outputs_expected_schema(self):
        project1 = ProjectFactory.create(name="b_project1")
        project2 = ProjectFactory.create(name="a_project2")
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_COMPLETE,
            countries=[],
            locales=[],
            recipe_slug="a-normandy-slug",
            normandy_id=123,
            other_normandy_ids=[],
            results_fail_to_launch=False,
            results_failures_notes="failure notes",
            platforms=[Experiment.PLATFORM_LINUX],
            is_high_population=True,
            projects=[project1, project2],
        )

        # ensure expected_data has "string" if pref_type is json string
        pref_type = PrefTypeField().to_representation(experiment.pref_type)
        serializer = ExperimentSerializer(experiment)
        expected_data = {
            "client_matching": experiment.client_matching,
            "platforms": experiment.platforms,
            "end_date": JSTimestampField().to_representation(experiment.end_date),
            "experiment_url": experiment.experiment_url,
            "firefox_channel": experiment.firefox_channel,
            "firefox_min_version": experiment.firefox_min_version,
            "firefox_max_version": experiment.firefox_max_version,
            "name": experiment.name,
            "population": experiment.population,
            "population_percent": "{0:.4f}".format(experiment.population_percent),
            "pref_branch": experiment.pref_branch,
            "pref_name": experiment.pref_name,
            "pref_type": pref_type,
            "addon_experiment_id": experiment.addon_experiment_id,
            "addon_release_url": experiment.addon_release_url,
            "proposed_start_date": JSTimestampField().to_representation(
                experiment.proposed_start_date
            ),
            "proposed_enrollment": experiment.proposed_enrollment,
            "proposed_duration": experiment.proposed_duration,
            "public_description": experiment.public_description,
            "slug": experiment.slug,
            "start_date": JSTimestampField().to_representation(experiment.start_date),
            "status": Experiment.STATUS_COMPLETE,
            "type": experiment.type,
            "normandy_slug": experiment.recipe_slug,
            "normandy_id": experiment.normandy_id,
            "other_normandy_ids": experiment.other_normandy_ids,
            "is_high_population": experiment.is_high_population,
            "variants": [
                ExperimentVariantSerializer(variant).data
                for variant in experiment.variants.all()
            ],
            "locales": [],
            "countries": [],
            "changes": [
                ExperimentChangeLogSerializer(change).data
                for change in experiment.changes.all()
            ],
            "results": {
                "results_url": None,
                "results_initial": None,
                "results_lessons_learned": None,
                "results_fail_to_launch": False,
                "results_recipe_errors": None,
                "results_restarts": None,
                "results_low_enrollment": None,
                "results_early_end": None,
                "results_no_usable_data": None,
                "results_failures_notes": "failure notes",
                "results_changes_to_firefox": None,
                "results_data_for_hypothesis": None,
                "results_confidence": None,
                "results_measure_impact": None,
                "results_impact_notes": None,
            },
            "projects": ["a_project2", "b_project1"],
        }

        self.assertEqual(set(serializer.data.keys()), set(expected_data.keys()))
        self.assertEqual(serializer.data, expected_data)

    def test_serializer_locales(self):
        locale = LocaleFactory()
        experiment = ExperimentFactory.create(locales=[locale])
        serializer = ExperimentSerializer(experiment)
        self.assertEqual(
            serializer.data["locales"], [{"code": locale.code, "name": locale.name}]
        )

    def test_serializer_countries(self):
        country = CountryFactory()
        experiment = ExperimentFactory.create(countries=[country])
        serializer = ExperimentSerializer(experiment)
        self.assertEqual(
            serializer.data["countries"], [{"code": country.code, "name": country.name}]
        )


class TestExperimentChangeLogSerializer(TestCase):
    def test_serializer_outputs_expected_schema(self):
        change_log = ExperimentChangeLogFactory.create(
            changed_on="2019-08-02T18:19:26.267960Z"
        )
        serializer = ExperimentChangeLogSerializer(change_log)
        self.assertEqual(serializer.data["changed_on"], change_log.changed_on)
