import datetime
import unittest
import zipfile
from io import BytesIO
from unittest import mock

from experimenter.klaatu.client import (
    KlaatuClient,
    KlaatuError,
    KlaatuStatus,
    KlaatuTargets,
    KlaatuWorkflows,
)


class TestKlaatuClient(unittest.TestCase):
    def setUp(self):
        self.client = KlaatuClient(KlaatuWorkflows.WINDOWS, "123abc456xzy")

    @mock.patch("experimenter.klaatu.client.requests.post")
    def test_run_test_success(self, mock_post):
        mock_post.return_value.status_code = 204

        self.client.run_test(
            experiment_slug="training-only-for-dev-tools",
            branch_slugs=["control"],
            targets=[KlaatuTargets.LATEST_BETA, "137.0"],
            server="stage",
        )

    @mock.patch("experimenter.klaatu.client.requests.post")
    def test_run_test_raises_on_failed_post(self, mock_post):
        mock_post.return_value.status_code = 400
        mock_post.return_value.text = "Bad Request"

        with self.assertRaises(KlaatuError) as error:
            self.client.run_test("slug", ["branch"], [KlaatuTargets.LATEST_RELEASE])

        self.assertIn("Failed to trigger workflow", str(error.exception))

    @mock.patch("experimenter.klaatu.client.requests.get")
    def test_find_run_id_returns_correct_id(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "workflow_runs": [
                {"id": "123", "display_title": "Test for test-experiment"},
                {"id": "456", "display_title": "Test for other-experiment"},
            ]
        }

        run_id = self.client.find_run_ids("test-experiment")
        self.assertEqual(run_id[0], 123)

    @mock.patch("experimenter.klaatu.client.requests.get")
    def test_find_run_id_returns_none_when_not_found(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "workflow_runs": [
                {"id": "12345", "display_title": "Test for other-experiment"},
            ]
        }

        run_id = self.client.find_run_ids("test-experiment")
        self.assertListEqual(run_id, [])

    @mock.patch("experimenter.klaatu.client.requests.get")
    def test_find_run_id_raises_on_server_error(self, mock_get):
        mock_get.return_value.status_code = 500
        mock_get.return_value.text = "Internal Server Error"

        with self.assertRaises(KlaatuError) as error:
            self.client.find_run_ids("test-experiment")

        self.assertIn("Failed to fetch workflow runs", str(error.exception))

    @mock.patch("experimenter.klaatu.client.requests.get")
    def test_find_run_id_includes_dispatched_at_filter(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "workflow_runs": [
                {"id": "12345", "display_title": "Test for test-experiment"},
            ]
        }

        dispatched_at = datetime.datetime(2025, 4, 20, 15, 30)
        run_id = self.client.find_run_ids("test-experiment", dispatched_at)[0]

        self.assertEqual(run_id, 12345)

    @mock.patch("experimenter.klaatu.client.requests.get")
    def test_is_job_complete_returns_true(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"status": KlaatuStatus.COMPLETE}

        self.assertTrue(self.client.is_job_complete(12345))

    @mock.patch("experimenter.klaatu.client.requests.get")
    def test_is_job_complete_returns_false(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"status": "in_progress"}

        self.assertFalse(self.client.is_job_complete(12345))

    @mock.patch("experimenter.klaatu.client.requests.get")
    def test_is_job_complete_raises_on_failure(self, mock_get):
        mock_get.return_value.status_code = 403
        mock_get.return_value.text = "Forbidden"

        with self.assertRaises(KlaatuError) as error:
            self.client.is_job_complete(12345)

        self.assertIn("Failed to check job status", str(error.exception))

    @mock.patch("experimenter.klaatu.client.requests.get")
    def test_fetch_artifact_returns_html_dict(self, mock_get):
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as file:
            file.writestr("index.html", "<html>Test</html>")

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
            mock.Mock(status_code=200, content=zip_buffer.getvalue()),
        ]

        result = self.client.fetch_artifacts(12345)
        self.assertEqual(list(result.keys()), ["artifact-slug"])
        self.assertIn("<html>", result["artifact-slug"])

    @mock.patch("experimenter.klaatu.client.requests.get")
    def test_fetch_artifact_raises_if_not_found(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"artifacts": []}

        with self.assertRaises(KlaatuError) as error:
            self.client.fetch_artifacts(12345)

        self.assertIn("No artifact found for job 12345", str(error.exception))

    @mock.patch("experimenter.klaatu.client.requests.get")
    def test_fetch_artifact_raises_on_bad_response(self, mock_get):
        mock_get.return_value.status_code = 500
        mock_get.return_value.text = "Internal Server Error"

        with self.assertRaises(KlaatuError) as error:
            self.client.fetch_artifacts(12345)

        self.assertIn("Failed to get artifacts", str(error.exception))

    @mock.patch("experimenter.klaatu.client.requests.get")
    def test_fetch_artifact_raises_on_failed_download(self, mock_get):
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

        with self.assertRaises(KlaatuError) as error:
            self.client.fetch_artifacts(12345)

        self.assertIn("Failed to download artifact", str(error.exception))
