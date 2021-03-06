from django.conf import settings

def template_settings(request):
    '''Template context processor: add selected setting to context
    so it can be used on any page .'''

    context_extras = {
        'SHOW_TEST_WARNING': getattr(settings, 'SHOW_TEST_WARNING', False),
        'GTAGS_ANALYTICS_ID': getattr(settings, 'GTAGS_ANALYTICS_ID', None),
        'GTAGS_ANALYTICS_ENV': getattr(settings, 'GTAGS_ANALYTICS_ENV', None)
    }
    return context_extras
