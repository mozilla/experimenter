from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from experimenter.experiments.api.v5.serializers import NimbusBranchSerializer
from experimenter.experiments.models.nimbus import NimbusBranch, NimbusBranchFeatureValue
from experimenter.experiments.tests.factories import (
    TINY_PNG,
    NimbusBranchFactory,
    NimbusBranchScreenshotFactory,
)
from experimenter.experiments.tests.factories.nimbus import (
    NimbusExperimentFactory,
    NimbusFeatureConfigFactory,
)


class TestNimbusBranchSerializer(TestCase):
    def test_saves_new_branch_with_feature_values_without_feature(self):
        experiment = NimbusExperimentFactory.create(feature_configs=[])

        data = {
            "name": "new branch",
            "description": "a new branch",
            "ratio": 1,
            "feature_values": [
                {
                    "feature_config": None,
                    "enabled": True,
                    "value": "feature1 value",
                },
                {
                    "feature_config": None,
                    "enabled": True,
                    "value": "feature2 value",
                },
            ],
        }
        serializer = NimbusBranchSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        branch = serializer.save(experiment=experiment)
        self.assertEqual(branch.experiment, experiment)
        self.assertEqual(branch.name, "new branch")
        self.assertEqual(branch.slug, "new-branch")
        self.assertEqual(branch.description, "a new branch")
        self.assertEqual(branch.ratio, 1)
        self.assertEqual(branch.feature_values.count(), 2)

        for feature_value_data in data["feature_values"]:
            self.assertTrue(
                NimbusBranchFeatureValue.objects.filter(
                    branch=branch, **feature_value_data
                ).exists()
            )

    def test_saves_new_branch_with_feature_values(self):
        feature1 = NimbusFeatureConfigFactory.create(name="feature1")
        feature2 = NimbusFeatureConfigFactory.create(name="feature2")
        experiment = NimbusExperimentFactory.create(feature_configs=[feature1, feature2])

        data = {
            "name": "new branch",
            "description": "a new branch",
            "ratio": 1,
            "feature_values": [
                {
                    "feature_config": feature1.id,
                    "enabled": True,
                    "value": "feature1 value",
                },
                {
                    "feature_config": feature2.id,
                    "enabled": True,
                    "value": "feature2 value",
                },
            ],
        }
        serializer = NimbusBranchSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        branch = serializer.save(experiment=experiment)
        self.assertEqual(branch.experiment, experiment)
        self.assertEqual(branch.name, "new branch")
        self.assertEqual(branch.slug, "new-branch")
        self.assertEqual(branch.description, "a new branch")
        self.assertEqual(branch.ratio, 1)
        self.assertEqual(branch.feature_values.count(), 2)

        branch_feature1_value = branch.feature_values.get(feature_config=feature1)
        self.assertEqual(branch_feature1_value.branch, branch)
        self.assertEqual(branch_feature1_value.feature_config, feature1)
        self.assertEqual(branch_feature1_value.enabled, True)
        self.assertEqual(branch_feature1_value.value, "feature1 value")

        branch_feature2_value = branch.feature_values.get(feature_config=feature2)
        self.assertEqual(branch_feature2_value.branch, branch)
        self.assertEqual(branch_feature2_value.feature_config, feature2)
        self.assertEqual(branch_feature2_value.enabled, True)
        self.assertEqual(branch_feature2_value.value, "feature2 value")

    def test_updates_existing_branch_with_feature_values(self):
        feature1 = NimbusFeatureConfigFactory.create(name="feature1")
        feature2 = NimbusFeatureConfigFactory.create(name="feature2")
        experiment = NimbusExperimentFactory.create(feature_configs=[feature1, feature2])
        branch = experiment.branches.all()[:1][0]

        data = {
            "name": "new branch",
            "description": "a new branch",
            "ratio": 1,
            "feature_values": [
                {
                    "feature_config": feature1.id,
                    "enabled": True,
                    "value": "feature1 value",
                },
                {
                    "feature_config": feature2.id,
                    "enabled": True,
                    "value": "feature2 value",
                },
            ],
        }
        serializer = NimbusBranchSerializer(instance=branch, data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        branch = serializer.save(experiment=experiment)
        self.assertEqual(branch.experiment, experiment)
        self.assertEqual(branch.name, "new branch")
        self.assertEqual(branch.description, "a new branch")
        self.assertEqual(branch.ratio, 1)
        self.assertEqual(branch.feature_values.count(), 2)

        branch_feature1_value = branch.feature_values.get(feature_config=feature1)
        self.assertEqual(branch_feature1_value.branch, branch)
        self.assertEqual(branch_feature1_value.feature_config, feature1)
        self.assertEqual(branch_feature1_value.enabled, True)
        self.assertEqual(branch_feature1_value.value, "feature1 value")

        branch_feature2_value = branch.feature_values.get(feature_config=feature2)
        self.assertEqual(branch_feature2_value.branch, branch)
        self.assertEqual(branch_feature2_value.feature_config, feature2)
        self.assertEqual(branch_feature2_value.enabled, True)
        self.assertEqual(branch_feature2_value.value, "feature2 value")

    def test_no_duplicate_features(self):
        feature1 = NimbusFeatureConfigFactory.create(name="feature1")

        data = {
            "name": "new branch",
            "description": "a new branch",
            "ratio": 1,
            "feature_values": [
                {
                    "feature_config": feature1.id,
                    "enabled": True,
                    "value": "feature1 value",
                },
                {
                    "feature_config": feature1.id,
                    "enabled": True,
                    "value": "feature2 value",
                },
            ],
        }
        serializer = NimbusBranchSerializer(data=data)
        self.assertFalse(serializer.is_valid(), serializer.errors)

    def test_branch_name_cant_slugify(self):
        data = {
            "name": "******",
            "description": "a control",
            "ratio": 1,
        }
        serializer = NimbusBranchSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors,
            {"name": ["Name needs to contain alphanumeric characters."]},
        )

    def test_branch_update_screenshots(self):
        branch = NimbusBranchFactory()
        existing_screenshot = branch.screenshots.first()
        existing_image = existing_screenshot.image
        deleted_screenshots = [
            NimbusBranchScreenshotFactory.create(branch=branch),
            NimbusBranchScreenshotFactory.create(branch=branch),
            NimbusBranchScreenshotFactory.create(branch=branch),
        ]

        updated_screenshot_data = {
            "id": existing_screenshot.id,
            "description": "01 updated",
        }
        image_content = TINY_PNG
        new_screenshot_data = {
            "description": "02 new screenshot",
            "image": SimpleUploadedFile(name="Capture.PNG", content=image_content),
        }
        data = {
            "name": "updated name",
            "description": "updated description",
            "ratio": 1,
            "screenshots": [
                updated_screenshot_data,
                new_screenshot_data,
            ],
        }
        serializer = NimbusBranchSerializer(branch, data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()

        branch = NimbusBranch.objects.get(pk=branch.id)
        self.assertEqual(branch.screenshots.count(), 2)

        for screenshot in deleted_screenshots:
            self.assertFalse(branch.screenshots.filter(pk=screenshot.id).exists())

        screenshots = branch.screenshots.order_by("description")
        updated_screenshot = screenshots[0]
        self.assertEqual(
            updated_screenshot.description, updated_screenshot_data["description"]
        )
        self.assertEqual(updated_screenshot.image.name, existing_image.name)

        new_screenshot = screenshots[1]
        self.assertEqual(new_screenshot.description, new_screenshot_data["description"])
        self.assertTrue(bool(new_screenshot.image))
        with new_screenshot.image.open() as image_file:
            self.assertEqual(image_file.read(), image_content)
