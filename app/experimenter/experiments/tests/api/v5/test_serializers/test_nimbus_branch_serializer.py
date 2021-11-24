from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from experimenter.experiments.api.v5.serializers import (
    NimbusBranchReadyForReviewSerializer,
    NimbusBranchSerializer,
)
from experimenter.experiments.models.nimbus import NimbusBranch
from experimenter.experiments.tests.factories import (
    TINY_PNG,
    NimbusBranchFactory,
    NimbusBranchScreenshotFactory,
)


class TestNimbusBranchSerializer(TestCase):
    def test_branch_validates(self):
        branch_data = {
            "name": "control",
            "description": "a control",
            "ratio": 1,
            "feature_enabled": True,
            "feature_value": "{}",
        }
        branch_serializer = NimbusBranchSerializer(data=branch_data)
        self.assertTrue(branch_serializer.is_valid())

    def test_branch_missing_feature_value(self):
        branch_data = {
            "name": "control",
            "description": "a control",
            "ratio": 1,
            "feature_enabled": True,
        }
        branch_serializer = NimbusBranchSerializer(data=branch_data)
        self.assertFalse(branch_serializer.is_valid())
        self.assertEqual(
            branch_serializer.errors,
            {"feature_value": ["A value must be supplied for an enabled feature."]},
        )

    def test_branch_missing_feature_enabled(self):
        branch_data = {
            "name": "control",
            "description": "a control",
            "ratio": 1,
            "feature_value": "{}",
        }
        branch_serializer = NimbusBranchSerializer(data=branch_data)
        self.assertFalse(branch_serializer.is_valid())
        self.assertEqual(
            branch_serializer.errors,
            {
                "feature_value": [
                    "feature_enabled must be specificed to include a feature_value."
                ]
            },
        )

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

    def test_branch_with_invalid_feature_value_json(self):
        branch_data = {
            "name": "control",
            "description": "a control",
            "ratio": 1,
            "feature_enabled": True,
            "feature_value": "invalid json",
        }
        branch_serializer = NimbusBranchReadyForReviewSerializer(data=branch_data)
        self.assertFalse(branch_serializer.is_valid())
        self.assertIn("feature_value", branch_serializer.errors)

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
