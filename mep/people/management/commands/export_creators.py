"""
Manage command to export creator data for use by others.

Generates a CSV and JSON file including details on every creator
(author, translated, editor, etc) in the database, with details
on creator nationality, gender, and other information.
"""

from mep.people.models import Person
from mep.people.management.commands.export_members import Command as ExportMemberCommand
from django.db.models import Prefetch


class Command(ExportMemberCommand):
    """Export creator data."""

    csv_fields = [
        "id",  # no URI for authors so using slug as ID
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
        return (
            Person.objects.filter(creator__isnull=False)
            .prefetch_related(Prefetch("nationalities"))
            .distinct()
        )

    def get_base_filename(self):
        """set the filename to "creators.csv" since it's a subset of people"""
        return "creators"
