from django.conf.urls import url

from experimenter.monitoring.views import (
    VersionView, LBHeartbeatView, HeartbeatView)

urlpatterns = [
    url('^__version__$', VersionView.as_view(),
        name='monitoring-version'),
    url('^__heartbeat__$', HeartbeatView.as_view(),
        name='monitoring-heartbeat'),
    url('^__lbheartbeat__$', LBHeartbeatView.as_view(),
        name='monitoring-lbheartbeat'),
]
