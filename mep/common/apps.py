from django.apps import AppConfig


class CommonConfig(AppConfig):
    name = 'mep.common'

    def ready(self):
        # import and connect signal handlers for Solr indexing
        from parasolr.django.signals import IndexableSignalHandler
