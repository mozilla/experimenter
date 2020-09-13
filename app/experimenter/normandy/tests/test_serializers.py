from decimal import Decimal

from django.test import TestCase

from experimenter.base.tests.factories import CountryFactory, LocaleFactory
from experimenter.experiments.api.v1.serializers import PrefTypeField
from experimenter.experiments.models import (
    Experiment,
    ExperimentVariant,
    RolloutPreference,
)
from experimenter.experiments.tests.factories import (
    ExperimentFactory,
    ExperimentVariantFactory,
    VariantPreferencesFactory,
)
from experimenter.normandy.serializers import (
    ExperimentRecipeAddonArgumentsSerializer,
    ExperimentRecipeAddonRolloutArgumentsSerializer,
    ExperimentRecipeAddonVariantSerializer,
    ExperimentRecipeMessageArgumentsSerializer,
    ExperimentRecipeMessageVariantSerializer,
    ExperimentRecipeMultiPrefVariantSerializer,
    ExperimentRecipePrefArgumentsSerializer,
    ExperimentRecipePrefRolloutArgumentsSerializer,
    ExperimentRecipeSerializer,
    ExperimentRecipeVariantSerializer,
    FilterObjectBucketSampleSerializer,
    FilterObjectChannelSerializer,
    FilterObjectCountrySerializer,
    FilterObjectLocaleSerializer,
    FilterObjectVersionsSerializer,
    PrefValueField,
)


class TestPrefValueField(TestCase):
    def test_variant_pref_value_returns_int_when_type_is_int(self):
        experiment = ExperimentFactory.create(pref_type=Experiment.PREF_TYPE_INT)
        variant = ExperimentVariantFactory.create(experiment=experiment, value="8")
        value = PrefValueField(
            type_field="experiment__pref_type", value_field="value"
        ).to_representation(variant)
        self.assertEqual(value, 8)

    def test_variant_pref_value_returns_bool_when_type_is_bool(self):
        experiment = ExperimentFactory.create(pref_type=Experiment.PREF_TYPE_BOOL)
        variant = ExperimentVariantFactory.create(experiment=experiment, value="false")
        value = PrefValueField(
            type_field="experiment__pref_type", value_field="value"
        ).to_representation(variant)
        self.assertEqual(value, False)

    def test_variant_pref_value_str_returns_bool_when_type_is_str(self):
        experiment = ExperimentFactory.create(pref_type=Experiment.PREF_TYPE_STR)
        variant = ExperimentVariantFactory.create(
            experiment=experiment, value="it's a string"
        )
        value = PrefValueField(
            type_field="experiment__pref_type", value_field="value"
        ).to_representation(variant)
        self.assertEqual(value, "it's a string")

    def test_variantpref_pref_value_returns_bool_when_type_is_bool(self):
        vp = VariantPreferencesFactory.create(
            pref_type=Experiment.PREF_TYPE_BOOL, pref_value="false"
        )
        value = PrefValueField(
            type_field="pref_type", value_field="pref_value"
        ).to_representation(vp)
        self.assertEqual(value, False)

    def test_variantpref_pref_value_returns_int_when_type_is_int(self):
        vp = VariantPreferencesFactory.create(
            pref_type=Experiment.PREF_TYPE_INT, pref_value="22"
        )
        value = PrefValueField(
            type_field="pref_type", value_field="pref_value"
        ).to_representation(vp)
        self.assertEqual(value, 22)

    def test_variantpref_pref_value_returns_str_when_type_is_str(self):
        vp = VariantPreferencesFactory.create(
            pref_type=Experiment.PREF_TYPE_STR, pref_value="it's another string"
        )
        value = PrefValueField(
            type_field="pref_type", value_field="pref_value"
        ).to_representation(vp)
        self.assertEqual(value, "it's another string")


class TestFilterObjectBucketSampleSerializer(TestCase):
    def test_serializer_outputs_expected_schema(self):
        experiment = ExperimentFactory.create(population_percent=Decimal("12.34"))
        serializer = FilterObjectBucketSampleSerializer(experiment)
        self.assertDictEqual(
            serializer.data,
            {
                "type": "bucketSample",
                "input": ["normandy.userId"],
                "start": 0,
                "count": 1234,
                "total": 10000,
            },
        )


