"""
Manage command to export location data for use by others.

Generates a CSV and JSON file including details on which member
of the library lived where (if known) during what time period 
(if known). The table includes summary details and coordinates 
for associated addresses.
"""

from django.db.models import Prefetch
from mep.common.management.export import BaseExport
from mep.common.utils import absolutize_url
from mep.accounts.models import Address


class Command(BaseExport):
    """Export member data."""

    help = __doc__

    model = Address

    csv_fields = [
        "member_ids",  # member slug
        "member_uris",
        "care_of_person_id",  # c/o person slug
        "care_of_person",  # c/o person name
        "street_address",
        "postal_code",
        "city",
        "arrondissement",
        "country",
        "start_date",
        "end_date",
        "longitude",
        "latitude",
    ]

    def get_queryset(self):
        """
        prefetch account, location and account persons
        """
        return Address.objects.prefetch_related(
            "account",
            "location",
            "account__persons",
        )

    def get_base_filename(self):
        """set the filename to 'locations.csv'"""
        return "locations"

    def get_object_data(self, addr):
        """
        Generate dictionary of data to export for a single
        :class:`~mep.people.models.Person`
        """
        loc = addr.location
        persons = addr.account.persons.all()

        # required properties
        data = dict(
            # Member info
            member=self.member_info(addr),
            # Address data
            start_date=addr.partial_start_date,
            end_date=addr.partial_end_date,
            care_of_person_id=addr.care_of_person.slug if addr.care_of_person else None,
            care_of_person=addr.care_of_person.name if addr.care_of_person else None,
            # Location data
            street_address=loc.street_address,
            city=loc.city,
            postal_code=loc.postal_code,
            latitude=float(loc.latitude) if loc.latitude is not None else None,
            longitude=float(loc.longitude) if loc.longitude is not None else None,
            country=loc.country.name if loc.country else None,
            arrondissement=loc.arrondissement(),
        )
        # filter out unset values so we don't get unnecessary content in json
        return {k: v for k, v in data.items() if v is not None}

    def member_info(self, location):
        """Event about member(s) associated with this location"""
        # adapted from event export logic
        # NOTE: would be nicer and more logical if each member had their own
        # dict entry, but that doesn't work with current flatting logic for csv
        members = location.account.persons.all()
        return dict(
            ids=[m.slug for m in members],
            uris=[absolutize_url(m.get_absolute_url()) for m in members],
            # useful to include or too redundant?
            # ("names", [m.name for m in members]),
            # ("sort_names", [m.sort_name for m in members]),
        )
