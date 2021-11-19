'''
Django app for shared code and functionality used
across other applications within the project.  Currently includes
abstract database models with common functionality or fields that are
used by models in multiple apps within the project.
'''
import rdflib


SCHEMA_ORG = rdflib.Namespace('http://schema.org/')
