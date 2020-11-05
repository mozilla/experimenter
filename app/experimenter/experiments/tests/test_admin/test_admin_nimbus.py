import json

from django.test import TestCase

from experimenter.experiments.admin.nimbus import (
    NimbusBranchAdminForm,
    NimbusExperimentAdminForm,
    NimbusFeatureConfigAdminForm,
)
from experimenter.experiments.tests.factories import (
    NimbusBranchFactory,
    NimbusExperimentFactory,
    NimbusFeatureConfigFactory,
)


class TestNimbusBranchAdminForm(TestCase):
    def setUp(self):
        self.schema = """
        {
            "$id": "https://example.com/person.schema.json",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "Person",
            "type": "object",
            "properties": {
                "firstName": {
                "type": "string",
                "description": "The person's first name."
                },
                "lastName": {
                "type": "string",
                "description": "The person's last name."
                },
                "age": {
                "description": "Age in years",
                "type": "integer",
                "minimum": 0
                }
            }
        }
        """

    def test_form_rejects_invalid_json(self):
        feature_config = NimbusFeatureConfigFactory(schema=self.schema)
        experiment = NimbusExperimentFactory.create(feature_config=feature_config)
        branch = NimbusBranchFactory.create(experiment=experiment)

        form = NimbusBranchAdminForm(
            instance=branch,
            data={"experiment": experiment, "feature_value": "{invalid"},
        )
        self.assertFalse(form.is_valid())
        self.assertIn("feature_value", form.errors)

    def test_form_rejects_invalid_feature_value(self):
        feature_config = NimbusFeatureConfigFactory(schema=self.schema)
        experiment = NimbusExperimentFactory.create(feature_config=feature_config)
        branch = NimbusBranchFactory.create(experiment=experiment)

        form = NimbusBranchAdminForm(
            instance=branch,
            data={
                "experiment": experiment,
                "feature_value": json.dumps(
                    {
                        "firstName": 1,
                        "lastName": 2,
                        "age": "three",
                    }
                ),
            },
        )
        self.assertFalse(form.is_valid())
        self.assertIn("feature_value", form.errors)

    def test_form_accepts_valid_feature_value(self):
        feature_config = NimbusFeatureConfigFactory(schema=self.schema)
        experiment = NimbusExperimentFactory.create(feature_config=feature_config)
        branch = NimbusBranchFactory.create(experiment=experiment)

        form = NimbusBranchAdminForm(
            instance=branch,
            data={
                "experiment": experiment,
                "feature_value": json.dumps(
                    {
                        "firstName": "John",
                        "lastName": "Jacob",
                        "age": 3,
                    }
                ),
            },
        )
        self.assertFalse(form.is_valid())
        self.assertNotIn("feature_value", form.errors)


class TestNimbusExperimentAdminForm(TestCase):
    def test_form_rejects_any_branch_if_no_experiment_provided(self):
        branch = NimbusBranchFactory.create()

        form = NimbusExperimentAdminForm(data={"reference_branch": branch.id})
        self.assertFalse(form.is_valid())
        self.assertIn("reference_branch", form.errors)

    def test_form_rejects_reference_branch_from_other_experiment(self):
        experiment = NimbusExperimentFactory.create()
        branch = NimbusBranchFactory.create()

        form = NimbusExperimentAdminForm(
            instance=experiment, data={"reference_branch": branch.id}
        )
        self.assertFalse(form.is_valid())
        self.assertIn("reference_branch", form.errors)

    def test_form_accepts_reference_branch_from_same_experiment(self):
        experiment = NimbusExperimentFactory.create()
        branch = NimbusBranchFactory.create(experiment=experiment)

        form = NimbusExperimentAdminForm(
            instance=experiment,
            data={"reference_branch": branch.id},
        )
        self.assertFalse(form.is_valid())
        self.assertNotIn("reference_branch", form.errors)


class TestNimbusFeatureConfigAdminForm(TestCase):
    def test_form_rejects_invalid_json(self):
        form = NimbusFeatureConfigAdminForm(
            data={"schema": "{invalid"},
        )
        self.assertFalse(form.is_valid())
        self.assertIn("schema", form.errors)

    def test_form_accepts_valid_json(self):
        form = NimbusFeatureConfigAdminForm(
            data={"schema": '{"schema": "my schema"}'},
        )
        self.assertFalse(form.is_valid())
        self.assertNotIn("schema", form.errors)
