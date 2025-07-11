class CirrusMiddleware:
    """
    A middleware that provides experiment enrollment information via nimbus.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.cirrus_url = settings.CIRRUS_URL

    def __call__(self, request):
        request.cirrus = {}
        if hasattr(request, "user") and request.user.id and self.cirrus_url:
            try:
                cirrus_response = requests.get(
                    cirrus_url, json={"client_id": request.user.id, "context": {}}
                )
                request.cirrus = cirrus_response.json()
            except requests.exceptions.RequestException as e:
                pass  # FIXME: log cirrus failure
        return self.get_response(request)
