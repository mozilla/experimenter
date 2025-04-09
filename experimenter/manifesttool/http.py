import requests

_client = None


def http_client():
    global _client

    if _client is None:
        _client = requests.Session()
        _client.headers.update(
            {
                "User-Agent": "experimenter-manifest-tool",
            }
        )

    return _client
