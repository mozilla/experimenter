from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.http import HttpResponse
from django.urls import Resolver404, resolve
from rest_framework.authentication import SessionAuthentication


class OpenIDCAuthMiddleware(AuthenticationMiddleware):
    """
    An authentication middleware that depends on a header being set in the
    request. This header will be populated by nginx configured to authenticate
    with OpenIDC.

    We will automatically create a user object and attach it to the
    experimenters group.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.User = get_user_model()

    def __call__(self, request):
        try:
            resolved = resolve(request.path)
            if resolved.url_name in settings.OPENIDC_AUTH_WHITELIST:
                # If the requested path is in our auth whitelist,
                # skip authentication entirely
                return self.get_response(request)
        except Resolver404:
            pass

        default_email = settings.DEV_USER_EMAIL if settings.DEBUG else None
        openidc_email = request.META.get(settings.OPENIDC_EMAIL_HEADER, default_email)

        if openidc_email is None:
            # If a user has bypassed the OpenIDC flow entirely and no header
            # is set then we reject the request entirely
            return HttpResponse("Please login using OpenID Connect", status=401)

        try:
            user = self.User.objects.get(username=openidc_email)
        except self.User.DoesNotExist:
            user = self.User(username=openidc_email, email=openidc_email)
            if user.email == settings.DEV_USER_EMAIL and settings.DEBUG:
                user.is_superuser = True
                user.is_staff = True
            user.save()

        request.user = user

        return self.get_response(request)


class OpenIDCRestFrameworkAuthenticator(SessionAuthentication):
    def authenticate(self, request):
        authenticated_user = getattr(request._request, "user", None)

        if authenticated_user:
            return (authenticated_user, None)

        return super().authenticate(request)
