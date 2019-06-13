from dal import autocomplete

from mep.footnotes.models import Bibliography

class BibliographyAutocomplete(autocomplete.Select2QuerySetView):
    '''Autocomplete for :class:`mep.footnotes.models.Bibliography` for use
    with django-autocomplete-light in the purchase change view.'''

    def get_queryset(self):
        '''Get a queryset filtered by query string.
        Filters on :class:`~mep.footnotes.models.Bibliography`.bibliographic_note.
        '''
        return Bibliography.objects.filter(bibliographic_note__icontains=self.q)
