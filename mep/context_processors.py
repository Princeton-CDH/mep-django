from django.conf import settings
from wagtail.models import Site


def template_settings(request):
    """Template context processor: add selected setting to context
    so it can be used on any page ."""

    site = Site.find_for_request(request)

    context_extras = {
        "SHOW_TEST_WARNING": getattr(settings, "SHOW_TEST_WARNING", False),
        "GTAGS_ANALYTICS_ID": getattr(settings, "GTAGS_ANALYTICS_ID", None),
        "GTAGS_ANALYTICS_ENV": getattr(settings, "GTAGS_ANALYTICS_ENV", None),
        "site": site,
        # needed for footer; easier to get here than in template
        "about_page": site.root_page.get_children().filter(slug="about").first(),
        "PLAUSIBLE_ANALYTICS_SCRIPT": getattr(
            settings, "PLAUSIBLE_ANALYTICS_SCRIPT", None
        ),
        "PLAUSIBLE_ANALYTICS_404s": getattr(
            settings, "PLAUSIBLE_ANALYTICS_404s", False
        ),
    }
    return context_extras
