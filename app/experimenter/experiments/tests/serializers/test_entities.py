import datetime

from django.test import TestCase

from experimenter.experiments.models import Experiment
from experimenter.experiments.tests.factories import (
    LocaleFactory,
    CountryFactory,
    ExperimentFactory,
    ExperimentVariantFactory,
    ExperimentChangeLogFactory,
)

from experimenter.experiments.serializers.entities import (
    ChangeLogSerializer,
    ExperimentChangeLogSerializer,
    JSTimestampField,
    PrefTypeField,
    ExperimentVariantSerializer,
    ExperimentSerializer,
)

from experimenter.experiments.serializers.recipe import ExperimentRecipeVariantSerializer


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
        )

        # ensure expected_data has "string" if pref_type is json string
        pref_type = PrefTypeField().to_representation(experiment.pref_type)
        serializer = ExperimentSerializer(experiment)
        expected_data = {
            "client_matching": experiment.client_matching,
            "platform": experiment.platform,
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
            "public_name": experiment.public_name,
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


class TestChangeLogSerializer(TestCase):

    def test_serializer_outputs_expected_schema(self):
        country1 = CountryFactory(code="CA", name="Canada")
        locale1 = LocaleFactory(code="da", name="Danish")
        experiment = ExperimentFactory.create(locales=[locale1], countries=[country1])

        related_exp = ExperimentFactory.create()
        experiment.related_to.add(related_exp)

        serializer = ChangeLogSerializer(experiment)

        risk_tech_description = experiment.risk_technical_description

        expected_data = {
            "type": experiment.type,
            "owner": experiment.owner.id,
            "name": experiment.name,
            "short_description": experiment.short_description,
            "related_work": experiment.related_work,
            "related_to": [related_exp.id],
            "proposed_start_date": str(experiment.proposed_start_date),
            "proposed_duration": experiment.proposed_duration,
            "proposed_enrollment": experiment.proposed_enrollment,
            "design": experiment.design,
            "addon_experiment_id": experiment.addon_experiment_id,
            "addon_release_url": experiment.addon_release_url,
            "pref_name": experiment.pref_name,
            "pref_type": experiment.pref_type,
            "pref_branch": experiment.pref_branch,
            "public_name": experiment.public_name,
            "public_description": experiment.public_description,
            "population_percent": "{0:.4f}".format(experiment.population_percent),
            "firefox_min_version": experiment.firefox_min_version,
            "firefox_max_version": experiment.firefox_max_version,
            "firefox_channel": experiment.firefox_channel,
            "client_matching": experiment.client_matching,
            "locales": [{"code": "da", "name": "Danish"}],
            "countries": [{"code": "CA", "name": "Canada"}],
            "platform": experiment.platform,
            "objectives": experiment.objectives,
            "analysis": experiment.analysis,
            "analysis_owner": experiment.analysis_owner.id,
            "survey_required": experiment.survey_required,
            "survey_urls": experiment.survey_urls,
            "survey_instructions": experiment.survey_instructions,
            "engineering_owner": experiment.engineering_owner,
            "bugzilla_id": experiment.bugzilla_id,
            "normandy_slug": experiment.normandy_slug,
            "normandy_id": experiment.normandy_id,
            "data_science_bugzilla_url": experiment.data_science_bugzilla_url,
            "feature_bugzilla_url": experiment.feature_bugzilla_url,
            "risk_partner_related": experiment.risk_partner_related,
            "risk_brand": experiment.risk_brand,
            "risk_fast_shipped": experiment.risk_fast_shipped,
            "risk_confidential": experiment.risk_confidential,
            "risk_release_population": experiment.risk_release_population,
            "risk_revenue": experiment.risk_revenue,
            "risk_data_category": experiment.risk_data_category,
            "risk_external_team_impact": experiment.risk_external_team_impact,
            "risk_telemetry_data": experiment.risk_telemetry_data,
            "risk_ux": experiment.risk_ux,
            "risk_security": experiment.risk_security,
            "risk_revision": experiment.risk_revision,
            "risk_technical": experiment.risk_technical,
            "risk_technical_description": risk_tech_description,
            "risks": experiment.risks,
            "testing": experiment.testing,
            "test_builds": experiment.test_builds,
            "qa_status": experiment.qa_status,
            "review_science": experiment.review_science,
            "review_engineering": experiment.review_engineering,
            "review_qa_requested": experiment.review_qa_requested,
            "review_intent_to_ship": experiment.review_intent_to_ship,
            "review_bugzilla": experiment.review_bugzilla,
            "review_qa": experiment.review_qa,
            "review_relman": experiment.review_relman,
            "review_advisory": experiment.review_advisory,
            "review_legal": experiment.review_legal,
            "review_ux": experiment.review_ux,
            "review_security": experiment.review_security,
            "review_vp": experiment.review_vp,
            "review_data_steward": experiment.review_data_steward,
            "review_comms": experiment.review_comms,
            "review_impacted_teams": experiment.review_impacted_teams,
            "variants": [
                ExperimentVariantSerializer(variant).data
                for variant in experiment.variants.all()
            ],
            "results_url": experiment.results_url,
            "results_initial": experiment.results_initial,
            "results_lessons_learned": experiment.results_lessons_learned,
            "rollout_playbook": experiment.rollout_playbook,
            "rollout_type": experiment.rollout_type,
        }

        self.assertEqual(set(serializer.data.keys()), set(expected_data.keys()))

        self.assertEqual(serializer.data, expected_data)
