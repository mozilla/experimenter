import unittest
from io import BytesIO
from unittest import mock

from experimenter.klaatu.client import KlaatuClient


class TestKlaatuClient(unittest.TestCase):
    def setUp(self):
        self.client = KlaatuClient(workflow_name="windows_manual.yml")

    @mock.patch("time.sleep", return_value=None)
    @mock.patch("requests.get")
    @mock.patch("requests.post")
    def test_run_test_returns_expected_run_id(self, mock_post, mock_get, mock_sleep):
        mock_post.return_value.status_code = 204
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "workflow_runs": [
                {
                    "id": 12345,
                    "display_title": "Experiment Smoke tests for "
                    "training-only-for-dev-tools",
                }
            ]
        }

        run_id = self.client.run_test(
            experiment_slug="training-only-for-dev-tools",
            branch_slug="control",
            targets=["latest-beta", "latest", "137.0"],
        )

        self.assertEqual(run_id, 12345)

    @mock.patch("requests.post")
    def test_run_test_raises_on_failed_post(self, mock_post):
        mock_post.return_value.status_code = 400
        mock_post.return_value.text = "Bad Request"

        with self.assertRaises(Exception) as error:
            self.client.run_test("slug", "branch", ["latest-beta", "latest", "137.0"])

        self.assertIn("Failed to trigger workflow", str(error.exception))

    @mock.patch("time.sleep", return_value=None)
    @mock.patch("requests.get")
    @mock.patch("requests.post")
    def test_run_test_timeout_no_run_found(self, mock_post, mock_get, mock_sleep):
        mock_get.return_value.status_code = 500
        mock_get.return_value.text = "Server Error"
        mock_post.return_value.status_code = 204
        with self.assertRaises(Exception) as error:
            self.client.run_test("slug", "branch", ["latest-beta", "latest", "137.0"])

        self.assertIn("Could not find the workflow run", str(error.exception))

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
    def test_is_job_complete_raises_on_failure(self, mock_get):
        mock_get.return_value.status_code = 403
        mock_get.return_value.text = "Forbidden"

        with self.assertRaises(Exception) as error:
            self.client.is_job_complete(12345)

        self.assertIn("Failed to check job status", str(error.exception))

    @mock.patch("requests.get")
    def test_download_artifact_extracts_file(self, mock_get):
        mock_extractall = mock.Mock()
        mock_zip = mock.MagicMock()
        mock_zip.__enter__.return_value.extractall = mock_extractall

        with mock.patch("zipfile.ZipFile", return_value=mock_zip):
            mock_get.side_effect = [
                mock.Mock(
                    status_code=200,
                    json=mock.Mock(
                        return_value={
                            "artifacts": [
                                {
                                    "workflow_run": {"id": 12345},
                                    "archive_download_url": "https://testurl.com",
                                    "name": "artifact-slug",
                                }
                            ]
                        }
                    ),
                ),
                mock.Mock(status_code=200, content=BytesIO().getvalue()),
            ]

            self.client.download_artifact(12345)
            mock_extractall.assert_called_once()

    @mock.patch("requests.get")
    def test_download_artifact_raises_if_not_found(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"artifacts": []}

        with self.assertRaises(Exception) as error:
            self.client.download_artifact(12345)

        self.assertIn("No artifact found for job", str(error.exception))

    @mock.patch("requests.get")
    def test_download_artifact_raises_on_bad_artifact_response(self, mock_get):
        mock_get.return_value.status_code = 500
        mock_get.return_value.text = "Internal Server Error"

        with self.assertRaises(Exception) as error:
            self.client.download_artifact(12345)

        self.assertIn("Failed to get artifacts", str(error.exception))

    @mock.patch("requests.get")
    def test_download_artifact_raises_on_failed_download(self, mock_get):
        mock_get.side_effect = [
            mock.Mock(
                status_code=200,
                json=mock.Mock(
                    return_value={
                        "artifacts": [
                            {
                                "workflow_run": {"id": 12345},
                                "archive_download_url": "https://testurl.com",
                                "name": "fail-artifact",
                            }
                        ]
                    }
                ),
            ),
            mock.Mock(status_code=403, text="Forbidden"),
        ]

        with self.assertRaises(Exception) as error:
            self.client.download_artifact(12345)

        self.assertIn("Failed to download artifact", str(error.exception))
