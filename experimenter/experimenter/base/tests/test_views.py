from django.test import TestCase, override_settings


@override_settings(DEBUG=False)
class TestHeartbeats(TestCase):
    def test_heartbeat(self):
        response = self.client.get("/__heartbeat__")
        self.assertEqual(response.status_code, 200)

    def test_lbheartbeat(self):
        response = self.client.get("/__lbheartbeat__")
        self.assertEqual(response.status_code, 200)
