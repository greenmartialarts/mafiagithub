from .utils.changelog import get_changelog
from django.conf import settings

def version_info(request):
    """Makes the current version number available to all templates"""
    changelog = get_changelog()
    current_version = changelog[0]['version'] if changelog else 'Unknown'
    return {
        'current_version': current_version,
        'turnstile_site_key': settings.TURNSTILE_SITE_KEY
    } 