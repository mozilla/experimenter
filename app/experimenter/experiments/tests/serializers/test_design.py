from django.test import TestCase
from rest_framework import serializers

from experimenter.experiments.models import (
    Experiment,
    ExperimentVariant,
    ExperimentChangeLog,
    RolloutPreference,
)
from experimenter.experiments.tests.factories import (
    ExperimentFactory,
    ExperimentVariantFactory,
    VariantPreferencesFactory,
    UserFactory,
)

from experimenter.experiments.serializers.design import (
    ExperimentDesignVariantBaseSerializer,
    ExperimentDesignAddonSerializer,
    ExperimentDesignBaseSerializer,
    ExperimentDesignBranchMultiPrefSerializer,
    ExperimentDesignBranchVariantPreferencesSerializer,
    ExperimentDesignBranchedAddonSerializer,
    ExperimentDesignGenericSerializer,
    ExperimentDesignMultiPrefSerializer,
    ExperimentDesignPrefSerializer,
    ExperimentDesignPrefRolloutSerializer,
    ExperimentDesignAddonRolloutSerializer,
    PrefValidationMixin,
)

from experimenter.experiments.serializers.entities import ExperimentVariantSerializer
from experimenter.experiments.constants import ExperimentConstants
from experimenter.experiments.tests.mixins import MockRequestMixin


class TestExperimentDesignVariantBaseSerializer(TestCase):

    def test_serializer_rejects_too_long_names(self):
        data = {
            "name": "Terrific branch" * 100,
            "ratio": 50,
            "description": "Very terrific branch.",
            "is_control": True,
        }
        serializer = ExperimentDesignVariantBaseSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)

    def test_serializer_puts_control_branch_first_and_sorts_rest_by_id(self):
        ExperimentVariantFactory.create(is_control=True)
        sorted_treatment_ids = sorted(
            [ExperimentVariantFactory.create(is_control=False).id for i in range(3)]
        )
        serializer = ExperimentDesignVariantBaseSerializer(
            ExperimentVariant.objects.all().order_by("-id"), many=True
        )
        self.assertTrue(serializer.data[0]["is_control"])
        self.assertFalse(any([b["is_control"] for b in serializer.data[1:]]))
        self.assertEqual(sorted_treatment_ids, [b["id"] for b in serializer.data[1:]])


class TestExperimentDesignBranchVarianPreferenceSerializer(TestCase):

    def test_serializer_outputs_expected_schema(self):
        variant = ExperimentVariantFactory.create()
        vp = VariantPreferencesFactory.create(variant=variant)

        serializer = ExperimentDesignBranchVariantPreferencesSerializer(vp)
        self.assertEqual(
            serializer.data,
            {
                "id": vp.id,
                "pref_name": vp.pref_name,
                "pref_branch": vp.pref_branch,
                "pref_type": vp.pref_type,
                "pref_value": vp.pref_value,
            },
        )


