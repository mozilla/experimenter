from django.conf import settings
from django.db import connections, OperationalError
from rest_framework.response import Response
from rest_framework.views import APIView


class VersionView(APIView):
    """
    Retrieve the latest git tag and commit versions.
    """

    def get(self, request):
        return Response(settings.GIT_VERSION_INFO)


class LBHeartbeatView(APIView):
    """
    Check that the application is running.
    """

    def get(self, request):
        return Response(status=200)


class HeartbeatView(APIView):
    """
    Check that the application is running
    and able to connect to dependent services.
    """

    def get(self, request):
        response = 200

        try:
            # Test that we are able to connect to the
            # database
            connections['default'].cursor()
        except OperationalError:
            response = 400

        return Response(status=response)
