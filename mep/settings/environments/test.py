from mep.settings import DATABASES, SOLR_CONNECTIONS

# These settings correspond to the service container settings in the
# .github/workflow .yml files.
DATABASES["default"].update(
    {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "shxco",
        "USER": "shxco",
        "PASSWORD": "shxco",
        "HOST": "127.0.0.1",
        "PORT": "5432",
        "TEST": {
            "CHARSET": "utf8",
        },
    }
)
SOLR_CONNECTIONS["default"].update(
    {
        "URL": "http://localhost:8983/solr/",
        "COLLECTION": "sandco",
        "CONFIGSET": "sandco",
        "TEST": {
            # aggressive commitWithin for test only
            "COMMITWITHIN": 750,
        },
    }
)

# turn off debug so we see 404s when testing
DEBUG = False

# required for tests when DEBUG = False
ALLOWED_HOSTS = ["*"]
