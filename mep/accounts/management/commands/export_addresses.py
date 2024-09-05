"""
Manage command to export library member location data.

Generates CSV and JSON files with details on known addresses
of library members; where the information is known, includes
start and end dates for the address, since some members have multiple
addresses.
"""
import argparse

from django.db.models import Prefetch
from mep.common.management.export import BaseExport
from mep.common.utils import absolutize_url
from mep.accounts.models import Address


class Command(BaseExport):
    """Export address information for library members."""

    help = __doc__

    model = Address

    _csv_fields = [
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
    include_dates = False

    def add_arguments(self, parser):
        super().add_arguments(parser)
        # in addition to base options, add a param to control date inclusion
        parser.add_argument(
            "--dates",
            action=argparse.BooleanOptionalAction,
            default=self.include_dates,
            help="Include start and end dates from export?",
        )

    @property
    def csv_fields(self):
        if not self.include_dates:
            return [f for f in self._csv_fields if not f.endswith("_date")]
        else:
            return self._csv_fields

    def handle(self, *args, **kwargs):
        """Export all model data into a CSV file and JSON file."""
        self.include_dates = kwargs.get("dates", self.include_dates)
        super().handle(*args, **kwargs)

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
        """set export filename to 'member_addresses.csv'"""
        return "member_addresses"

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
        if not self.include_dates:
            del data["start_date"]
            del data["end_date"]
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
