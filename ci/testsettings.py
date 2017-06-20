# This file is exec'd from settings.py, so it has access to and can
# modify all the variables in settings.py.

# If this file is changed in development, the development server will
# have to be manually restarted because changes will not be noticed
# immediately.

DEBUG = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'root',
        'USER': 'travismep',
        'PASSWORD': '',
        'HOST': '127.0.0.1',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'read_default_file': '~travis/.my.cnf'
        },
        'PORT': '',
        'TEST': {
                'CHARSET': 'utf8',
                'COLLATION': 'utf8_general_ci',
                'OPTIONS': {
                    'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
                },
            },
    },
}

# secret key added as a travis build step
