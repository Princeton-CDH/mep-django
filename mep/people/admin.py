from django.contrib import admin

from .models import Person, Country, Address


# enable default admin to see imported data
admin.site.register(Person)
admin.site.register(Country)
admin.site.register(Address)