class TestExperimentDesignMultiPrefSerializer(MockRequestMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.pref1 = {
            "pref_name": "pref name 1",
            "pref_value": "pref value 1",
            "pref_branch": "default",
            "pref_type": "string",
        }

        self.pref2 = {
            "pref_name": "pref name 2",
            "pref_value": "true",
            "pref_branch": "default",
            "pref_type": "boolean",
        }

        self.pref3 = {
            "pref_name": "pref name 3",
            "pref_value": '{"jsonField": "jsonValue"}',
            "pref_branch": "default",
            "pref_type": "json string",
        }

        self.pref4 = {
            "pref_name": "pref name 4",
            "pref_value": "88",
            "pref_branch": "default",
            "pref_type": "integer",
        }

        self.control_variant = {
            "description": "control description",
            "ratio": 50,
            "is_control": True,
            "name": "control name",
            "preferences": [self.pref1, self.pref2],
        }

        self.branch1 = {
            "description": "branch 1 description",
            "ratio": 50,
            "is_control": False,
            "name": " branch 1",
            "preferences": [self.pref1, self.pref2, self.pref3, self.pref4],
        }

        self.experiment = ExperimentFactory.create(type=ExperimentConstants.TYPE_PREF)

    def test_serializer_outputs_expected_schema(self):
        experiment = ExperimentFactory.create()
        variant = ExperimentVariantFactory.create(experiment=experiment, is_control=True)
        vp = VariantPreferencesFactory.create(variant=variant)

        serializer = ExperimentDesignMultiPrefSerializer(experiment)
        serializer.data["variants"][0]["preferences"][0].pop("id")
        self.assertEqual(
            dict(serializer.data["variants"][0]),
            {
                "id": variant.id,
                "description": variant.description,
                "is_control": variant.is_control,
                "name": variant.name,
                "ratio": variant.ratio,
                "preferences": [
                    {
                        "pref_name": vp.pref_name,
                        "pref_value": vp.pref_value,
                        "pref_branch": vp.pref_branch,
                        "pref_type": vp.pref_type,
                    }
                ],
            },
        )

    def test_serializer_saves_multipref_experiment_design(self):
        data = {"is_multi_pref": True, "variants": [self.control_variant, self.branch1]}

        serializer = ExperimentDesignMultiPrefSerializer(
            instance=self.experiment, data=data, context={"request": self.request}
        )

        self.assertTrue(serializer.is_valid())
        self.assertEqual(self.experiment.changes.count(), 0)

        experiment = serializer.save()
        self.assertTrue(experiment.variants.all().count(), 1)
        self.assertEqual(experiment.changes.count(), 1)

        control = ExperimentVariant.objects.get(experiment=experiment, is_control=True)
        branch1 = ExperimentVariant.objects.get(experiment=experiment, is_control=False)

        self.assertEqual(control.preferences.all().count(), 2)
        self.assertEqual(branch1.preferences.all().count(), 4)

    def test_serailizer_reject_duplicate_pref_name_in_branch(self):
        self.pref1["pref_name"] = self.pref2["pref_name"]
        data = {"variants": [self.control_variant]}

        serializer = ExperimentDesignMultiPrefSerializer(
            instance=self.experiment, data=data
        )
        self.assertFalse(serializer.is_valid())
        error_string = str(serializer.errors)
        self.assertIn("Pref name per Branch needs to be unique", error_string)

    def test_serailizer_reject_mismatch_type_value_integer(self):
        self.pref1["pref_type"] = Experiment.PREF_TYPE_INT
        self.pref1["pref_value"] = "some random string"
        data = {"variants": [self.control_variant]}

        serializer = ExperimentDesignMultiPrefSerializer(
            instance=self.experiment, data=data
        )
        self.assertFalse(serializer.is_valid())
        error_string = str(serializer.errors)
        self.assertIn("The pref value must be an integer", error_string)

    def test_serailizer_reject_mismatch_type_value_bool(self):
        self.pref1["pref_type"] = Experiment.PREF_TYPE_BOOL
        self.pref1["pref_value"] = "some random string"
        data = {"variants": [self.control_variant]}

        serializer = ExperimentDesignMultiPrefSerializer(
            instance=self.experiment, data=data
        )
        self.assertFalse(serializer.is_valid())
        error_string = str(serializer.errors)
        self.assertIn("The pref value must be a boolean", error_string)

    def test_serailizer_reject_mismatch_type_value_json_string(self):
        self.pref1["pref_type"] = Experiment.PREF_TYPE_JSON_STR
        self.pref1["pref_value"] = "some random string"
        data = {"variants": [self.control_variant]}

        serializer = ExperimentDesignMultiPrefSerializer(
            instance=self.experiment, data=data
        )
        self.assertFalse(serializer.is_valid())
        error_string = str(serializer.errors)
        self.assertIn("The pref value must be valid JSON", error_string)

    def test_serializer_rejects_missing_preference_fields(self):
        self.pref1.pop("pref_name")

        data = {"variants": [self.control_variant]}

        serializer = ExperimentDesignMultiPrefSerializer(
            instance=self.experiment, data=data
        )

        self.assertFalse(serializer.is_valid())

        error_string = str(serializer.errors)

        self.assertIn("This field is required", error_string)

    def test_serializer_removes_preferences(self):
        variant = ExperimentVariantFactory.create(experiment=self.experiment)
        variant_pref = VariantPreferencesFactory.create(variant=variant)
        self.control_variant["id"] = variant.id
        self.control_variant["ratio"] = 100

        self.assertEqual(variant.preferences.all().count(), 1)
        self.assertTrue(variant.preferences.get(id=variant_pref.id))

        data = {"is_multi_pref": False, "variants": [self.control_variant]}
        serializer = ExperimentDesignMultiPrefSerializer(
            instance=self.experiment, data=data, context={"request": self.request}
        )
        self.assertTrue(serializer.is_valid())

        serializer.save()

        variant = ExperimentVariant.objects.get(id=variant.id)

        self.assertEqual(variant.preferences.all().count(), 2)

        self.assertEqual(variant.preferences.filter(id=variant_pref.id).count(), 0)

    def test_serializer_updates_existing_variant_pref(self):

        variant = ExperimentVariantFactory.create(experiment=self.experiment)
        variant_pref = VariantPreferencesFactory.create(variant=variant)
        self.pref1["id"] = variant_pref.id
        self.control_variant["id"] = variant.id
        self.control_variant["ratio"] = 100

        self.assertEqual(variant.preferences.all().count(), 1)
        self.assertTrue(variant.preferences.get(id=variant_pref.id))

        data = {"is_multi_pref": True, "variants": [self.control_variant]}
        serializer = ExperimentDesignMultiPrefSerializer(
            instance=self.experiment, data=data, context={"request": self.request}
        )
        self.assertTrue(serializer.is_valid())

        experiment = serializer.save()

        variant = ExperimentVariant.objects.get(id=variant.id)

        self.assertEqual(variant.preferences.all().count(), 2)

        self.assertEqual(variant.preferences.filter(id=variant_pref.id).count(), 1)

        self.assertEqual(experiment.changes.count(), 1)

    def test_serializer_outputs_dummy_variants_when_no_variants(self):
        experiment = ExperimentFactory.create(
            type=ExperimentConstants.TYPE_PREF, is_multi_pref=True
        )

        serializer = ExperimentDesignMultiPrefSerializer(experiment)

        self.assertEqual(
            serializer.data,
            {
                "is_multi_pref": True,
                "variants": [
                    {
                        "description": None,
                        "is_control": True,
                        "name": None,
                        "ratio": 50,
                        "preferences": [{}],
                    },
                    {
                        "description": None,
                        "is_control": False,
                        "name": None,
                        "ratio": 50,
                        "preferences": [{}],
                    },
                ],
            },
        )


class TestExperimentDesignBranchMultiPrefSerializer(TestCase):

    def setUp(self):
        self.pref1 = {
            "pref_name": "pref1",
            "pref_value": "pref 1 value",
            "pref_branch": "default",
            "pref_type": "string",
        }
        self.pref2 = {
            "pref_name": "pref2",
            "pref_value": "pref 2 value",
            "pref_branch": "default",
            "pref_type": "string",
        }
        self.variant = {
            "ratio": 100,
            "is_control": True,
            "name": "control",
            "description": "control description",
            "preferences": [self.pref1, self.pref2],
        }

    def test_serializer_outputs_expected_schema(self):
        variant = ExperimentVariantFactory.create()
        vp = VariantPreferencesFactory.create(variant=variant)
        serializer = ExperimentDesignBranchMultiPrefSerializer(variant)

        self.assertEqual(
            serializer.data,
            {
                "id": variant.id,
                "description": variant.description,
                "ratio": variant.ratio,
                "is_control": False,
                "name": variant.name,
                "preferences": [
                    {
                        "id": vp.id,
                        "pref_name": vp.pref_name,
                        "pref_value": vp.pref_value,
                        "pref_branch": vp.pref_branch,
                        "pref_type": vp.pref_type,
                    }
                ],
            },
        )


class TestExperimentDesignBaseSerializer(MockRequestMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.control_variant_data = {
            "name": "Terrific branch",
            "ratio": 50,
            "description": "Very terrific branch.",
            "is_control": True,
        }
        self.treatment_variant_data = {
            "name": "Great branch",
            "ratio": 50,
            "description": "Very great branch.",
            "is_control": False,
        }

    def test_serializer_saves_new_variants(self):
        experiment = ExperimentFactory.create(type=ExperimentConstants.TYPE_GENERIC)

        self.assertEqual(experiment.variants.all().count(), 0)

        data = {"variants": [self.control_variant_data, self.treatment_variant_data]}

        serializer = ExperimentDesignBaseSerializer(
            instance=experiment, data=data, context={"request": self.request}
        )

        self.assertTrue(serializer.is_valid())

        experiment = serializer.save()

        self.assertEqual(experiment.variants.all().count(), 2)

        control_variant = experiment.variants.get(is_control=True)
        self.assertEqual(control_variant.name, self.control_variant_data["name"])
        self.assertEqual(control_variant.ratio, self.control_variant_data["ratio"])
        self.assertEqual(
            control_variant.description, self.control_variant_data["description"]
        )

        treatment_variant = experiment.variants.get(is_control=False)
        self.assertEqual(treatment_variant.name, self.treatment_variant_data["name"])
        self.assertEqual(treatment_variant.ratio, self.treatment_variant_data["ratio"])
        self.assertEqual(
            treatment_variant.description, self.treatment_variant_data["description"]
        )

    def test_serializer_updates_existing_variants(self):
        experiment = ExperimentFactory.create(type=ExperimentConstants.TYPE_GENERIC)
        control_variant = ExperimentVariantFactory.create(
            experiment=experiment, is_control=True
        )
        treatment_variant = ExperimentVariantFactory.create(
            experiment=experiment, is_control=False
        )

        self.assertEqual(experiment.variants.all().count(), 2)

        self.control_variant_data["id"] = control_variant.id
        self.treatment_variant_data["id"] = treatment_variant.id

        data = {"variants": [self.control_variant_data, self.treatment_variant_data]}

        serializer = ExperimentDesignBaseSerializer(
            instance=experiment, data=data, context={"request": self.request}
        )

        self.assertTrue(serializer.is_valid())

        experiment = serializer.save()

        self.assertEqual(experiment.variants.all().count(), 2)

        control_variant = ExperimentVariant.objects.get(id=control_variant.id)
        self.assertEqual(control_variant.name, self.control_variant_data["name"])
        self.assertEqual(control_variant.ratio, self.control_variant_data["ratio"])
        self.assertEqual(
            control_variant.description, self.control_variant_data["description"]
        )

        treatment_variant = ExperimentVariant.objects.get(id=treatment_variant.id)
        self.assertEqual(treatment_variant.name, self.treatment_variant_data["name"])
        self.assertEqual(treatment_variant.ratio, self.treatment_variant_data["ratio"])
        self.assertEqual(
            treatment_variant.description, self.treatment_variant_data["description"]
        )

    def test_serializer_deletes_removed_variants(self):
        experiment = ExperimentFactory.create(type=ExperimentConstants.TYPE_GENERIC)
        control_variant = ExperimentVariantFactory.create(
            experiment=experiment, is_control=True
        )
        ExperimentVariantFactory.create(experiment=experiment, is_control=False)
        treatment2_variant = ExperimentVariantFactory.create(
            experiment=experiment, is_control=False
        )

        self.assertEqual(experiment.variants.all().count(), 3)

        self.control_variant_data["id"] = control_variant.id
        self.treatment_variant_data["id"] = treatment2_variant.id

        data = {"variants": [self.control_variant_data, self.treatment_variant_data]}

        serializer = ExperimentDesignBaseSerializer(
            instance=experiment, data=data, context={"request": self.request}
        )

        self.assertTrue(serializer.is_valid())

        experiment = serializer.save()

        self.assertEqual(experiment.variants.all().count(), 2)
        self.assertEqual(
            set(experiment.variants.all()), set([control_variant, treatment2_variant])
        )

    def test_serializer_adds_new_variant(self):
        experiment = ExperimentFactory.create(type=ExperimentConstants.TYPE_GENERIC)
        control_variant = ExperimentVariantFactory.create(
            experiment=experiment, is_control=True
        )
        treatment1_variant = ExperimentVariantFactory.create(
            experiment=experiment, is_control=False
        )

        self.assertEqual(experiment.variants.all().count(), 2)

        self.control_variant_data["id"] = control_variant.id
        self.control_variant_data["ratio"] = 33
        self.treatment_variant_data["id"] = treatment1_variant.id
        self.treatment_variant_data["ratio"] = 33

        treatment2_variant_data = {
            "name": "New Branch",
            "ratio": 34,
            "description": "New Branch",
            "is_control": False,
        }

        data = {
            "variants": [
                self.control_variant_data,
                self.treatment_variant_data,
                treatment2_variant_data,
            ]
        }

        serializer = ExperimentDesignBaseSerializer(
            instance=experiment, data=data, context={"request": self.request}
        )

        self.assertTrue(serializer.is_valid())

        experiment = serializer.save()

        self.assertEqual(experiment.variants.all().count(), 3)

        new_variant = ExperimentVariant.objects.get(name=treatment2_variant_data["name"])
        self.assertEqual(
            set(experiment.variants.all()),
            set([control_variant, treatment1_variant, new_variant]),
        )

    def test_serializer_rejects_ratio_not_100(self):
        experiment = ExperimentFactory.create(type=ExperimentConstants.TYPE_GENERIC)

        self.control_variant_data["ratio"] = 50
        self.treatment_variant_data["ratio"] = 40

        data = {"variants": [self.control_variant_data, self.treatment_variant_data]}

        serializer = ExperimentDesignBaseSerializer(instance=experiment, data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("variants", serializer.errors)

    def test_serializer_rejects_ratios_of_0(self):
        experiment = ExperimentFactory.create(type=ExperimentConstants.TYPE_GENERIC)

        self.control_variant_data["ratio"] = 0

        data = {"variants": [self.control_variant_data]}

        serializer = ExperimentDesignBaseSerializer(instance=experiment, data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("variants", serializer.errors)

    def test_serializer_rejects_ratios_above_100(self):
        experiment = ExperimentFactory.create(type=ExperimentConstants.TYPE_GENERIC)

        self.control_variant_data["ratio"] = 110

        data = {"variants": [self.control_variant_data]}

        serializer = ExperimentDesignBaseSerializer(instance=experiment, data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("variants", serializer.errors)

    def test_serializer_rejects_duplicate_branch_names(self):
        experiment = ExperimentFactory.create(type=ExperimentConstants.TYPE_GENERIC)

        self.control_variant_data["name"] = "Great branch"

        data = {"variants": [self.control_variant_data, self.treatment_variant_data]}

        serializer = ExperimentDesignBaseSerializer(instance=experiment, data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("variants", serializer.errors)

    def test_serializer_allows_special_char_branch_names(self):
        experiment = ExperimentFactory.create(type=ExperimentConstants.TYPE_PREF)

        self.control_variant_data["name"] = "&re@t -br@nche$!"

        data = {"variants": [self.control_variant_data, self.treatment_variant_data]}

        serializer = ExperimentDesignBaseSerializer(
            instance=experiment, data=data, context={"request": self.request}
        )

        self.assertTrue(serializer.is_valid())
        serializer.save()

        variant = ExperimentVariant.objects.get(name="&re@t -br@nche$!")
        self.assertEqual(variant.slug, "ret-brnche")

    def test_serializer_swapping_variant_name_throws_returns_errors(self):
        experiment = ExperimentFactory.create()
        variant1 = ExperimentVariantFactory.create(experiment=experiment)
        variant2 = ExperimentVariantFactory.create(experiment=experiment)

        v1_data = ExperimentVariantSerializer(variant1).data
        v2_data = ExperimentVariantSerializer(variant2).data

        # swap names
        v1_data["name"], v2_data["name"] = v2_data["name"], v1_data["name"]
        v1_data["ratio"] = 50
        v2_data["ratio"] = 50

        data = {"variants": [v1_data, v2_data]}

        serializer = ExperimentDesignBaseSerializer(
            instance=experiment, data=data, context={"request": self.request}
        )
        self.assertTrue(serializer.is_valid())

        self.assertEqual(experiment.changes.count(), 0)

        with self.assertRaises(serializers.ValidationError):
            serializer.save()

            self.assertIn(
                "Experimenter Error Occured: duplicate key value", serializer.errors
            )

            # no changes occured
            self.assertEqual(experiment.changes.count(), 0)
            variant1 = ExperimentVariant.get(id=variant1.id)
            variant2 = ExperimentVariant.get(id=variant2.id)

            self.assertEqual(variant1.name, v2_data["name"])
            self.assertEqual(variant2.name, v1_data["name"])


class TestExperimentDesignPrefSerializer(MockRequestMixin, TestCase):

    def setUp(self):
        super().setUp()

        self.variant_1 = {
            "name": "Terrific branch",
            "ratio": 50,
            "value": "true",
            "description": "Very terrific branch.",
            "is_control": True,
        }
        self.variant_2 = {
            "name": "Great branch",
            "ratio": 50,
            "value": "false",
            "description": "Very great branch.",
            "is_control": False,
        }

    def test_serializer_outputs_expected_schema(self):
        experiment = ExperimentFactory.create_with_variants(
            type=ExperimentConstants.TYPE_PREF
        )

        serializer = ExperimentDesignPrefSerializer(experiment)
        serializer_data = serializer.data
        variant_data = serializer_data.pop("variants")
        variant_data = [dict(variant) for variant in variant_data]
        expected_variant_data = [
            {
                "id": variant.id,
                "description": variant.description,
                "is_control": variant.is_control,
                "name": variant.name,
                "value": variant.value,
                "ratio": variant.ratio,
            }
            for variant in experiment.variants.all()
        ]
        self.assertEqual(
            serializer_data,
            {
                "is_multi_pref": False,
                "pref_name": experiment.pref_name,
                "pref_type": experiment.pref_type,
                "pref_branch": experiment.pref_branch,
            },
        )
        self.assertCountEqual(expected_variant_data, variant_data)

    def test_serializer_saves_pref_experiment_design(self):
        experiment = ExperimentFactory.create(
            type=ExperimentConstants.TYPE_PREF, pref_name="first pref name"
        )

        data = {
            "is_multi_pref": False,
            "pref_type": "boolean",
            "pref_name": "second name",
            "pref_branch": "default",
            "variants": [self.variant_1, self.variant_2],
        }

        serializer = ExperimentDesignPrefSerializer(
            instance=experiment, data=data, context={"request": self.request}
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(experiment.changes.count(), 0)

        experiment = serializer.save()

        self.assertEqual(experiment.pref_name, "second name")
        self.assertEqual(experiment.changes.count(), 1)

    def test_serializer_rejects_duplicate_branch_values(self):
        experiment = ExperimentFactory.create(type=ExperimentConstants.TYPE_PREF)

        self.variant_1["value"] = "value 1"
        self.variant_2["value"] = "value 1"

        data = {
            "is_multi_pref": False,
            "pref_type": "string",
            "pref_name": "name",
            "pref_branch": "default",
            "variants": [self.variant_1, self.variant_2],
        }
        serializer = ExperimentDesignPrefSerializer(instance=experiment, data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("variants", serializer.errors)
        experiment = Experiment.objects.get(id=experiment.id)
        self.assertEqual(experiment.changes.count(), 0)

    def test_serializer_rejects_no_type_choice(self):
        experiment = ExperimentFactory.create(type=ExperimentConstants.TYPE_PREF)

        data = {
            "is_multi_pref": False,
            "pref_type": "Firefox Pref Type",
            "pref_name": "name",
            "pref_branch": "default",
            "variants": [self.variant_1, self.variant_2],
        }
        serializer = ExperimentDesignPrefSerializer(instance=experiment, data=data)

        self.assertFalse(serializer.is_valid())
        self.assertEqual(set(serializer.errors), set(["pref_type"]))
        experiment = Experiment.objects.get(id=experiment.id)
        self.assertEqual(experiment.changes.count(), 0)

    def test_serializer_rejects_no_branch_choice(self):
        experiment = ExperimentFactory.create(type=ExperimentConstants.TYPE_PREF)

        data = {
            "is_multi_pref": False,
            "pref_type": "boolean",
            "pref_name": "name",
            "pref_branch": "Firefox Pref Branch",
            "variants": [self.variant_1, self.variant_2],
        }
        serializer = ExperimentDesignPrefSerializer(instance=experiment, data=data)

        self.assertFalse(serializer.is_valid())
        self.assertEqual(set(serializer.errors), set(["pref_branch"]))

    def test_serializer_rejects_inconsistent_pref_type_bool(self):
        experiment = ExperimentFactory.create(type=ExperimentConstants.TYPE_PREF)

        self.variant_1["value"] = "value 1"

        data = {
            "is_multi_pref": False,
            "pref_type": "boolean",
            "pref_name": "name",
            "pref_branch": "default",
            "variants": [self.variant_1, self.variant_2],
        }
        serializer = ExperimentDesignPrefSerializer(instance=experiment, data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("variants", serializer.errors)
        experiment = Experiment.objects.get(id=experiment.id)
        self.assertEqual(experiment.changes.count(), 0)

    def test_serializer_accepts_int_branch_values(self):
        experiment = ExperimentFactory.create(type=ExperimentConstants.TYPE_PREF)

        self.variant_1["value"] = 50
        self.variant_2["value"] = 40

        data = {
            "is_multi_pref": False,
            "pref_type": "integer",
            "pref_name": "name",
            "pref_branch": "default",
            "variants": [self.variant_1, self.variant_2],
        }
        serializer = ExperimentDesignPrefSerializer(instance=experiment, data=data)

        self.assertTrue(serializer.is_valid())

    def test_serializer_rejects_inconsistent_pref_type_int(self):
        experiment = ExperimentFactory.create(type=ExperimentConstants.TYPE_PREF)
        self.variant_1["value"] = "value 1"
        self.variant_2["value"] = "value 2"

        data = {
            "is_multi_pref": False,
            "pref_type": "integer",
            "pref_name": "name",
            "pref_branch": "default",
            "variants": [self.variant_1, self.variant_2],
        }
        serializer = ExperimentDesignPrefSerializer(instance=experiment, data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("variants", serializer.errors)

    def test_serializer_accepts_pref_type_json_value(self):
        experiment = ExperimentFactory.create(type=ExperimentConstants.TYPE_PREF)

        self.variant_1["value"] = "{}"
        self.variant_2["value"] = '{"variant":[1,2,3,4]}'

        data = {
            "is_multi_pref": False,
            "pref_type": "json string",
            "pref_branch": "default",
            "pref_name": "name",
            "variants": [self.variant_1, self.variant_2],
        }
        serializer = ExperimentDesignPrefSerializer(instance=experiment, data=data)

        self.assertTrue(serializer.is_valid())

    def test_serializer_rejects_inconsistent_pref_type_json(self):
        experiment = ExperimentFactory.create(type=ExperimentConstants.TYPE_PREF)

        self.variant_1["value"] = "value_1"
        self.variant_2["value"] = "value 2"

        data = {
            "is_multi_pref": False,
            "pref_type": "json string",
            "pref_name": "name",
            "pref_branch": "default",
            "variants": [self.variant_1, self.variant_2],
        }
        serializer = ExperimentDesignPrefSerializer(instance=experiment, data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("variants", serializer.errors)

    def test_serializer_rejects_too_long_pref_type(self):
        data = {
            "pref_type": "json string" * 100,
            "pref_name": "name",
            "pref_branch": "default",
            "variants": [self.variant_1, self.variant_2],
        }
        serializer = ExperimentDesignPrefSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("pref_type", serializer.errors)

    def test_serializer_rejects_too_long_pref_name(self):
        data = {
            "pref_type": "json string",
            "pref_name": "name" * 100,
            "pref_branch": "default",
            "variants": [self.variant_1, self.variant_2],
        }
        serializer = ExperimentDesignPrefSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("pref_name", serializer.errors)

    def test_serializer_rejects_too_long_pref_branch(self):
        data = {
            "pref_type": "json string",
            "pref_name": "name",
            "pref_branch": "default" * 100,
            "variants": [self.variant_1, self.variant_2],
        }
        serializer = ExperimentDesignPrefSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("pref_branch", serializer.errors)

    def test_serializer_outputs_dummy_variants_when_no_variants(self):
        experiment = ExperimentFactory.create(type=ExperimentConstants.TYPE_PREF)

        serializer = ExperimentDesignPrefSerializer(experiment)

        self.assertEqual(
            serializer.data,
            {
                "is_multi_pref": False,
                "pref_name": experiment.pref_name,
                "pref_type": experiment.pref_type,
                "pref_branch": experiment.pref_branch,
                "variants": [
                    {
                        "description": None,
                        "is_control": True,
                        "name": None,
                        "ratio": 50,
                        "value": None,
                    },
                    {
                        "description": None,
                        "is_control": False,
                        "name": None,
                        "ratio": 50,
                        "value": None,
                    },
                ],
            },
        )


class TestExperimentDesignAddonSerializer(MockRequestMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.control_variant_data = {
            "name": "Terrific branch",
            "ratio": 50,
            "description": "Very terrific branch.",
            "is_control": True,
        }
        self.treatment_variant_data = {
            "name": "Great branch",
            "ratio": 50,
            "description": "Very great branch.",
            "is_control": False,
        }

    def test_serializer_outputs_expected_schema(self):
        experiment = ExperimentFactory.create_with_variants(
            type=ExperimentConstants.TYPE_ADDON
        )

        serializer = ExperimentDesignAddonSerializer(experiment)
        serializer_data = serializer.data
        variant_data = serializer_data.pop("variants")
        variant_data = [dict(variant) for variant in variant_data]
        expected_variant_data = [
            {
                "id": variant.id,
                "description": variant.description,
                "is_control": variant.is_control,
                "name": variant.name,
                "ratio": variant.ratio,
            }
            for variant in experiment.variants.all()
        ]
        self.assertEqual(
            serializer_data,
            {
                "addon_release_url": experiment.addon_release_url,
                "is_branched_addon": False,
            },
        )
        self.assertCountEqual(variant_data, expected_variant_data)

    def test_serializer_saves_design_addon_experiment(self):
        experiment = ExperimentFactory.create(
            type=ExperimentConstants.TYPE_ADDON,
            addon_release_url="http://www.example.com",
        )

        data = {
            "addon_release_url": "http://www.example.com",
            "is_branched_addon": False,
            "variants": [self.control_variant_data, self.treatment_variant_data],
        }

        serializer = ExperimentDesignAddonSerializer(
            instance=experiment, data=data, context={"request": self.request}
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(experiment.changes.count(), 0)
        experiment = serializer.save()

        self.assertEqual(experiment.changes.count(), 1)

    def test_serializer_rejects_too_long_urls(self):
        data = {
            "addon_release_url": "http://www.example.com" * 100,
            "is_branched_addon": False,
            "variants": [self.control_variant_data, self.treatment_variant_data],
        }

        serializer = ExperimentDesignAddonSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("addon_release_url", serializer.errors)

    def test_serializer_outputs_dummy_variants_when_no_variants(self):
        experiment = ExperimentFactory.create(type=ExperimentConstants.TYPE_ADDON)

        serializer = ExperimentDesignAddonSerializer(experiment)

        self.assertEqual(
            serializer.data,
            {
                "addon_release_url": experiment.addon_release_url,
                "is_branched_addon": False,
                "variants": [
                    {"description": None, "is_control": True, "name": None, "ratio": 50},
                    {"description": None, "is_control": False, "name": None, "ratio": 50},
                ],
            },
        )


class TestExperimentDesignGenericSerializer(MockRequestMixin, TestCase):

    def test_serializer_outputs_expected_schema(self):
        experiment = ExperimentFactory.create_with_variants(
            type=ExperimentConstants.TYPE_GENERIC
        )

        serializer = ExperimentDesignGenericSerializer(experiment)
        serializer_data = serializer.data
        variant_data = serializer_data.pop("variants")
        variant_data = [dict(variant) for variant in variant_data]
        expected_variant_data = [
            {
                "id": variant.id,
                "description": variant.description,
                "is_control": variant.is_control,
                "name": variant.name,
                "ratio": variant.ratio,
            }
            for variant in experiment.variants.all()
        ]

        self.assertEqual(serializer_data, {"design": experiment.design})
        self.assertCountEqual(variant_data, expected_variant_data)

    def test_serializer_saves_design_generic_experiment(self):
        experiment = ExperimentFactory.create(
            type=ExperimentConstants.TYPE_GENERIC, design="First Design"
        )
        variant_1 = {
            "name": "Terrific branch",
            "ratio": 50,
            "description": "Very terrific branch.",
            "is_control": True,
        }
        variant_2 = {
            "name": "Great branch",
            "ratio": 50,
            "description": "Very great branch.",
            "is_control": False,
        }

        data = {"design": "Second Design", "variants": [variant_1, variant_2]}

        serializer = ExperimentDesignGenericSerializer(
            instance=experiment, data=data, context={"request": self.request}
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(experiment.changes.count(), 0)

        experiment = serializer.save()

        self.assertEqual(experiment.design, "Second Design")
        self.assertEqual(experiment.changes.count(), 1)

    def test_serializer_outputs_dummy_variants_when_no_variants(self):
        experiment = ExperimentFactory.create(type=ExperimentConstants.TYPE_GENERIC)

        serializer = ExperimentDesignGenericSerializer(experiment)

        self.assertEqual(
            serializer.data,
            {
                "design": experiment.design,
                "variants": [
                    {"description": None, "is_control": True, "name": None, "ratio": 50},
                    {"description": None, "is_control": False, "name": None, "ratio": 50},
                ],
            },
        )


class TestExperimentDesignBranchedAddonSerializer(MockRequestMixin, TestCase):

    def test_serializer_outputs_expected_schema(self):
        experiment = ExperimentFactory.create_with_variants(
            type=ExperimentConstants.TYPE_ADDON
        )
        experiment.is_branched_addon = True
        experiment.save()

        serializer = ExperimentDesignBranchedAddonSerializer(experiment)
        serializer_data = serializer.data
        variant_data = serializer_data.pop("variants")
        variant_data = [dict(variant) for variant in variant_data]
        expected_variant_data = [
            {
                "id": variant.id,
                "description": variant.description,
                "is_control": variant.is_control,
                "name": variant.name,
                "ratio": variant.ratio,
                "addon_release_url": variant.addon_release_url,
            }
            for variant in experiment.variants.all()
        ]

        self.assertEqual(serializer_data, {"is_branched_addon": True})
        self.assertCountEqual(variant_data, expected_variant_data)

    def test_serializer_saves_branched_addon_experiment(self):
        experiment = ExperimentFactory.create_with_variants(
            type=ExperimentConstants.TYPE_ADDON, is_branched_addon=False
        )
        variant_1 = {
            "addon_release_url": "http://example.com",
            "name": "Terrific branch",
            "ratio": 50,
            "description": "Very terrific branch.",
            "is_control": True,
        }
        variant_2 = {
            "addon_release_url": "http://example2.com",
            "name": "Great branch",
            "ratio": 50,
            "description": "Very great branch.",
            "is_control": False,
        }

        data = {"is_branched_addon": True, "variants": [variant_1, variant_2]}

        serializer = ExperimentDesignBranchedAddonSerializer(
            instance=experiment, data=data, context={"request": self.request}
        )

        self.assertTrue(serializer.is_valid())
        self.assertEqual(experiment.changes.count(), 0)

        experiment = serializer.save()

        self.assertTrue(experiment.is_branched_addon)
        self.assertEqual(experiment.changes.count(), 1)


class TestExperimentDesignPrefRolloutSerializer(MockRequestMixin, TestCase):

    def test_pref_fields_required_for_rollout_type_pref(self):

        experiment = ExperimentFactory.create(type=Experiment.TYPE_ROLLOUT)

        data = {"rollout_type": Experiment.TYPE_PREF}

        serializer = ExperimentDesignPrefRolloutSerializer(
            instance=experiment, data=data, context={"request": self.request}
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("preferences", serializer.errors)

    def test_validates_pref_type_matches_value(self):
        experiment = ExperimentFactory.create(type=Experiment.TYPE_ROLLOUT)

        data = {
            "rollout_type": Experiment.TYPE_PREF,
            "preferences": [
                {
                    "pref_name": "browser.pref",
                    "pref_type": Experiment.PREF_TYPE_INT,
                    "pref_value": "abc",
                }
            ],
        }

        serializer = ExperimentDesignPrefRolloutSerializer(
            instance=experiment, data=data, context={"request": self.request}
        )
        self.assertFalse(serializer.is_valid())

    def test_saves_pref_rollout(self):
        experiment = ExperimentFactory.create(type=Experiment.TYPE_ROLLOUT)

        data = {
            "rollout_type": Experiment.TYPE_PREF,
            "preferences": [
                {
                    "pref_name": "browser.pref",
                    "pref_type": Experiment.PREF_TYPE_INT,
                    "pref_value": "1",
                },
                {
                    "pref_name": "browser.pref2",
                    "pref_type": Experiment.PREF_TYPE_STR,
                    "pref_value": "A STRING!",
                },
            ],
        }

        serializer = ExperimentDesignPrefRolloutSerializer(
            instance=experiment, data=data, context={"request": self.request}
        )

        self.assertTrue(serializer.is_valid())

        experiment = serializer.save()

        self.assertEqual(experiment.rollout_type, data["rollout_type"])

        self.assertEqual(experiment.preferences.count(), 2)
        data_pref1 = data["preferences"][0]
        pref1 = experiment.preferences.first()
        data_pref2 = data["preferences"][1]
        pref2 = experiment.preferences.last()
        self.assertEqual(pref1.pref_name, data_pref1["pref_name"])
        self.assertEqual(pref1.pref_type, data_pref1["pref_type"])
        self.assertEqual(pref1.pref_value, data_pref1["pref_value"])

        self.assertEqual(pref2.pref_name, data_pref2["pref_name"])
        self.assertEqual(pref2.pref_type, data_pref2["pref_type"])
        self.assertEqual(pref2.pref_value, data_pref2["pref_value"])

    def test_pref_name_uniqueness_constraint(self):
        experiment = ExperimentFactory.create(type=Experiment.TYPE_ROLLOUT)

        data = {
            "rollout_type": Experiment.TYPE_PREF,
            "preferences": [
                {
                    "pref_name": "browser.pref",
                    "pref_type": Experiment.PREF_TYPE_INT,
                    "pref_value": "1",
                },
                {
                    "pref_name": "browser.pref",
                    "pref_type": Experiment.PREF_TYPE_STR,
                    "pref_value": "A STRING!",
                },
            ],
        }

        serializer = ExperimentDesignPrefRolloutSerializer(
            instance=experiment, data=data, context={"request": self.request}
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn(
            "Pref name needs to be unique",
            serializer.errors["preferences"][0]["pref_name"],
        )

    def test_save_pref_rollout_with_existing_prefs(self):
        experiment = ExperimentFactory.create(type=Experiment.TYPE_ROLLOUT)
        preference1 = RolloutPreference(
            pref_type=Experiment.PREF_TYPE_INT,
            pref_name="browser.pref",
            pref_value="4",
            experiment=experiment,
        )
        preference1.save()
        original_pref1_id = experiment.preferences.first().id

        RolloutPreference(
            pref_type=Experiment.PREF_TYPE_INT,
            pref_name="browser.pref2",
            pref_value="4",
            experiment=experiment,
        ).save()

        data = {
            "rollout_type": Experiment.TYPE_PREF,
            "preferences": [
                {
                    "id": original_pref1_id,
                    "pref_name": "change.original.pref",
                    "pref_type": Experiment.PREF_TYPE_STR,
                    "pref_value": "change original pref",
                },
                {
                    "pref_name": "browser.pref3",
                    "pref_type": Experiment.PREF_TYPE_STR,
                    "pref_value": "A STRING!",
                },
            ],
        }

        serializer = ExperimentDesignPrefRolloutSerializer(
            instance=experiment, data=data, context={"request": self.request}
        )

        self.assertTrue(serializer.is_valid())
        experiment = serializer.save()

        self.assertEqual(experiment.rollout_type, data["rollout_type"])

        self.assertEqual(experiment.preferences.count(), 2)
        data_pref1 = data["preferences"][0]
        data_pref2 = data["preferences"][1]
        pref1 = experiment.preferences.get(id=original_pref1_id)
        pref2 = experiment.preferences.exclude(id=original_pref1_id)[0]

        self.assertEqual(pref1.pref_name, data_pref1["pref_name"])
        self.assertEqual(pref1.pref_type, data_pref1["pref_type"])
        self.assertEqual(pref1.pref_value, data_pref1["pref_value"])

        self.assertEqual(pref2.pref_name, data_pref2["pref_name"])
        self.assertEqual(pref2.pref_type, data_pref2["pref_type"])
        self.assertEqual(pref2.pref_value, data_pref2["pref_value"])

    def test_serializer_outputs_empty_pref_when_no_prefs(self):
        experiment = ExperimentFactory.create(type=Experiment.TYPE_ROLLOUT)

        serializer = ExperimentDesignPrefRolloutSerializer(instance=experiment)

        self.assertEqual(serializer.data["preferences"], [{}])

    def test_serializer_outputs_expected_schema(self):
        experiment = ExperimentFactory.create(type=Experiment.TYPE_ROLLOUT)
        preference = RolloutPreference(
            pref_type=Experiment.PREF_TYPE_INT,
            pref_name="browser.pref",
            pref_value="4",
            experiment=experiment,
        )
        preference.save()

        serializer = ExperimentDesignPrefRolloutSerializer(instance=experiment)

        self.assertEqual(len(serializer.data["preferences"]), 1)
        self.assertCountEqual(
            serializer.data["preferences"],
            [
                {
                    "id": experiment.preferences.first().id,
                    "pref_name": "browser.pref",
                    "pref_value": "4",
                    "pref_type": Experiment.PREF_TYPE_INT,
                }
            ],
        )


class TestExperimentDesignAddonRolloutSerializer(MockRequestMixin, TestCase):

    def test_addon_fields_required_for_rollout_type_addon(self):
        experiment = ExperimentFactory.create(type=Experiment.TYPE_ROLLOUT)

        data = {"rollout_type": Experiment.TYPE_ADDON}

        serializer = ExperimentDesignAddonRolloutSerializer(
            instance=experiment, data=data, context={"request": self.request}
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("addon_release_url", serializer.errors)

    def test_saves_addon_rollout(self):
        experiment = ExperimentFactory.create(type=Experiment.TYPE_ROLLOUT)

        data = {
            "rollout_type": Experiment.TYPE_ADDON,
            "addon_release_url": "https://www.example.com/addon.xpi",
        }

        serializer = ExperimentDesignAddonRolloutSerializer(
            instance=experiment, data=data, context={"request": self.request}
        )

        self.assertTrue(serializer.is_valid())

        experiment = serializer.save()

        self.assertEqual(experiment.rollout_type, data["rollout_type"])
        self.assertEqual(experiment.addon_release_url, data["addon_release_url"])


class TestChangeLogSerializerMixin(MockRequestMixin, TestCase):

    def test_update_changelog_creates_no_log_when_no_change(self):
        experiment = ExperimentFactory.create_with_status(
            target_status=Experiment.STATUS_DRAFT, num_variants=0
        )
        variant = ExperimentVariantFactory.create(
            ratio=100,
            name="variant name",
            experiment=experiment,
            value=None,
            addon_release_url=None,
        )

        data = {
            "variants": [
                {
                    "id": variant.id,
                    "ratio": variant.ratio,
                    "description": variant.description,
                    "name": variant.name,
                    "is_control": variant.is_control,
                }
            ]
        }

        self.assertEqual(experiment.changes.count(), 1)
        serializer = ExperimentDesignBaseSerializer(
            instance=experiment, data=data, context={"request": self.request}
        )

        self.assertTrue(serializer.is_valid())
        experiment = serializer.save()

        self.assertEqual(experiment.changes.count(), 1)

    def test_update_change_log_creates_log_with_correct_change(self):

        experiment = ExperimentFactory.create()
        variant = ExperimentVariantFactory.create(
            experiment=experiment,
            ratio=100,
            description="it's a description",
            name="variant name",
        )

        variant_data = {
            "ratio": 100,
            "description": variant.description,
            "name": variant.name,
        }
        changed_values = {
            "variants": {
                "new_value": {"variants": [variant_data]},
                "old_value": None,
                "display_name": "Branches",
            }
        }
        ExperimentChangeLog.objects.create(
            experiment=experiment,
            changed_by=UserFactory(),
            old_status=Experiment.STATUS_DRAFT,
            new_status=Experiment.STATUS_DRAFT,
            changed_values=changed_values,
            message="",
        )

        self.assertEqual(experiment.changes.count(), 1)

        change_data = {
            "variants": [
                {
                    "id": variant.id,
                    "ratio": 100,
                    "description": "some other description",
                    "name": "some other name",
                    "is_control": False,
                }
            ]
        }
        serializer = ExperimentDesignBaseSerializer(
            instance=experiment, data=change_data, context={"request": self.request}
        )

        self.assertTrue(serializer.is_valid())
        experiment = serializer.save()

        serializer_variant_data = ExperimentVariantSerializer(variant).data

        self.assertEqual(experiment.changes.count(), 2)
        changed_values = experiment.changes.latest().changed_values

        variant = ExperimentVariant.objects.get(id=variant.id)
        changed_serializer_variant_data = ExperimentVariantSerializer(variant).data

        self.assertIn("variants", changed_values)
        self.assertEqual(
            changed_values["variants"]["old_value"], [serializer_variant_data]
        )
        self.assertEqual(
            changed_values["variants"]["new_value"], [changed_serializer_variant_data]
        )


class TestPrefValidationMixin(TestCase):

    def test_matching_json_string_type_value(self):
        pref_type = "json string"
        pref_value = "{}"
        key_value = "key_value"
        validator = PrefValidationMixin()
        value = validator.validate_pref_value(pref_type, pref_value, key_value)

        self.assertEqual(value, {})

    def test_non_matching_json_string_type_value(self):
        pref_type = "json string"
        pref_value = "not a json string"
        key_value = "key_value"
        validator = PrefValidationMixin()
        value = validator.validate_pref_value(pref_type, pref_value, key_value)

        self.assertEqual(value, {"key_value": "The pref value must be valid JSON."})

    def test_matching_integer_type_value(self):
        pref_type = "integer"
        pref_value = "8"
        key_value = "key_value"
        validator = PrefValidationMixin()
        value = validator.validate_pref_value(pref_type, pref_value, key_value)

        self.assertEqual(value, {})

    def test_non_matching_integer_type_value(self):
        pref_type = "integer"
        pref_value = "not a integer"
        key_value = "key_value"
        validator = PrefValidationMixin()
        value = validator.validate_pref_value(pref_type, pref_value, key_value)

        self.assertEqual(value, {"key_value": "The pref value must be an integer."})

    def test_matching_boolean_type_value(self):
        pref_type = "boolean"
        pref_value = "true"
        key_value = "key_value"
        validator = PrefValidationMixin()
        value = validator.validate_pref_value(pref_type, pref_value, key_value)

        self.assertEqual(value, {})

    def test_non_matching_boolean_type_value(self):
        pref_type = "boolean"
        pref_value = "not a boolean"
        key_value = "key_value"
        validator = PrefValidationMixin()
        value = validator.validate_pref_value(pref_type, pref_value, key_value)

        self.assertEqual(value, {"key_value": "The pref value must be a boolean."})

    def test_validate_multi_preference_returns_correct_errors(self):
        pref = {"pref_type": "Firefox Pref Type", "pref_value": "It's a value"}
        validator = PrefValidationMixin()
        value = validator.validate_multi_preference(pref)
        self.assertEqual(value, {"pref_type": "Please select a pref type"})

    def test_validate_missing_pref_type_returns_proper_errors(self):
        pref_branch = "Firefox Pref Branch"
        validator = PrefValidationMixin()
        value = validator.validate_pref_branch(pref_branch)
        self.assertEqual(value, {"pref_branch": "Please select a branch"})