class TestFilterObjectChannelSerializer(TestCase):
    def test_serializer_outputs_expected_schema(self):
        experiment = ExperimentFactory.create(firefox_channel=Experiment.CHANNEL_NIGHTLY)
        serializer = FilterObjectChannelSerializer(experiment)
        self.assertDictEqual(
            serializer.data, {"type": "channel", "channels": ["nightly"]}
        )


class TestFilterObjectVersionsSerializer(TestCase):
    def test_serializer_outputs_version_string_with_only_min(self):
        experiment = ExperimentFactory.create(
            firefox_min_version="68.0", firefox_max_version=""
        )
        serializer = FilterObjectVersionsSerializer(experiment)
        self.assertDictEqual(serializer.data, {"type": "version", "versions": [68]})

    def test_serializer_outputs_version_string_with_range(self):
        experiment = ExperimentFactory.create(
            firefox_min_version="68.0", firefox_max_version="70.0"
        )
        serializer = FilterObjectVersionsSerializer(experiment)
        self.assertDictEqual(
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


class TestExperimentRecipeAddonVariantSerializer(TestCase):
    def test_serializer_outputs_expected_schema(self):
        variant = ExperimentVariant(slug="slug-value", ratio=25)
        serializer = ExperimentRecipeAddonVariantSerializer(variant)
        self.assertDictEqual(
            {"ratio": 25, "slug": "slug-value", "extensionApiId": None}, serializer.data
        )


class TestExperimentRecipeAddonArgumentsSerializer(TestCase):
    def test_serializer_outputs_expected_schema(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_SHIP, type=Experiment.TYPE_ADDON
        )
        serializer = ExperimentRecipeAddonArgumentsSerializer(experiment)
        self.assertDictEqual(
            serializer.data,
            {
                "name": experiment.addon_experiment_id,
                "description": experiment.public_description,
            },
        )


class TestExperimentRecipeAddonRolloutArgumentsSerializer(TestCase):
    def test_serializer_outputs_expected_schema(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_SHIP,
            type=Experiment.TYPE_ROLLOUT,
            rollout_type=Experiment.TYPE_ADDON,
            addon_release_url="https://www.example.com/addon.xpi",
        )
        serializer = ExperimentRecipeAddonRolloutArgumentsSerializer(experiment)
        self.assertDictEqual(
            serializer.data,
            {
                "slug": experiment.recipe_slug,
                "extensionApiId": "TODO: https://www.example.com/addon.xpi",
            },
        )


class TestExperimentRecipePrefRolloutArgumentsSerializer(TestCase):
    def test_serializer_outputs_expected_schema_for_int(self):

        experiment = ExperimentFactory.create(
            type=Experiment.TYPE_ROLLOUT,
            recipe_slug="normandy-slug",
            rollout_type=Experiment.TYPE_PREF,
        )

        preference = RolloutPreference(
            pref_type=Experiment.PREF_TYPE_INT,
            pref_name="browser.pref",
            pref_value="4",
            experiment=experiment,
        )

        preference.save()

        experiment = Experiment.objects.get(recipe_slug="normandy-slug")
        serializer = ExperimentRecipePrefRolloutArgumentsSerializer(experiment)

        serializer_data = serializer.data

        self.assertEqual(serializer_data["slug"], "normandy-slug")

        self.assertDictEqual(
            dict(serializer_data["preferences"][0]),
            {"preferenceName": "browser.pref", "value": 4},
        )

    def test_serializer_outputs_expected_schema_for_bool(self):
        experiment = ExperimentFactory.create(
            type=Experiment.TYPE_ROLLOUT,
            recipe_slug="normandy-slug",
            rollout_type=Experiment.TYPE_PREF,
        )

        preference = RolloutPreference(
            pref_type=Experiment.PREF_TYPE_BOOL,
            pref_name="browser.pref",
            pref_value="true",
            experiment=experiment,
        )

        preference.save()
        serializer = ExperimentRecipePrefRolloutArgumentsSerializer(experiment)

        serializer_data = serializer.data

        self.assertEqual(serializer_data["slug"], "normandy-slug")

        self.assertDictEqual(
            dict(serializer_data["preferences"][0]),
            {"preferenceName": "browser.pref", "value": True},
        )

    def test_serializer_outputs_expected_schema_for_str(self):
        experiment = ExperimentFactory.create(
            type=Experiment.TYPE_ROLLOUT,
            recipe_slug="normandy-slug",
            rollout_type=Experiment.TYPE_PREF,
        )

        preference = RolloutPreference(
            pref_type=Experiment.PREF_TYPE_STR,
            pref_name="browser.pref",
            pref_value="a string",
            experiment=experiment,
        )

        preference.save()
        serializer = ExperimentRecipePrefRolloutArgumentsSerializer(experiment)
        serializer_data = serializer.data

        self.assertEqual(serializer_data["slug"], "normandy-slug")

        self.assertDictEqual(
            dict(serializer_data["preferences"][0]),
            {"preferenceName": "browser.pref", "value": "a string"},
        )

    def test_serializer_outputs_expected_schema_for_multi_pref(self):

        experiment = ExperimentFactory.create(
            type=Experiment.TYPE_ROLLOUT,
            recipe_slug="normandy-slug",
            rollout_type=Experiment.TYPE_PREF,
        )

        preference1 = RolloutPreference(
            pref_type=Experiment.PREF_TYPE_INT,
            pref_name="browser.pref",
            pref_value="4",
            experiment=experiment,
        )

        preference2 = RolloutPreference(
            pref_type=Experiment.PREF_TYPE_STR,
            pref_name="browser.pref1",
            pref_value="a string",
            experiment=experiment,
        )

        preference1.save()
        preference2.save()

        serializer = ExperimentRecipePrefRolloutArgumentsSerializer(experiment)

        serializer_data = serializer.data

        self.assertEqual(serializer_data["slug"], "normandy-slug")

        self.assertCountEqual(
            serializer_data["preferences"],
            [
                {"preferenceName": "browser.pref", "value": 4},
                {"preferenceName": "browser.pref1", "value": "a string"},
            ],
        )


class TestExperimentRecipeSerializer(TestCase):
    maxDiff = None

    def test_serializer_outputs_expected_schema_for_pref_experiment(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_SHIP,
            firefox_min_version="65.0",
            type=Experiment.TYPE_PREF,
            locales=[LocaleFactory.create()],
            countries=[CountryFactory.create()],
            platforms=[Experiment.PLATFORM_MAC],
            profile_age="Existing Profiles Only",
        )
        serializer = ExperimentRecipeSerializer(experiment)
        self.assertEqual(serializer.data["action_name"], "preference-experiment")
        self.assertEqual(serializer.data["name"], experiment.name)
        expected_comment = (
            f"{experiment.client_matching}\n"
            f"Platform: ['All Mac']\n"
            "Profile Age: Existing Profiles Only"
        )
        self.assertEqual(serializer.data["comment"], expected_comment)
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
        self.assertDictEqual(
            serializer.data["arguments"],
            ExperimentRecipePrefArgumentsSerializer(experiment).data,
        )

        self.assertEqual(serializer.data["experimenter_slug"], experiment.slug)

    def test_serializer_outputs_expected_schema_for_windows_versions(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_SHIP,
            firefox_min_version="65.0",
            type=Experiment.TYPE_PREF,
            locales=[LocaleFactory.create()],
            countries=[CountryFactory.create()],
            windows_versions=[Experiment.VERSION_WINDOWS_8],
        )

        serializer = ExperimentRecipeSerializer(experiment)

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

    def test_serializer_outputs_expected_schema_for_addon_experiment(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_SHIP,
            firefox_min_version="63.0",
            type=Experiment.TYPE_ADDON,
            locales=[LocaleFactory.create()],
            countries=[CountryFactory.create()],
            platforms=[Experiment.PLATFORM_WINDOWS],
            windows_versions=[Experiment.VERSION_WINDOWS_8],
        )
        serializer = ExperimentRecipeSerializer(experiment)
        self.assertEqual(serializer.data["action_name"], "opt-out-study")
        self.assertEqual(serializer.data["name"], experiment.name)

        expected_comment = (
            f"{experiment.client_matching}\n"
            f"Platform: ['All Windows']\n"
            f"Windows Versions: ['Windows 8']\n"
        )
        self.assertEqual(serializer.data["comment"], expected_comment)
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
        self.assertDictEqual(
            serializer.data["arguments"],
            ExperimentRecipeAddonArgumentsSerializer(experiment).data,
        )

        self.assertEqual(serializer.data["experimenter_slug"], experiment.slug)

    def test_serializer_outputs_expect_schema_for_branched_addon(self):
        experiment = ExperimentFactory.create(
            countries=[CountryFactory.create()],
            firefox_min_version="70.0",
            locales=[LocaleFactory.create()],
            name="public name",
            recipe_slug="some-random-slug",
            platforms=[Experiment.PLATFORM_LINUX],
            public_description="this is my public description!",
            type=Experiment.TYPE_ADDON,
        )

        variant = ExperimentVariant(slug="slug-value", ratio=25, experiment=experiment)

        variant.save()

        serializer = ExperimentRecipeSerializer(experiment)
        self.assertEqual(serializer.data["action_name"], "branched-addon-study")
        self.assertEqual(serializer.data["name"], experiment.name)

        expected_comment = f"{experiment.client_matching}\n" f"Platform: ['All Linux']\n"
        self.assertEqual(serializer.data["comment"], expected_comment)
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
        self.assertDictEqual(
            serializer.data["arguments"],
            {
                "branches": [{"ratio": 25, "slug": "slug-value", "extensionApiId": None}],
                "slug": "some-random-slug",
                "userFacingDescription": "this is my public description!",
                "userFacingName": "public name",
            },
        )

    def test_serializer_outputs_expected_multipref_schema_for_singularpref(self):
        experiment = ExperimentFactory.create(
            name="public name",
            pref_type=Experiment.PREF_TYPE_INT,
            pref_branch=Experiment.PREF_BRANCH_DEFAULT,
            firefox_min_version="70.0",
            locales=[LocaleFactory.create()],
            countries=[CountryFactory.create()],
            public_description="this is my public description!",
            recipe_slug="some-random-slug",
            platforms=[Experiment.PLATFORM_WINDOWS],
        )

        variant = ExperimentVariant(
            slug="slug-value", ratio=25, experiment=experiment, value=5
        )

        variant.save()

        expected_comment = expected_comment = (
            f"{experiment.client_matching}\n" f"Platform: ['All Windows']\n"
        )
        serializer = ExperimentRecipeSerializer(experiment)
        self.assertEqual(serializer.data["action_name"], "multi-preference-experiment")
        self.assertEqual(serializer.data["name"], experiment.name)
        self.assertEqual(serializer.data["comment"], expected_comment)
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
        expected_data = {
            "slug": "some-random-slug",
            "experimentDocumentUrl": experiment.experiment_url,
            "userFacingName": "public name",
            "userFacingDescription": "this is my public description!",
            "branches": [
                {
                    "preferences": {
                        experiment.pref_name: {
                            "preferenceBranchType": "default",
                            "preferenceType": Experiment.PREF_TYPE_INT,
                            "preferenceValue": 5,
                        }
                    },
                    "ratio": 25,
                    "slug": "slug-value",
                }
            ],
        }
        self.assertDictEqual(serializer.data["arguments"], expected_data)

    def test_serializer_outputs_expected_schema_for_multipref(self):
        experiment = ExperimentFactory.create(
            name="public name",
            firefox_min_version="70.0",
            locales=[LocaleFactory.create()],
            countries=[CountryFactory.create()],
            public_description="this is my public description!",
            recipe_slug="some-random-slug",
            platforms=[
                Experiment.PLATFORM_WINDOWS,
                Experiment.PLATFORM_MAC,
                Experiment.PLATFORM_LINUX,
            ],
            is_multi_pref=True,
        )

        variant = ExperimentVariant(
            slug="slug-value", ratio=25, experiment=experiment, is_control=True
        )

        variant.save()

        pref = VariantPreferencesFactory.create(variant=variant)

        expected_comment = expected_comment = f"{experiment.client_matching}\n"
        serializer = ExperimentRecipeSerializer(experiment)
        self.assertEqual(serializer.data["action_name"], "multi-preference-experiment")
        self.assertEqual(serializer.data["name"], experiment.name)
        self.assertEqual(serializer.data["comment"], expected_comment)
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

        expected_data = {
            "slug": "some-random-slug",
            "experimentDocumentUrl": experiment.experiment_url,
            "userFacingName": "public name",
            "userFacingDescription": "this is my public description!",
            "branches": [
                {
                    "preferences": {
                        pref.pref_name: {
                            "preferenceBranchType": pref.pref_branch,
                            "preferenceType": pref.pref_type,
                            "preferenceValue": pref.pref_value,
                        }
                    },
                    "ratio": 25,
                    "slug": "slug-value",
                }
            ],
        }
        self.assertDictEqual(serializer.data["arguments"], expected_data)

    def test_serializer_outputs_expected_schema_for_addon_rollout(self):
        experiment = ExperimentFactory.create(
            addon_release_url="https://www.example.com/addon.xpi",
            countries=[],
            firefox_channel=Experiment.CHANNEL_BETA,
            firefox_max_version="71",
            firefox_min_version="70",
            locales=[],
            name="Experimenter Name",
            recipe_slug="normandy-slug",
            platforms=[Experiment.PLATFORM_WINDOWS],
            population_percent=30.0,
            rollout_type=Experiment.TYPE_ADDON,
            slug="experimenter-slug",
            type=Experiment.TYPE_ROLLOUT,
        )
        serializer = ExperimentRecipeSerializer(experiment)
        self.assertDictEqual(
            serializer.data,
            {
                "action_name": "addon-rollout",
                "arguments": {
                    "extensionApiId": "TODO: https://www.example.com/addon.xpi",
                    "slug": "normandy-slug",
                },
                "comment": "Geos: US, CA, GB\n"
                'Some "additional" filtering\n'
                "Platform: ['All Windows']\n",
                "experimenter_slug": "experimenter-slug",
                "filter_object": [
                    {
                        "count": 3000,
                        "input": ["normandy.userId"],
                        "start": 0,
                        "total": 10000,
                        "type": "bucketSample",
                    },
                    {"channels": ["beta"], "type": "channel"},
                    {"type": "version", "versions": [70, 71]},
                ],
                "name": "Experimenter Name",
            },
        )

    def test_serializer_outputs_expected_schema_for_pref_rollout(self):
        experiment = ExperimentFactory.create(
            countries=[],
            firefox_channel=Experiment.CHANNEL_BETA,
            firefox_max_version="71",
            firefox_min_version="70",
            locales=[],
            name="Experimenter Name",
            recipe_slug="normandy-slug",
            platforms=[Experiment.PLATFORM_WINDOWS],
            population_percent=30.0,
            rollout_type=Experiment.TYPE_PREF,
            slug="experimenter-slug",
            type=Experiment.TYPE_ROLLOUT,
        )
        preference = RolloutPreference(
            pref_name="browser.pref",
            pref_value="true",
            pref_type=Experiment.PREF_TYPE_BOOL,
            experiment=experiment,
        )
        preference.save()
        serializer = ExperimentRecipeSerializer(experiment)

        self.assertDictEqual(
            serializer.data,
            {
                "action_name": "preference-rollout",
                "arguments": {
                    "preferences": [{"preferenceName": "browser.pref", "value": True}],
                    "slug": "normandy-slug",
                },
                "comment": "Geos: US, CA, GB\n"
                'Some "additional" filtering\n'
                "Platform: ['All Windows']\n",
                "experimenter_slug": "experimenter-slug",
                "filter_object": [
                    {
                        "count": 3000,
                        "input": ["normandy.userId"],
                        "start": 0,
                        "total": 10000,
                        "type": "bucketSample",
                    },
                    {"type": "channel", "channels": ["beta"]},
                    {"type": "version", "versions": [70, 71]},
                ],
                "name": "Experimenter Name",
            },
        )

    def test_serializer_outputs_expected_schema_for_message(self):
        experiment = ExperimentFactory.create(
            name="public name",
            type=Experiment.TYPE_MESSAGE,
            firefox_min_version="70.0",
            locales=[LocaleFactory.create()],
            countries=[CountryFactory.create()],
            public_description="this is my public description!",
            recipe_slug="some-random-slug",
            platforms=[Experiment.PLATFORM_WINDOWS],
        )

        variant = ExperimentVariant(
            slug="slug-value", ratio=25, experiment=experiment, is_control=True
        )

        variant.save()

        expected_comment = expected_comment = (
            f"{experiment.client_matching}\n" f"Platform: ['All Windows']\n"
        )
        serializer = ExperimentRecipeSerializer(experiment)
        self.assertEqual(serializer.data["action_name"], "messaging-experiment")
        self.assertEqual(serializer.data["name"], experiment.name)
        self.assertEqual(serializer.data["comment"], expected_comment)
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

        expected_data = {
            "slug": "some-random-slug",
            "experimentDocumentUrl": experiment.experiment_url,
            "userFacingName": "public name",
            "userFacingDescription": "this is my public description!",
            "branches": [{"groups": [], "value": {}, "ratio": 25, "slug": "slug-value"}],
        }

        self.assertDictEqual(serializer.data["arguments"], expected_data)

    def test_serializer_excludes_locales_if_none_set(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_SHIP, type=Experiment.TYPE_ADDON
        )
        experiment.locales.all().delete()
        serializer = ExperimentRecipeSerializer(experiment)
        filter_object_types = [f["type"] for f in serializer.data["filter_object"]]
        self.assertNotIn("locale", filter_object_types)

    def test_serializer_excludes_countries_if_none_set(self):
        experiment = ExperimentFactory.create_with_status(
            Experiment.STATUS_SHIP, type=Experiment.TYPE_ADDON
        )
        experiment.countries.all().delete()
        serializer = ExperimentRecipeSerializer(experiment)
        filter_object_types = [f["type"] for f in serializer.data["filter_object"]]
        self.assertNotIn("country", filter_object_types)


class TestExperimentRecipeMultiPrefVariantSerializer(TestCase):
    def test_serializer_outputs_expected_schema_non_multi_pref_format(self):
        experiment = ExperimentFactory.create(
            recipe_slug="normandy-slug",
            pref_branch=Experiment.PREF_BRANCH_DEFAULT,
            pref_type=Experiment.PREF_TYPE_JSON_STR,
            pref_name="browser.pref",
            firefox_min_version="55.0",
        )
        variant = ExperimentVariantFactory.create(
            slug="control", ratio=25, experiment=experiment, value='{"some": "json"}'
        )
        serializer = ExperimentRecipeMultiPrefVariantSerializer(variant)
        expected_data = {
            "preferences": {
                "browser.pref": {
                    "preferenceBranchType": "default",
                    "preferenceType": "string",
                    "preferenceValue": '{"some": "json"}',
                }
            },
            "ratio": 25,
            "slug": "control",
        }

        self.assertDictEqual(expected_data, serializer.data)

    def test_serializer_outputs_expected_schema_for_multi_pref_format(self):
        experiment = ExperimentFactory.create(
            recipe_slug="normandy-slug", firefox_min_version="55.0", is_multi_pref=True
        )
        variant = ExperimentVariantFactory.create(
            slug="control", ratio=25, experiment=experiment
        )

        preference = VariantPreferencesFactory.create(variant=variant)
        serializer = ExperimentRecipeMultiPrefVariantSerializer(variant)

        self.assertEqual(serializer.data["ratio"], 25)
        self.assertEqual(serializer.data["slug"], "control")

        serialized_preferences = serializer.data["preferences"]
        self.assertDictEqual(
            serialized_preferences[preference.pref_name],
            {
                "preferenceBranchType": preference.pref_branch,
                "preferenceType": preference.pref_type,
                "preferenceValue": preference.pref_value,
            },
        )

    def test_seriailzer_outputs_expected_schema_for_single_pref_experiment(self):
        experiment = ExperimentFactory.create(
            pref_type=Experiment.PREF_TYPE_JSON_STR, firefox_max_version="70.0"
        )
        variant = ExperimentVariantFactory.create(experiment=experiment)

        serializer = ExperimentRecipeMultiPrefVariantSerializer(variant)

        self.assertEqual(serializer.data["ratio"], variant.ratio)
        self.assertEqual(serializer.data["slug"], variant.slug)

        serialized_preferences = serializer.data["preferences"]
        self.assertDictEqual(
            serialized_preferences[experiment.pref_name],
            {
                "preferenceBranchType": experiment.pref_branch,
                "preferenceType": PrefTypeField().to_representation(experiment.pref_type),
                "preferenceValue": variant.value,
            },
        )

    def test_seriailzer_outputs_expected_schema_for_multi_pref_variant(self):
        experiment = ExperimentFactory.create(
            pref_type=Experiment.PREF_TYPE_JSON_STR, is_multi_pref=True
        )
        variant = ExperimentVariantFactory.create(experiment=experiment)
        preference = VariantPreferencesFactory.create(variant=variant)
        serializer = ExperimentRecipeMultiPrefVariantSerializer(variant)

        self.assertEqual(serializer.data["ratio"], variant.ratio)
        self.assertEqual(serializer.data["slug"], variant.slug)

        serialized_preferences = serializer.data["preferences"]
        self.assertDictEqual(
            serialized_preferences[preference.pref_name],
            {
                "preferenceBranchType": preference.pref_branch,
                "preferenceType": PrefTypeField().to_representation(preference.pref_type),
                "preferenceValue": preference.pref_value,
            },
        )
        self.assertEqual(serializer.data["ratio"], variant.ratio)
        self.assertEqual(serializer.data["slug"], variant.slug)


class TestExperimentRecipeVariantSerializer(TestCase):
    def test_serializer_outputs_expected_schema(self):
        experiment = ExperimentFactory(pref_type=Experiment.PREF_TYPE_STR)
        variant = ExperimentVariantFactory.create(experiment=experiment)
        serializer = ExperimentRecipeVariantSerializer(variant)
        self.assertDictEqual(
            serializer.data,
            {"ratio": variant.ratio, "slug": variant.slug, "value": variant.value},
        )


class TestExperimentRecipePrefArgumentsSerializer(TestCase):
    def test_serializer_outputs_expected_schema(self):
        experiment = ExperimentFactory(pref_type=Experiment.PREF_TYPE_INT)
        serializer = ExperimentRecipePrefArgumentsSerializer(experiment)
        self.assertDictEqual(
            serializer.data,
            {
                "preferenceBranchType": experiment.pref_branch,
                "slug": experiment.recipe_slug,
                "experimentDocumentUrl": experiment.experiment_url,
                "preferenceName": experiment.pref_name,
                "preferenceType": experiment.pref_type,
                "branches": [
                    ExperimentRecipeVariantSerializer(variant).data
                    for variant in experiment.variants.all()
                ],
            },
        )

    def test_serializer_outputs_expected_schema_with_json_str(self):
        experiment = ExperimentFactory(pref_type=Experiment.PREF_TYPE_JSON_STR)
        serializer = ExperimentRecipePrefArgumentsSerializer(experiment)
        self.assertDictEqual(
            serializer.data,
            {
                "preferenceBranchType": experiment.pref_branch,
                "slug": experiment.recipe_slug,
                "experimentDocumentUrl": experiment.experiment_url,
                "preferenceName": experiment.pref_name,
                "preferenceType": "string",
                "branches": [
                    ExperimentRecipeVariantSerializer(variant).data
                    for variant in experiment.variants.all()
                ],
            },
        )


class TestExperimentRecipeMessageVariantSerializer(TestCase):
    def test_serializer_outputs_expected_schema(self):
        experiment = ExperimentFactory()
        variant = ExperimentVariantFactory.create(experiment=experiment)
        serializer = ExperimentRecipeMessageVariantSerializer(variant)
        self.assertDictEqual(
            serializer.data,
            {"ratio": variant.ratio, "slug": variant.slug, "value": {}, "groups": []},
        )


class TestExperimentRecipeMessageArgumentsSerializer(TestCase):
    def test_serializer_outputs_expected_schema(self):
        experiment = ExperimentFactory()
        serializer = ExperimentRecipeMessageArgumentsSerializer(experiment)
        self.assertDictEqual(
            serializer.data,
            {
                "slug": experiment.recipe_slug,
                "experimentDocumentUrl": experiment.experiment_url,
                "userFacingName": experiment.name,
                "userFacingDescription": experiment.public_description,
                "branches": [
                    ExperimentRecipeMessageVariantSerializer(variant).data
                    for variant in experiment.variants.all()
                ],
            },
        )
