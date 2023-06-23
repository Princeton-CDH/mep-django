"""
Manage command to export member data for use by others.

Generates a CSV and JSON file including details on every library member in the
database, with summary details and coordinates for associated addresses.

"""

from collections import OrderedDict

from mep.common.management.export import BaseExport
from mep.common.templatetags.mep_tags import domain
from mep.common.utils import absolutize_url
from mep.people.models import Person


class Command(BaseExport):
    """Export member data."""

    help = __doc__

    model = Person

    csv_fields = [
        "uri",
        "name",
        "sort_name",
        "title",
        "gender",
        "is_organization",
        "has_card",
        "birth_year",
        "death_year",
        "membership_years",
        "viaf_url",
        "wikipedia_url",
        # related country
        "nationalities",
        # related location
        "addresses",
        "postal_codes",
        "arrondissements",
        "coordinates",
        # generic
        "notes",
        "updated",
    ]

    def get_queryset(self):
        """filter to library members"""
        return Person.objects.library_members()

    def get_base_filename(self):
        """set the filename to "members.csv" since it's a subset of people"""
        return "members"

    def get_object_data(self, obj):
        """
        Generate dictionary of data to export for a single
        :class:`~mep.people.models.Person`
        """
        # required properties
        data = OrderedDict(
            [
                ("uri", absolutize_url(obj.get_absolute_url())),
                ("name", obj.name),
                ("sort_name", obj.sort_name),
                ("is_organization", obj.is_organization),
                ("has_card", obj.has_card()),
            ]
        )
        # add title if set
        if obj.title:
            data["title"] = obj.title
        # add gender if set
        if obj.gender:
            data["gender"] = obj.get_gender_display()

        data["is_organization"] = obj.is_organization
        data["has_card"] = obj.has_card()

        # add birth/death dates if known
        if obj.birth_year:
            data["birth_year"] = obj.birth_year
        if obj.death_year:
            data["death_year"] = obj.death_year
        # set for unique, list for json serialization
        data["membership_years"] = list(
            set(d.year for d in obj.account_set.first().event_dates)
        )

        # viaf & wikipedia URLs
        if obj.viaf_id:
            data["viaf_url"] = obj.viaf_id
        for info_url in obj.urls.all():
            if domain(info_url.url) == "wikipedia":
                data["wikipedia_url"] = info_url.url
                break

        # add all nationalities
        if obj.nationalities.exists():
            data["nationalities"] = []
            for country in obj.nationalities.all():
                data["nationalities"].append(country.name)

        # add ordered list of addresses & coordinates
        locations = obj.account_set.first().locations
        if locations.exists():
            data["addresses"] = []
            data["coordinates"] = []
            data["postal_codes"] = []
            data["arrondissements"] = []
            for location in locations.all():
                data["addresses"].append(str(location))
                data["coordinates"].append(
                    "%s, %s" % (location.latitude, location.longitude)
                    if (location.latitude and location.longitude)
                    else ""
                )
                data["postal_codes"].append(location.postal_code)
                data["arrondissements"].append(location.arrondissement() or "")

        # add public notes
        if obj.public_notes:
            data["notes"] = obj.public_notes

        # last modified
        data["updated"] = obj.updated_at.isoformat()

        return data
