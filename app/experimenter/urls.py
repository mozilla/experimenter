from django.conf.urls import url, include
from django.contrib import admin


urlpatterns = [
    url(r'^api/v1/', include('experimenter.experiments.urls')),
    url(r'^', admin.site.urls),
]
