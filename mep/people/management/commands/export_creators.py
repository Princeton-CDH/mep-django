"""
Manage command to export member data for use by others.

Generates a CSV and JSON file including details on every library member in the
database, with summary details and coordinates for associated addresses.

"""

from mep.people.models import Person
from mep.books.models import Creator
from mep.people.management.commands.export_members import Command as ExportMemberCommand


class Command(ExportMemberCommand):
    """Export member data."""

    def get_queryset(self):
        """filter to creators"""
        creator_ids = {c.person_id for c in Creator.objects.all()}
        return Person.objects.filter(pk__in=creator_ids)

    def get_base_filename(self):
        """set the filename to "creators.csv" since it's a subset of people"""
        return "creators"
