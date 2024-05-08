"""
Manage command to export creator data for use by others.

Generates a CSV and JSON file including details on every creator
(author, translated, editor, etc) in the database, with details
on creator nationality, gender, and other information.
"""

from mep.people.models import Person
from mep.people.management.commands import export_members


class Command(export_members.Command):
    """Export creator data."""

    csv_fields = [
        # authors don't have public URLs, so use person slug as id
        "id",
        "name",
        "sort_name",
        "gender",
        "is_organization",
        "birth_year",
        "death_year",
        "viaf_url",
        "wikipedia_url",
        # related country
        "nationalities",
        # if also a library member, include member uri
        "member_uri",
        # generic
        "notes",
        "updated",
    ]

    def get_queryset(self):
        """filter to creators"""
        return (
            Person.objects.filter(creator__isnull=False)
            .prefetch_related(
                "nationalities",
                "account_set",  # needed to determine if member, for member uri
                "urls",
            )
            .distinct()
        )

    def get_base_filename(self):
        """set the filename to "creators.csv" since it's a subset of people"""
        return "creators"
