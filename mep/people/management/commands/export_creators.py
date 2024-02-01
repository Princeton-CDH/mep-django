"""
Manage command to export creator data for use by others.

Generates a CSV and JSON file including details on every creator
database, with summary details and coordinates for associated addresses.

"""

from mep.people.models import Person
from mep.books.models import Creator
from mep.people.management.commands.export_members import Command as ExportMemberCommand


class Command(ExportMemberCommand):
    """Export member data."""

    csv_fields = [
        "id",  # will be saved as id
        "name",
        "sort_name",
        "title",
        "gender",
        "is_organization",
        "birth_year",
        "death_year",
        "viaf_url",
        "wikipedia_url",
        # related country
        "nationalities",
        # generic
        "notes",
        "updated",
    ]

    def get_queryset(self):
        """filter to creators"""
        return Person.objects.filter(creator__isnull=False)

    def get_base_filename(self):
        """set the filename to "creators.csv" since it's a subset of people"""
        return "creators"
