from django.db import models
from django.core.exceptions import ValidationError

# abstract models with common fields to be
# used as mix-ins


class AliasIntegerField(models.IntegerField):
    """Alias field adapted from https://djangosnippets.org/snippets/10440/
    to allow accessing an existing db field by a different name, both
    for user display and in model and queryset use.
    """

    def contribute_to_class(self, cls, name, private_only=False):
        # configure as a non-concrete field (no db column associated)
        super(AliasIntegerField, self).contribute_to_class(
            cls,
            name,
            private_only=True,
        )
        self.concrete = False
        setattr(cls, name, self)

    def __get__(self, instance, instance_type=None):
        # if no instance is defined, return the descriptor object
        if not instance:
            return self
        return getattr(instance, self.db_column)

    def __set__(self, instance, value, instance_type=None):
        if not instance:
            raise AttributeError(
                "Are you trying to set a field that does not "
                "exist on the aliased model?"
            )
        return setattr(instance, self.db_column, value)


class Named(models.Model):
    """Abstract model with a 'name' field; by default, name is used as
    the string display."""

    #: unique name (required)
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        abstract = True
        ordering = ["name"]

    def __repr__(self):
        # name is unique, so should be sufficient to identify
        return "<%s %s>" % (self.__class__.__name__, self.name)

    def __str__(self):
        return self.name


class Notable(models.Model):
    """Abstract model with an optional notes text field"""

    #: optional notes
    notes = models.TextField(blank=True)

    class Meta:
        abstract = True

    def has_notes(self):
        """boolean flag indicating if notes are present, for display
        in admin lists"""
        return bool(self.notes)

    has_notes.boolean = True

    snippet_length = 75

    def note_snippet(self):
        """First 75 letters of the note, for brief display"""
        return "".join(
            [
                self.notes[: self.snippet_length],
                " ..." if len(self.notes) > self.snippet_length else "",
            ]
        )

    note_snippet.short_description = "Notes"
    note_snippet.admin_order_field = "notes"


class DateRange(models.Model):
    """Abstract model with optional start and end years, and a
    custom dates property to display the date range nicely.  Includes
    validation that requires end year falls after start year."""

    #: start year (optional)
    start_year = models.SmallIntegerField(null=True, blank=True)
    #: end year (optional)
    end_year = models.SmallIntegerField(null=True, blank=True)

    class Meta:
        abstract = True

    @property
    def dates(self):
        """Date or date range as a string for display"""

        # no dates are set
        if not self.start_year and not self.end_year:
            return ""

        if not self.end_year:  # only start year
            # '100 BCE –' / '1900 –'
            return "%s –" % DateRange._year_str(self.start_year)

        # only end year
        if not self.start_year:
            # '– 100 BCE' / '– 1900'
            return "– %s" % DateRange._year_str(self.end_year)

        # same year
        if self.start_year == self.end_year:
            # '100 BCE' / '1900'
            return DateRange._year_str(self.start_year)

        # start date is BCE
        if self.start_year < 0:
            # end date is BCE
            if self.end_year < 0:
                # '100 – 50 BCE'
                return "%s – %s BCE" % (abs(self.start_year), abs(self.end_year))
            # '100 BCE – 20 CE'
            return "%s BCE – %s CE" % (abs(self.start_year), self.end_year)

        # both CE, '1900 – 1901'
        return "%s – %s" % (self.start_year, self.end_year)

    def clean(self):
        """validate that end year is greater than or equal to start year"""

        # require end year to be greater than or equal to start year
        # (allowing equal to support single-year ranges)
        if self.start_year and self.end_year and self.start_year > self.end_year:
            raise ValidationError("End year must be after start year")

    @staticmethod
    def _year_str(year):
        if year < 0:
            return "%s BCE" % abs(year)
        return str(year)


class TrackChangesModel(models.Model):
    """:class:`~django.models.Model` mixin that keeps a copy of initial
    data in order to check if fields have been changed. Change detection
    only works on the current instance of an object."""

    # NOTE: copied from ppa-django codebase

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # store a copy of model data to allow for checking if
        # it has changed
        self.__initial = self.__dict__.copy()

    def save(self, *args, **kwargs):
        """Saves data and reset copy of initial data."""
        super().save(*args, **kwargs)
        # update copy of initial data to reflect saved state
        self.__initial = self.__dict__.copy()

    def has_changed(self, field):
        """check if a field has been changed"""
        return getattr(self, field) != self.__initial[field]

    def initial_value(self, field):
        """return the initial value for a field"""
        return self.__initial[field]
