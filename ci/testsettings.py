# This file is exec'd from settings.py, so it has access to and can
# modify all the variables in settings.py.

# If this file is changed in development, the development server will
# have to be manually restarted because changes will not be noticed
# immediately.

import os

DEBUG = False

DB_BACKEND = os.getenv('DJANGO_DB_BACKEND')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.%s' % DB_BACKEND,
        'NAME':  os.getenv('DB_PASSWORD'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        # localhost, default port
    },
}

# mysql-specific init options
if os.getenv('DJANGO_DB_BACKEND') == 'mysql':
    DATABASES['default'].update({
        'USER': 'root',
        'OPTIONS': {
            # In each case, we want strict mode on to catch truncation issues
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
        'TEST': {
                # We also want the test database to for utf8 and the general
                # collation to keep case sensitive unicode searches working
                # as we would expect on production
                'CHARSET': 'utf8',
                'COLLATION': 'utf8_general_ci',
        }
    })


SOLR_CONNECTIONS = {
    'default': {
        'URL': 'http://localhost:8983/solr/',
        'COLLECTION': 'sandco',
        'CONFIGSET': 'sandco',
        'TEST': {
            # aggressive commitWithin for test only
            'COMMITWITHIN': 750,
        }
    }
}


# required by mezzanine for unit tests
ALLOWED_HOSTS = ['*']

# secret key added as a travis build step
