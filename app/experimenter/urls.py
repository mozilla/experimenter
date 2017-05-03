from django.conf import settings
from django.conf.urls import url
from django.conf.urls.static import static
from django.contrib import admin


urlpatterns = [
    url(r'^', admin.site.urls),
]

if settings.DEBUG:  # pragma: no cover
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.STATIC_ROOT)
