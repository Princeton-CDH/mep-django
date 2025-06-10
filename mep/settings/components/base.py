"""
Django settings for mep project.
"""

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
# called from mep-django/mep/settings/__init__.py
# do NOT import this module directly, the path will be different
PROJECT_APP_PATH = Path(__file__).resolve().parent.parent
PROJECT_APP = PROJECT_APP_PATH.name
# base dir is one level up from that (mep-django)
BASE_DIR = PROJECT_APP_PATH.parent

# Default debug to False, override locally
DEBUG = False

# Override in local settings, if using DEBUG = True locally, 'localhost'
# and variations allowed
ALLOWED_HOSTS = []

# Application definition
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    # auto-complete light before grappelli & admin to override jquery init
    "dal",
    "dal_select2",
    "grappelli.dashboard",
    "grappelli",
    "django.contrib.admin",
    "django.contrib.messages",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.sitemaps",
    "django.contrib.staticfiles",
    "django.contrib.redirects",
    "django.contrib.humanize",
    "django_cas_ng",
    "pucas",
    "viapy",
    "parasolr",
    "djiffy",
    "fullurl",
    "admin_log_entries",
    "webpack_loader",
    "wagtail.sites",
    "wagtail.users",
    "wagtail.snippets",
    "wagtail.documents",
    "wagtail.images",
    "wagtail.admin",
    "wagtail.contrib.legacy.richtext",  # preserve rich-text class behavior after wagtail 2.10
    "wagtail.contrib.settings",
    "wagtail",
    "wagtail.embeds",
    "wagtail.contrib.redirects",
    "taggit",
    "widget_tweaks",
    "markdownify",
    # local apps
    "mep.common",
    "mep.people",
    "mep.accounts",
    "mep.books",
    "mep.footnotes",
    "mep.pages",
    "import_export",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "wagtail.contrib.legacy.sitemiddleware.SiteMiddleware",
    "wagtail.contrib.redirects.middleware.RedirectMiddleware",
    "csp.middleware.CSPMiddleware",
]

AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "django_cas_ng.backends.CASBackend",
)

ROOT_URLCONF = "mep.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "mep.context_extras",
                "mep.context_processors.template_settings",
                "wagtail.contrib.settings.context_processors.settings",
            ],
            "loaders": [
                "apptemplates.Loader",
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
            ],
        },
    },
]

WSGI_APPLICATION = "mep.wsgi.application"


DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

GRAPPELLI_ADMIN_TITLE = "Shakespeare & Company Project Admin"

WAGTAIL_SITE_NAME = "Shakespeare & Company Project"

WAGTAILADMIN_BASE_URL = "https://shakespeareandco.princeton.edu/cms/"

# mezzanine integration package names (normally uses custom forks)
PACKAGE_NAME_FILEBROWSER = "filebrowser_safe"
PACKAGE_NAME_GRAPPELLI = "grappelli"


# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "America/New_York"

USE_I18N = True

USE_TZ = True

# Use three-letter month names everywhere (instead of default AP style)
DATE_FORMAT = "M j, Y"

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_URL = "/static/"

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = BASE_DIR / STATIC_URL.strip("/")


# Additional locations of static files
STATICFILES_DIRS = [
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    BASE_DIR / "sitemedia",
    BASE_DIR / "bundles",
]

# These will be added to ``INSTALLED_APPS``, only if available.
# NOTE: this is mezzanine-specific; probably remove
OPTIONAL_APPS = (
    "debug_toolbar",
    "django_extensions",
    PACKAGE_NAME_FILEBROWSER,
    PACKAGE_NAME_GRAPPELLI,
)


WAGTAILEMBEDS_FINDERS = [
    {"class": "wagtail.embeds.finders.oembed"},
    {"class": "mep.pages.embed_finders.GlitchHubEmbedFinder"},
]


# pucas configuration that is not expected to change across deploys
# and does not reference local server configurations or fields
PUCAS_LDAP = {
    # basic user profile attributes
    "ATTRIBUTES": ["givenName", "sn", "mail"],
    "ATTRIBUTE_MAP": {
        "first_name": "givenName",
        "last_name": "sn",
        "email": "mail",
    },
}

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = "/media/"

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = BASE_DIR / MEDIA_URL.strip("/")

SITE_ID = 1

# use grappelli custom dashboard for consistent admin menu ordering
GRAPPELLI_INDEX_DASHBOARD = "mep.dashboard.CustomIndexDashboard"

# username for logging activity by local scripts
SCRIPT_USERNAME = "script"

# django-csp configuration for content security policy definition and
# violation reporting - https://github.com/mozilla/django-csp

# fallback for all protocols: block it
CSP_DEFAULT_SRC = "'none'"

# allow loading js locally, from google (for analytics), and
# nytimes github (for svg crowbar)
CSP_SCRIPT_SRC = (
    "'self'",
    "www.googletagmanager.com",
    "*.google-analytics.com",
    "nytimes.github.io",
    "unpkg.com",
    "d3js.org",
    "princeton-cdh.github.io",
)

# allow loading fonts locally only
CSP_FONT_SRC = ("'self'",)

# allow loading css locally & via inline styles
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "unpkg.com")

# allow loading web manifest locally only
CSP_MANIFEST_SRC = ("'self'",)

# allow XMLHttpRequest or Fetch requests locally (for search), analytics & maps
CSP_CONNECT_SRC = (
    "'self'",
    "*.google-analytics.com",
    "*.arcgis.com",
    "princeton-cdh.github.io",
)

# whitelisted image sources - analytics (tracking pixel?), IIIF, maps, etc.
CSP_IMG_SRC = (
    "'self'",
    "www.googletagmanager.com",
    "*.google-analytics.com",
    "iiif.princeton.edu",
    "figgy.princeton.edu",
    "*.arcgis.com",
    "iiif-cloud.princeton.edu",
    "api.mapbox.com",
    "data:",
)

# exclude admin and cms urls from csp directives since they're authenticated
CSP_EXCLUDE_URL_PREFIXES = ("/admin", "/cms")

# allow usage of nonce for inline js (for analytics)
CSP_INCLUDE_NONCE_IN = ("script-src",)

# Django webpack loader
WEBPACK_LOADER = {
    "DEFAULT": {
        "CACHE": True,
        "BUNDLE_DIR_NAME": "bundles/",  # must end with slash
        "STATS_FILE": BASE_DIR / "webpack-stats.json",
        "POLL_INTERVAL": 0.1,
        "TIMEOUT": None,
        "IGNORE": [r".+\.hot-update.js", r".+\.map"],
    }
}

IMPORT_EXPORT_USE_TRANSACTIONS = (
    False  # before_import object creation won't work otherwise
)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "shxco",
        "USER": "shxco",
        "PASSWORD": "",
        "HOST": "",  # empty string for localhost
        "PORT": "",  # empty string for default
    }
}

SOLR_CONNECTIONS = {
    "default": {
        "URL": "http://localhost:8983/solr/",
        "COLLECTION": "shxco",
        "CONFIGSET": "shxco",
        "TEST": {
            # set aggressive commitWithin when testing
            "COMMITWITHIN": 750,
        },
    }
}
