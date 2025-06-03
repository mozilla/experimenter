import uuid

from locust import HttpUser, task, between

class BasicApiUser(HttpUser):
    wait_time = between(1, 3)  # seconds between tasks
    example_context = {
        "key1": "value1",
        "key2": {
            "key2.1": "value2",
            "key2.2": "value3"
        },
        "language": "en",
        "region": "US",
        "random_key": "gold_team_rules",
    }

    @task(5)
    def get_root(self):
        with self.client.get(
            "/",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"{response.status_code=}, expected 200, {response.text=}")

    @task(3)
    def post_v1_features(self):

        with self.client.post(
            "/v1/features/",
            json={"client_id": f"{uuid.uuid4()}", "context": self.example_context},
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"{response.status_code=}, expected 200, {response.text=}")
            if isinstance(response.json(), dict) is False:
                response.failure(f"{response.status_code=}, expected a JSON response, {response.text=}")


    @task(3)
    def post_v2_features(self):

        with self.client.post(
            "/v2/features/",
            json={"client_id": f"{uuid.uuid4()}", "context": self.example_context},
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"{response.status_code=}, expected 200, {response.text=}")
