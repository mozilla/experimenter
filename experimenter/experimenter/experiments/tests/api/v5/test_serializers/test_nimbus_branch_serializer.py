from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from experimenter.experiments.api.v5.serializers import NimbusBranchSerializer
from experimenter.experiments.models import NimbusBranch, NimbusExperiment
from experimenter.experiments.tests.factories import (
    TINY_PNG,
    NimbusBranchFactory,
    NimbusBranchScreenshotFactory,
    NimbusExperimentFactory,
    NimbusFeatureConfigFactory,
)


class TestNimbusBranchSerializerSingleFeature(TestCase):
    def test_branch_validates(self):
        branch_data = {
            "name": "control",
            "description": "a control",
            "ratio": 1,
            "feature_value": "{}",
        }
        branch_serializer = NimbusBranchSerializer(data=branch_data)
        self.assertTrue(branch_serializer.is_valid())

    def test_branch_name_cant_slugify(self):
        branch_data = {
            "name": "******",
            "description": "a control",
            "ratio": 1,
        }
        branch_serializer = NimbusBranchSerializer(data=branch_data)
        self.assertFalse(branch_serializer.is_valid())
        self.assertEqual(
            branch_serializer.errors,
            {"name": ["Name needs to contain alphanumeric characters."]},
        )

    def test_serializer_saves_new_branch(self):
        application = NimbusExperiment.Application.DESKTOP
        feature_config = NimbusFeatureConfigFactory.create(application=application)
        experiment = NimbusExperimentFactory.create(
            application=application, feature_configs=[feature_config]
        )
        experiment.branches.all().delete()

        branch_data = {
            "name": "control",
            "description": "a control",
            "ratio": 1,
            "feature_values": [
                {
                    "feature_config": feature_config.id,
                    "value": "{}",
                },
            ],
        }

        branch_serializer = NimbusBranchSerializer(data=branch_data)
        self.assertTrue(branch_serializer.is_valid(), branch_serializer.errors)

        branch = branch_serializer.save(experiment=experiment)
        self.assertEqual(branch.name, "control")
        self.assertEqual(branch.description, "a control")
        self.assertEqual(branch.ratio, 1)

        branch_feature_value = branch.feature_values.get()
        self.assertEqual(branch_feature_value.feature_config, feature_config)
        self.assertEqual(branch_feature_value.value, "{}")

    def test_serializer_updates_existing_branch(self):
        application = NimbusExperiment.Application.DESKTOP
        feature_config = NimbusFeatureConfigFactory.create(application=application)
        experiment = NimbusExperimentFactory.create(
            application=application, feature_configs=[feature_config]
        )

        branch_data = {
            "name": "new control",
            "description": "a new control",
            "ratio": 2,
            "feature_values": [
                {
                    "feature_config": feature_config.id,
                    "value": "{}",
                }
            ],
        }

        branch_serializer = NimbusBranchSerializer(
            instance=experiment.reference_branch, data=branch_data
        )
        self.assertTrue(branch_serializer.is_valid())

        branch = branch_serializer.save(experiment=experiment)
        self.assertEqual(branch.name, "new control")
        self.assertEqual(branch.slug, "new-control")
        self.assertEqual(branch.description, "a new control")
        self.assertEqual(branch.ratio, 2)

        branch_feature_value = branch.feature_values.get()
        self.assertEqual(branch_feature_value.feature_config, feature_config)
        self.assertEqual(branch_feature_value.value, "{}")

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
        branch_data = {
            "name": "updated name",
            "description": "updated description",
            "ratio": 1,
            "screenshots": [
                updated_screenshot_data,
                new_screenshot_data,
            ],
        }
        branch_serializer = NimbusBranchSerializer(branch, data=branch_data)
        self.assertTrue(branch_serializer.is_valid(), branch_serializer.errors)
        branch_serializer.save()

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


