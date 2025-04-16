import unittest
from unittest import mock
from io import BytesIO
from experimenter.klaatu.client import KlaatuClient


class TestKlaatuClient(unittest.TestCase):
    def setUp(self):
        self.client = KlaatuClient(workflow_name="windows_manual.yml")

    @mock.patch("requests.post")
    @mock.patch("requests.get")
    def test_run_test_returns_expected_run_id(self, mock_get, mock_post):
        mock_post.return_value.status_code = 204
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "workflow_runs": [
                {"id": 12345, "display_title": "Experiment Smoke tests for training-only-for-dev-tools"}
            ]
        }

        run_id = self.client.run_test(
            experiment_slug="training-only-for-dev-tools",
            branch_slug="control",
            targets=["latest-beta", "latest", "137.0"]
        )

        self.assertEqual(run_id, 12345)

    @mock.patch("requests.get")
    def test_is_job_complete_returns_true(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"status": "completed"}

        self.assertTrue(self.client.is_job_complete(12345))

    @mock.patch("requests.get")
    def test_is_job_complete_returns_false(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"status": "in_progress"}

        self.assertFalse(self.client.is_job_complete(12345))

    @mock.patch("requests.get")
    def test_download_artifact_extracts_file(self, mock_get):
        mock_extractall = mock.Mock()
        mock_zip = mock.MagicMock()
        mock_zip.__enter__.return_value.extractall = mock_extractall

        with mock.patch("zipfile.ZipFile", return_value=mock_zip):
            mock_get.side_effect = [
                mock.Mock(status_code=200, json=mock.Mock(return_value={
                    "artifacts": [
                        {
                            "workflow_run": {"id": 8888},
                            "archive_download_url": "https://example.com/archive.zip",
                            "name": "artifact-slug"
                        }
                    ]
                })),
                mock.Mock(status_code=200, content=BytesIO().getvalue())
            ]

            self.client.download_artifact(8888)
            mock_extractall.assert_called_once()

    @mock.patch("requests.get")
    def test_download_artifact_raises_if_not_found(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"artifacts": []}

        with self.assertRaises(Exception) as error:
            self.client.download_artifact(9999)

        self.assertIn("No artifact found for job", str(error.exception))
