from collections import defaultdict

from django.core.management.base import BaseCommand, CommandError

from mep.people.models import Person, Address, Country, InfoURL
from mep.people.xml_models import Personography

class Command(BaseCommand):
    '''Import personography data from TEI file'''
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument('path',
            help='''Path to personography XML file.''')

    def handle(self, *args, **kwargs):
        try:
            personog = Personography.from_file(kwargs['path'])
        except:
            raise CommandError('Failed to load personography "%(path)s"' %
                kwargs)
        self.stdout.write('Found %d people in XML personography' % len(personog.people))

        # get totals from the database before adding anything
        start_totals = {
            'people': Person.objects.count(),
            'addresses': Address.objects.count(),
            'countries': Country.objects.count(),
            'urls': InfoURL.objects.count(),
        }

        # loop through people in the personograpy and create records in the db
        for xml_person in personog.people:
            # only import if person is not already in the database
            if not xml_person.is_imported():
                xml_person.to_db_person()

        # report how many items were added
        new_totals = {
            'people': Person.objects.count(),
            'addresses': Address.objects.count(),
            'countries': Country.objects.count(),
            'urls': InfoURL.objects.count(),
        }
        for i in ['people', 'addresses', 'countries', 'urls']:
            self.stdout.write('%d %s added (%d total)' % \
                (new_totals[i] - start_totals[i], i, new_totals[i]))


