'''
Django app for shared code and functionality used
across other applications within the project.  Currently includes
abstract database models with common functionality or fields that are
used by models in multiple apps within the project.
'''
import rdflib


default_app_config = 'mep.common.apps.CommonConfig'
SCHEMA_ORG = rdflib.Namespace('http://schema.org/')
