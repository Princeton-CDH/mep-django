"""
Manage command to export library member location data.

Generates CSV and JSON files with details on known addresses
of library members; where the information is known, includes
start and end dates for the address, since some members have multiple
addresses.
"""

import argparse

from mep.common.management.export import BaseExport
from mep.common.utils import absolutize_url
from mep.accounts.models import Address


class Command(BaseExport):
    """Export address information for library members."""

    help = __doc__

    model = Address

    _csv_fields = [
        "member_ids",  # member slug
        "member_names",
        "member_sort_names",
        "member_uris",
        "care_of_person_id",  # c/o person slug
        "care_of_person_name",  # c/o person name
        "location_name",  # location name if there is one
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
        # skip any addresses not associated with a member
        return Address.objects.filter(account__persons__isnull=False).prefetch_related(
            "account",
            "location",
            "account__persons",
        )

    def get_base_filename(self):
        """set export filename to 'member_addresses.csv'"""
        return "member_addresses"

    def get_object_data(self, obj):
        """
        Generate dictionary of data to export for a single
        :class:`~mep.people.models.Person`
        """
        loc = obj.location

        # required properties
        data = dict(
            # Member info
            members=self.member_info(obj),
            # Address data
            start_date=obj.partial_start_date,
            end_date=obj.partial_end_date,
            care_of_person_id=obj.care_of_person.slug if obj.care_of_person else None,
            care_of_person_name=obj.care_of_person.name if obj.care_of_person else None,
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
        # adapted from event export logic; returns a list of dictionaries
        # with member id, uri, name and sort name
        members = location.account.persons.all()
        return [
            dict(
                id=m.slug,
                uri=absolutize_url(m.get_absolute_url()),
                name=m.name,
                sort_name=m.sort_name,
            )
            for m in members
        ]
