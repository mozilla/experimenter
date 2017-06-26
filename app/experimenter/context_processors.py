from django.conf import settings


def disqus_context(request):
    return {
        'DISQUS_URL': settings.DISQUS_URL,
    }
