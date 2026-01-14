from django.conf import settings

def global_settings(request):
    return {
        'USE_TAILWIND_CDN': settings.USE_TAILWIND_CDN,
    }
