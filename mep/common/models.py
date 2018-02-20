from django.db import models
from django.core.exceptions import ValidationError

# abstract models with common fields to be
# used as mix-ins


class AliasIntegerField(models.IntegerField):
    '''Alias field adapted from https://djangosnippets.org/snippets/10440/
    to allow accessing an existing db field by a different name, both
    for user display and in model and queryset use.
    '''

    def contribute_to_class(self, cls, name, virtual_only=False):
        super(AliasIntegerField, self).contribute_to_class(cls, name, virtual_only=True)
        setattr(cls, name, self)

    def __get__(self, instance, instance_type=None):
        if not instance:
            raise AttributeError('Are you trying to set a field that does not '
                                 'exist on the aliased model?')
        return getattr(instance, self.db_column)

    def __set__(self, instance, value, instance_type=None):
        if not instance:
            raise AttributeError('Are you trying to set a field that does not '
                                 'exist on the aliased model?')
        return setattr(instance, self.db_column, value)


class Named(models.Model):
    '''Abstract model with a 'name' field; by default, name is used as
    the string display.'''

    #: unique name (required)
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        abstract = True
        ordering = ['name']

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.__dict__)

    def __str__(self):
        return self.name


class Notable(models.Model):
    '''Abstract model with an optional notes text field'''

    #: optional notes
    notes = models.TextField(blank=True)

    class Meta:
        abstract = True

    def has_notes(self):
        '''boolean flag indicating if notes are present, for display
        in admin lists'''
        return bool(self.notes)
    has_notes.boolean = True

    snippet_length = 75
    def note_snippet(self):
        '''First 75 letters of the note, for brief display'''
        return ''.join([self.notes[:self.snippet_length],
                         ' ...' if len(self.notes) > self.snippet_length else ''])
    note_snippet.short_description = 'Notes'


class DateRange(models.Model):
    '''Abstract model with optional start and end years, and a
    custom dates property to display the date range nicely.  Includes
    validation that requires end year falls after start year.'''

    #: start year (optional)
    start_year = models.PositiveIntegerField(null=True, blank=True)
    #: end year (optional)
    end_year = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        abstract = True

    @property
    def dates(self):
        '''Date or date range as a string for display'''

        # if no dates are set, return an empty string
        if not self.start_year and not self.end_year:
            return ''

        # if start and end year are the same just return one year
        if self.start_year == self.end_year:
            return self.start_year

        date_parts = [self.start_year, '-', self.end_year]
        return ''.join([str(dp) for dp in date_parts if dp is not None])

    def clean_fields(self, exclude=None):
        '''validate that end year is greater than or equal to start year'''
        if exclude is None:
            exclude = []
        if 'start_year' in exclude or 'end_year' in exclude:
            return
        # require end year to be greater than or equal to start year
        # (allowing equal to support single-year ranges)
        if self.start_year and self.end_year and \
                not self.end_year >= self.start_year:
            raise ValidationError('End year must be after start year')
