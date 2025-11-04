def get_request_ip(request) -> None | str:
    if xff := request.META.get("HTTP_X_FORWARDED_FOR"):
        # Only trust the last 3 values in XFF because they are added by the Google Cloud
        # Load Balancer and nginx, and use the least recent of those values.
        return xff.rsplit(",", 4)[-3:][0]
    return request.META.get("REMOTE_ADDR")
