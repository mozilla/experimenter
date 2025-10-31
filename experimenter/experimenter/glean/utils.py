def get_request_ip(request) -> None | str:
    if xff := request.META.get("HTTP_X_FORWARDED_FOR"):
        # The last two ips are both the google cloud load balancer, before that is the
        # client ip as determined by the gclb, and before that is the untrusted
        # client-provided XFF value, so return the 3rd to last value, and gracefully
        # handle less than 3 values.
        return xff.rsplit(",", 4)[-3:][0]
    return request.META.get("REMOTE_ADDR")
