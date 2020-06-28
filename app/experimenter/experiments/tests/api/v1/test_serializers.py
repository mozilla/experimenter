import datetime
import json
import os
from jsonschema import validate
import datetime

from django.test import TestCase

from experimenter.base.tests.factories import CountryFactory, LocaleFactory
from experimenter.experiments.models import Experiment
from experimenter.experiments.tests.factories import (
    ExperimentFactory,
    ExperimentVariantFactory,
    ExperimentChangeLogFactory,
)
from experimenter.experiments.api.v1.serializers import (
    ExperimentChangeLogSerializer,
    ExperimentCSVSerializer,
    ExperimentRapidRecipeSerializer,
    ExperimentSerializer,
    ExperimentVariantSerializer,
    JSTimestampField,
    PrefTypeField,
)
from experimenter.projects.tests.factories import ProjectFactory
from experimenter.normandy.serializers import ExperimentRecipeVariantSerializer
from jsonschema import validate


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
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_COMPLETE,
            countries=[],
            locales=[],
            normandy_slug="a-normandy-slug",
            normandy_id=123,
            other_normandy_ids=[],
            results_fail_to_launch=False,
            results_failures_notes="failure notes",
            platforms=[Experiment.PLATFORM_LINUX],
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
            "normandy_slug": experiment.normandy_slug,
            "normandy_id": experiment.normandy_id,
            "other_normandy_ids": experiment.other_normandy_ids,
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
            "telemetry_event_category": experiment.telemetry_event_category,
            "telemetry_event_method": experiment.telemetry_event_method,
            "telemetry_event_object": experiment.telemetry_event_object,
            "telemetry_event_value": experiment.telemetry_event_value,
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


class TestExperimentCSVSerializer(TestCase):
    def test_serializer_outputs_expected_schema(self):
        project1 = ProjectFactory.create(name="a")
        project2 = ProjectFactory.create(name="b")
        parent = ExperimentFactory.create()
        related_experiment1 = ExperimentFactory.create(slug="a")
        related_experiment2 = ExperimentFactory.create(slug="b")
        experiment = ExperimentFactory.create(
            proposed_start_date=datetime.date(2020, 1, 1),
            parent=parent,
            projects=[project1, project2],
        )
        experiment.related_to.add(related_experiment1, related_experiment2)

        serializer = ExperimentCSVSerializer(experiment)
        self.assertDictEqual(
            serializer.data,
            {
                "name": experiment.name,
                "type": experiment.type,
                "status": experiment.status,
                "experiment_url": experiment.experiment_url,
                "public_description": experiment.public_description,
                "owner": experiment.owner.email,
                "analysis_owner": experiment.analysis_owner.email,
                "engineering_owner": experiment.engineering_owner,
                "short_description": experiment.short_description,
                "objectives": experiment.objectives,
                "parent": experiment.parent.experiment_url,
                "projects": f"{project1.name}, {project2.name}",
                "data_science_issue_url": experiment.data_science_issue_url,
                "feature_bugzilla_url": experiment.feature_bugzilla_url,
                "firefox_channel": experiment.firefox_channel,
                "normandy_slug": experiment.normandy_slug,
                "proposed_duration": experiment.proposed_duration,
                "proposed_start_date": "2020-01-01",
                "related_to": (
                    f"{related_experiment1.experiment_url}, "
                    f"{related_experiment2.experiment_url}"
                ),
                "related_work": experiment.related_work,
                "results_initial": experiment.results_initial,
                "results_url": experiment.results_url,
            },
        )


class TestExperimentRapidSerializer(TestCase):
    def test_serializer_outputs_expected_schema(self):
        audience = Experiment.RAPID_AUDIENCE_CHOICES[0][1]
        features = [feature[0] for feature in Experiment.RAPID_FEATURE_CHOICES]
        normandy_slug = "experimenter-normandy-slug"
        today = datetime.datetime.today()
        experiment = ExperimentFactory.create(
            type=Experiment.TYPE_RAPID,
            rapid_type=Experiment.RAPID_AA_CFR,
            audience=audience,
            features=features,
            normandy_slug=normandy_slug,
            proposed_enrollment=9,
            proposed_start_date=today,
        )

        ExperimentVariantFactory.create(
            experiment=experiment, slug="control", is_control=True
        )
        ExperimentVariantFactory.create(experiment=experiment, slug="variant-2")

        serializer = ExperimentRapidRecipeSerializer(experiment)
        data = serializer.data

        fn = os.path.join(os.path.dirname(__file__), "experimentRecipe.json")

        with open(fn, "r") as f:
            json_schema = json.load(f)
        self.assertIsNone(validate(instance=data, schema=json_schema))

        arguments = data.pop("arguments")
        branches = arguments.pop("branches")

        self.assertDictEqual(
            data,
            {"id": normandy_slug, "filter_expression": "AUDIENCE1", "enabled": True},
        )
        self.maxDiff = None
        self.assertDictEqual(
            dict(arguments),
            {
                "userFacingName": experiment.name,
                "userFacingDescription": experiment.public_description,
                "slug": normandy_slug,
                "active": True,
                "isEnrollmentPaused": False,
                "endDate": None,
                "proposedEnrollment": experiment.proposed_enrollment,
                "features": features,
                "referenceBranch": "control",
                "startDate": today.isoformat(),
                "bucketConfig": {
                    "count": 0,
                    "namespace": "",
                    "randomizationUnit": "normandy_id",
                    "start": 0,
                    "total": 10000,
                },
            },
        )
        converted_branches = [dict(branch) for branch in branches]
        self.assertEqual(
            converted_branches,
            [
                {"ratio": 33, "slug": "variant-2", "value": None},
                {"ratio": 33, "slug": "control", "value": None},
            ],
        )
