"""
Manage command to export location data for use by others.

Generates a CSV and JSON file including details on which member
of the library lived where (if known) during what time period 
(if known). The table includes summary details and coordinates 
for associated addresses.
"""

from collections import OrderedDict
from django.db.models import Prefetch
from mep.common.management.export import BaseExport
from mep.common.templatetags.mep_tags import domain
from mep.common.utils import absolutize_url
from mep.people.models import Location, Person
from mep.accounts.models import Account, Address
from mep.accounts.partial_date import DatePrecisionField


class Command(BaseExport):
    """Export member data."""

    help = __doc__

    model = Address

    csv_fields = [
        "member_id",  # member slug
        "member_uri",
        "care_of_person_id",  # person slug
        "street_address",
        "postal_code",
        "city",
        "arrrondissement",
        "country",
        "start_date",
        "end_date",
        "longitude",
        "latitude",
    ]

    def get_queryset(self):
        """
        custom filter needed to return person-address combos,
        so we can pass a one object per row to `get_object_data`
        """
        addresses = Address.objects.prefetch_related(
            Prefetch("account"),
            Prefetch("person"),
            Prefetch("location"),
        )
        res = []
        for addr in addresses.all():
            persons = [addr.person] if addr.person else addr.account.persons.all()
            for person in persons:
                res.append((person, addr))
        return res

    def get_base_filename(self):
        """set the filename to 'locations.csv'"""
        return "locations"

    def get_object_data(self, obj):
        """
        Generate dictionary of data to export for a single
        :class:`~mep.people.models.Person`
        """
        person, addr = obj
        loc = addr.location

        # required properties
        return dict(
            # Member
            member_id=person.slug,
            member_uri=absolutize_url(person.get_absolute_url()),
            # Address data
            start_date=addr.partial_start_date,
            end_date=addr.partial_end_date,
            care_of_person_id=addr.care_of_person.slug if addr.care_of_person else None,
            # Location data
            street_address=loc.street_address,
            city=loc.city,
            postal_code=loc.postal_code,
            latitude=float(loc.latitude) if loc.latitude is not None else None,
            longitude=float(loc.longitude) if loc.longitude is not None else None,
            country=loc.country.name if loc.country else None,
            arrrondissement=loc.arrondissement(),
        )
