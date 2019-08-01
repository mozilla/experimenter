import datetime
from decimal import Decimal

from django.test import TestCase

from experimenter.experiments.models import Experiment
from experimenter.experiments.tests.factories import (
    LocaleFactory,
    CountryFactory,
    ExperimentFactory,
    ExperimentVariantFactory,
)
from experimenter.experiments.serializers import (
    CountrySerializer,
    ChangeLogSerializer,
    ExperimentRecipeAddonArgumentsSerializer,
    ExperimentRecipePrefArgumentsSerializer,
    ExperimentRecipeSerializer,
    ExperimentRecipeVariantSerializer,
    ExperimentSerializer,
    ExperimentVariantSerializer,
    FilterObjectBucketSampleSerializer,
    FilterObjectChannelSerializer,
    FilterObjectCountrySerializer,
    FilterObjectLocaleSerializer,
    FilterObjectVersionsSerializer,
    JSTimestampField,
    PrefTypeField,
    LocaleSerializer,
    ExperimentCloneSerializer,
)

from experimenter.experiments.tests.mixins import MockRequestMixin


class TestJSTimestampField(TestCase):

    def test_field_serializes_to_js_time_format(self):
        field = JSTimestampField()
        example_datetime = datetime.datetime(2000, 1, 1, 1, 1, 1, 1)
        self.assertEqual(
            field.to_representation(example_datetime), 946688461000.0
        )

    def test_field_returns_none_if_no_datetime_passed_in(self):
        field = JSTimestampField()
        self.assertEqual(field.to_representation(None), None)


