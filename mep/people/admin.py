from django.contrib import admin

from .models import Person, Country


admin.site.register(Person)
admin.site.register(Country)