class TestNimbusBranchSerializerMultiFeature(TestCase):
    maxDiff = None

    def test_branch_validates(self):
        branch_data = {
            "name": "control",
            "description": "a control",
            "ratio": 1,
            "feature_values": [],
        }
        branch_serializer = NimbusBranchSerializer(data=branch_data)
        self.assertTrue(branch_serializer.is_valid())

    def test_no_duplicate_feature_configs(self):
        feature_config = NimbusFeatureConfigFactory.create()
        branch_data = {
            "name": "control",
            "description": "a control",
            "ratio": 1,
            "feature_values": [
                {"feature_config": feature_config.id, "value": "{}"},
                {"feature_config": feature_config.id, "value": "{}"},
            ],
        }
        branch_serializer = NimbusBranchSerializer(data=branch_data)
        self.assertFalse(branch_serializer.is_valid())
        self.assertEqual(
            branch_serializer.errors,
            {
                "feature_values": [
                    {
                        "feature_config": (
                            NimbusExperiment.ERROR_DUPLICATE_BRANCH_FEATURE_VALUE
                        )
                    },
                    {
                        "feature_config": (
                            NimbusExperiment.ERROR_DUPLICATE_BRANCH_FEATURE_VALUE
                        )
                    },
                ]
            },
        )

    def test_serializer_saves_new_branch(self):
        application = NimbusExperiment.Application.DESKTOP
        feature_config1 = NimbusFeatureConfigFactory.create(application=application)
        feature_config2 = NimbusFeatureConfigFactory.create(application=application)
        experiment = NimbusExperimentFactory.create(
            application=application, feature_configs=[feature_config1, feature_config2]
        )
        experiment.branches.all().delete()

        branch_data = {
            "name": "control",
            "description": "a control",
            "ratio": 1,
            "feature_values": [
                {"feature_config": feature_config1.id, "value": "{}"},
                {"feature_config": feature_config2.id, "value": "{}"},
            ],
        }

        branch_serializer = NimbusBranchSerializer(data=branch_data)
        self.assertTrue(branch_serializer.is_valid())

        branch = branch_serializer.save(experiment=experiment)
        self.assertEqual(branch.name, "control")
        self.assertEqual(branch.description, "a control")
        self.assertEqual(branch.ratio, 1)

        self.assertEqual(branch.feature_values.count(), 2)
        for feature_config in [feature_config1, feature_config2]:
            branch_feature_value = branch.feature_values.get(
                feature_config=feature_config
            )
            self.assertEqual(branch_feature_value.feature_config, feature_config)
            self.assertEqual(branch_feature_value.value, "{}")

    def test_serializer_updates_existing_branch(self):
        application = NimbusExperiment.Application.DESKTOP
        feature_config1 = NimbusFeatureConfigFactory.create(application=application)
        feature_config2 = NimbusFeatureConfigFactory.create(application=application)
        experiment = NimbusExperimentFactory.create(
            application=application, feature_configs=[feature_config1, feature_config2]
        )

        branch_data = {
            "name": "new control",
            "description": "a new control",
            "ratio": 2,
            "feature_values": [
                {"feature_config": feature_config1.id, "value": "{}"},
                {"feature_config": feature_config2.id, "value": "{}"},
            ],
        }

        branch_serializer = NimbusBranchSerializer(
            instance=experiment.reference_branch, data=branch_data
        )
        self.assertTrue(branch_serializer.is_valid())

        branch = branch_serializer.save(experiment=experiment)
        self.assertEqual(branch.name, "new control")
        self.assertEqual(branch.description, "a new control")
        self.assertEqual(branch.ratio, 2)

        self.assertEqual(branch.feature_values.count(), 2)
        for feature_config in [feature_config1, feature_config2]:
            branch_feature_value = branch.feature_values.get(
                feature_config=feature_config
            )
            self.assertEqual(branch_feature_value.feature_config, feature_config)
            self.assertEqual(branch_feature_value.value, "{}")