class TestPrefTypeField(TestCase):

    def test_non_json_field(self):
        field = PrefTypeField()
        self.assertEqual(
            field.to_representation(Experiment.PREF_TYPE_INT),
            Experiment.PREF_TYPE_INT,
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
        variant = ExperimentVariantFactory.create(
            experiment=experiment, value="true"
        )
        serializer = ExperimentRecipeVariantSerializer(variant)

        self.assertEqual(type(serializer.data["value"]), bool)
        self.assertEqual(
            serializer.data,
            {"ratio": variant.ratio, "slug": variant.slug, "value": True},
        )

    def test_serializer_outputs_expected_int_val(self):
        experiment = ExperimentFactory(pref_type=Experiment.PREF_TYPE_INT)
        variant = ExperimentVariantFactory.create(
            experiment=experiment, value="28"
        )
        serializer = ExperimentRecipeVariantSerializer(variant)

        self.assertEqual(type(serializer.data["value"]), int)
        self.assertEqual(
            serializer.data,
            {"ratio": variant.ratio, "slug": variant.slug, "value": 28},
        )

    def test_serializer_outputs_expected_str_val(self):
        experiment = ExperimentFactory(pref_type=Experiment.PREF_TYPE_STR)
        variant = ExperimentVariantFactory.create(experiment=experiment)
        serializer = ExperimentRecipeVariantSerializer(variant)

        self.assertEqual(type(serializer.data["value"]), str)
        self.assertEqual(
            serializer.data,
            {
                "ratio": variant.ratio,
                "slug": variant.slug,
                "value": variant.value,
            },
        )


class TestLocaleSerializer(TestCase):

    def test_serializer_outputs_expected_schema(self):
        locale = LocaleFactory.create()
        serializer = LocaleSerializer(locale)
        self.assertEqual(
            serializer.data, {"code": locale.code, "name": locale.name}
        )


class TestChangeLogSerializer(TestCase):

    def test_serializer_outputs_expected_schema(self):
        country1 = CountryFactory(code="CA", name="Canada")
        locale1 = LocaleFactory(code="da", name="Danish")
        experiment = ExperimentFactory.create(
            locales=[locale1], countries=[country1]
        )

        serializer = ChangeLogSerializer(experiment)

        risk_tech_description = experiment.risk_technical_description

        expected_data = {
            "type": experiment.type,
            "status": experiment.status,
            "owner": experiment.owner.id,
            "name": experiment.name,
            "short_description": experiment.short_description,
            "related_work": experiment.related_work,
            "proposed_start_date": str(experiment.proposed_start_date),
            "proposed_duration": experiment.proposed_duration,
            "proposed_enrollment": experiment.proposed_enrollment,
            "addon_experiment_id": experiment.addon_experiment_id,
            "addon_release_url": experiment.addon_release_url,
            "pref_key": experiment.pref_key,
            "pref_type": experiment.pref_type,
            "pref_branch": experiment.pref_branch,
            "public_name": experiment.public_name,
            "public_description": experiment.public_description,
            "population_percent": "{0:.4f}".format(
                experiment.population_percent
            ),
            "firefox_min_version": experiment.firefox_min_version,
            "firefox_max_version": experiment.firefox_max_version,
            "firefox_channel": experiment.firefox_channel,
            "client_matching": experiment.client_matching,
            "locales": [{"code": "da", "name": "Danish"}],
            "countries": [{"code": "CA", "name": "Canada"}],
            "platform": experiment.platform,
            "objectives": experiment.objectives,
            "analysis": experiment.analysis,
            "analysis_owner": experiment.analysis_owner,
            "survey_required": experiment.survey_required,
            "survey_urls": experiment.survey_urls,
            "survey_instructions": experiment.survey_instructions,
            "engineering_owner": experiment.engineering_owner,
            "bugzilla_id": experiment.bugzilla_id,
            "slug": experiment.slug,
            "normandy_slug": experiment.normandy_slug,
            "normandy_id": experiment.normandy_id,
            "data_science_bugzilla_url": experiment.data_science_bugzilla_url,
            "feature_bugzilla_url": experiment.feature_bugzilla_url,
            "risk_internal_only": experiment.risk_internal_only,
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
        }

        self.assertEqual(
            set(serializer.data.keys()), set(expected_data.keys())
        )

        self.assertEqual(serializer.data, expected_data)


class TestCountrySerializer(TestCase):

    def test_serializer_outputs_expected_schema(self):
        country = CountryFactory.create()
        serializer = CountrySerializer(country)
        self.assertEqual(
            serializer.data, {"code": country.code, "name": country.name}
        )


class TestExperimentSerializer(TestCase):

    def test_serializer_outputs_expected_schema(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_COMPLETE, countries=[], locales=[]
        )
        serializer = ExperimentSerializer(experiment)
        expected_data = {
            "analysis": experiment.analysis,
            "analysis_owner": experiment.analysis_owner,
            "client_matching": experiment.client_matching,
            "platform": experiment.platform,
            "end_date": JSTimestampField().to_representation(
                experiment.end_date
            ),
            "experiment_url": experiment.experiment_url,
            "firefox_channel": experiment.firefox_channel,
            "firefox_min_version": experiment.firefox_min_version,
            "firefox_max_version": experiment.firefox_max_version,
            "name": experiment.name,
            "objectives": experiment.objectives,
            "population": experiment.population,
            "population_percent": "{0:.4f}".format(
                experiment.population_percent
            ),
            "pref_branch": experiment.pref_branch,
            "pref_key": experiment.pref_key,
            "pref_type": experiment.pref_type,
            "addon_experiment_id": experiment.addon_experiment_id,
            "addon_release_url": experiment.addon_release_url,
            "proposed_start_date": JSTimestampField().to_representation(
                experiment.proposed_start_date
            ),
            "proposed_enrollment": experiment.proposed_enrollment,
            "proposed_duration": experiment.proposed_duration,
            "short_description": experiment.short_description,
            "slug": experiment.slug,
            "start_date": JSTimestampField().to_representation(
                experiment.start_date
            ),
            "status": Experiment.STATUS_COMPLETE,
            "type": experiment.type,
            "variants": [
                ExperimentVariantSerializer(variant).data
                for variant in experiment.variants.all()
            ],
            "locales": [],
            "countries": [],
        }

        self.assertEqual(
            set(serializer.data.keys()), set(expected_data.keys())
        )
        self.assertEqual(serializer.data, expected_data)

    def test_serializer_locales(self):
        locale = LocaleFactory()
        experiment = ExperimentFactory.create(locales=[locale])
        serializer = ExperimentSerializer(experiment)
        self.assertEqual(
            serializer.data["locales"],
            [{"code": locale.code, "name": locale.name}],
        )

    def test_serializer_countries(self):
        country = CountryFactory()
        experiment = ExperimentFactory.create(countries=[country])
        serializer = ExperimentSerializer(experiment)
        self.assertEqual(
            serializer.data["countries"],
            [{"code": country.code, "name": country.name}],
        )


class TestFilterObjectBucketSampleSerializer(TestCase):

    def test_serializer_outputs_expected_schema(self):
        experiment = ExperimentFactory.create(
            population_percent=Decimal("12.34")
        )
        serializer = FilterObjectBucketSampleSerializer(experiment)
        self.assertEqual(
            serializer.data,
            {
                "type": "bucketSample",
                "input": ["normandy.recipe.id", "normandy.userId"],
                "start": 0,
                "count": 1234,
                "total": 10000,
            },
        )


class TestFilterObjectChannelSerializer(TestCase):

    def test_serializer_outputs_expected_schema(self):
        experiment = ExperimentFactory.create(
            firefox_channel=Experiment.CHANNEL_NIGHTLY
        )
        serializer = FilterObjectChannelSerializer(experiment)
        self.assertEqual(
            serializer.data, {"type": "channel", "channels": ["nightly"]}
        )


class TestFilterObjectVersionsSerializer(TestCase):

    def test_serializer_outputs_version_string_with_only_min(self):
        experiment = ExperimentFactory.create(
            firefox_min_version="68.0", firefox_max_version=""
        )
        serializer = FilterObjectVersionsSerializer(experiment)
        self.assertEqual(
            serializer.data, {"type": "version", "versions": [68]}
        )

    def test_serializer_outputs_version_string_with_range(self):
        experiment = ExperimentFactory.create(
            firefox_min_version="68.0", firefox_max_version="70.0"
        )
        serializer = FilterObjectVersionsSerializer(experiment)
        self.assertEqual(
            serializer.data, {"type": "version", "versions": [68, 69, 70]}
        )


class TestFilterObjectLocaleSerializer(TestCase):

    def test_serializer_outputs_expected_schema(self):
        locale1 = LocaleFactory.create(code="ab")
        locale2 = LocaleFactory.create(code="cd")
        experiment = ExperimentFactory.create(locales=[locale1, locale2])
        serializer = FilterObjectLocaleSerializer(experiment)
        self.assertEqual(serializer.data["type"], "locale")
        self.assertEqual(set(serializer.data["locales"]), set(["ab", "cd"]))


class TestFilterObjectCountrySerializer(TestCase):

    def test_serializer_outputs_expected_schema(self):
        country1 = CountryFactory.create(code="ab")
        country2 = CountryFactory.create(code="cd")
        experiment = ExperimentFactory.create(countries=[country1, country2])
        serializer = FilterObjectCountrySerializer(experiment)
        self.assertEqual(serializer.data["type"], "country")
        self.assertEqual(set(serializer.data["countries"]), set(["ab", "cd"]))


class TestExperimentRecipeVariantSerializer(TestCase):

    def test_serializer_outputs_expected_schema(self):
        experiment = ExperimentFactory(pref_type=Experiment.PREF_TYPE_STR)
        variant = ExperimentVariantFactory.create(experiment=experiment)
        serializer = ExperimentRecipeVariantSerializer(variant)
        self.assertEqual(
            serializer.data,
            {
                "ratio": variant.ratio,
                "slug": variant.slug,
                "value": variant.value,
            },
        )


class TestExperimentRecipePrefArgumentsSerializer(TestCase):

    def test_serializer_outputs_expected_schema(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_SHIP
        )
        serializer = ExperimentRecipePrefArgumentsSerializer(experiment)
        self.assertEqual(
            serializer.data,
            {
                "preferenceBranchType": experiment.pref_branch,
                "slug": experiment.normandy_slug,
                "experimentDocumentUrl": experiment.experiment_url,
                "preferenceName": experiment.pref_key,
                "preferenceType": experiment.pref_type,
                "branches": [
                    ExperimentRecipeVariantSerializer(variant).data
                    for variant in experiment.variants.all()
                ],
            },
        )


class TestExperimentRecipeAddonArgumentsSerializer(TestCase):

    def test_serializer_outputs_expected_schema(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_SHIP
        )
        serializer = ExperimentRecipeAddonArgumentsSerializer(experiment)
        self.assertEqual(
            serializer.data,
            {
                "name": experiment.addon_experiment_id,
                "description": experiment.public_description,
            },
        )


class TestExperimentRecipeSerializer(TestCase):

    def test_serializer_outputs_expected_schema_for_pref_experiment(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_SHIP,
            type=Experiment.TYPE_PREF,
            locales=[LocaleFactory.create()],
            countries=[CountryFactory.create()],
        )
        serializer = ExperimentRecipeSerializer(experiment)
        self.assertEqual(
            serializer.data["action_name"], "preference-experiment"
        )
        self.assertEqual(serializer.data["name"], experiment.name)
        self.assertEqual(
            serializer.data["comment"], experiment.client_matching
        )
        self.assertEqual(
            serializer.data["filter_object"],
            [
                FilterObjectBucketSampleSerializer(experiment).data,
                FilterObjectChannelSerializer(experiment).data,
                FilterObjectVersionsSerializer(experiment).data,
                FilterObjectLocaleSerializer(experiment).data,
                FilterObjectCountrySerializer(experiment).data,
            ],
        )
        self.assertEqual(
            serializer.data["arguments"],
            ExperimentRecipePrefArgumentsSerializer(experiment).data,
        )

    def test_serializer_outputs_expected_schema_for_addon_experiment(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_SHIP,
            type=Experiment.TYPE_ADDON,
            locales=[LocaleFactory.create()],
            countries=[CountryFactory.create()],
        )
        serializer = ExperimentRecipeSerializer(experiment)
        self.assertEqual(serializer.data["action_name"], "opt-out-study")
        self.assertEqual(serializer.data["name"], experiment.name)
        self.assertEqual(
            serializer.data["comment"], experiment.client_matching
        )
        self.assertEqual(
            serializer.data["filter_object"],
            [
                FilterObjectBucketSampleSerializer(experiment).data,
                FilterObjectChannelSerializer(experiment).data,
                FilterObjectVersionsSerializer(experiment).data,
                FilterObjectLocaleSerializer(experiment).data,
                FilterObjectCountrySerializer(experiment).data,
            ],
        )
        self.assertEqual(
            serializer.data["arguments"],
            ExperimentRecipeAddonArgumentsSerializer(experiment).data,
        )

    def test_serializer_excludes_locales_if_none_set(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_SHIP, type=Experiment.TYPE_ADDON
        )
        experiment.locales.all().delete()
        serializer = ExperimentRecipeSerializer(experiment)
        filter_object_types = [
            f["type"] for f in serializer.data["filter_object"]
        ]
        self.assertNotIn("locale", filter_object_types)

    def test_serializer_excludes_countries_if_none_set(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_SHIP, type=Experiment.TYPE_ADDON
        )
        experiment.countries.all().delete()
        serializer = ExperimentRecipeSerializer(experiment)
        filter_object_types = [
            f["type"] for f in serializer.data["filter_object"]
        ]
        self.assertNotIn("country", filter_object_types)


class TestCloneSerializer(MockRequestMixin, TestCase):

    def test_clone_serializer_rejects_duplicate_slug(self):
        experiment_1 = ExperimentFactory.create(
            name="good experiment", slug="great-experiment"
        )
        clone_data = {"name": "great experiment"}
        serializer = ExperimentCloneSerializer(
            instance=experiment_1, data=clone_data
        )

        self.assertFalse(serializer.is_valid())

    def test_clone_serializer_rejects_duplicate_name(self):
        experiment = ExperimentFactory.create(
            name="wonderful experiment", slug="amazing-experiment"
        )
        clone_data = {"name": "wonderful experiment"}
        serializer = ExperimentCloneSerializer(
            instance=experiment, data=clone_data
        )

        self.assertFalse(serializer.is_valid())

    def test_clone_serializer_rejects_invalid_name(self):
        experiment = ExperimentFactory.create(
            name="great experiment", slug="great-experiment"
        )

        clone_data = {"name": "@@@@@@@@"}
        serializer = ExperimentCloneSerializer(
            instance=experiment, data=clone_data
        )

        self.assertFalse(serializer.is_valid())

    def test_clone_serializer_accepts_unique_name(self):
        experiment = ExperimentFactory.create(
            name="great experiment", slug="great-experiment"
        )
        clone_data = {"name": "best experiment"}
        serializer = ExperimentCloneSerializer(
            instance=experiment,
            data=clone_data,
            context={"request": self.request},
        )
        self.assertTrue(serializer.is_valid())

        serializer.save()

        self.assertEqual(serializer.data["name"], "best experiment")
        self.assertEqual(
            serializer.data["clone_url"], "/experiments/best-experiment/"
        )
