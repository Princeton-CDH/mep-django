'''
Utility methods for group_works_by_uri data migration.

'''

import re

from django.utils.text import slugify


def similar_titles(titles):
    '''Check if the titles are similar enough to support merging.
    Should only be called when titles are not exactly the same.

    :param titles: list of string titles
    :rtype: bool
    '''
    normalized_titles = set([
        # lower case, ignore whitespace and punctuation
        slugify(
            # remove minimal stopwords
            re.sub(r'\b(the|and|a)\b', '',
                   # make two-letter initials consistent (D.H. vs D. H.)
                   re.sub(r'\b([A-Z]\.)\s([A-Z]\.)\s', r'\1\2 ', title)
                   # convert to lower case for replacing stop words;
                   # replace em-dash with regular dash, since slugify
                   # handles differently
                   .lower().replace('–', '-')))
        for title in titles
    ])

    # if normalized titles have collapsed to a single title, then they
    # are similar enough to merge
    return len(normalized_titles) == 1


def ok_to_merge(works):
    '''Check if a group of works is safe to merge, sanity checking
    based on title & author.

    :param titles: queryset of :class:`~mep.books.models.Work`
    :rtype: bool
    '''

    # if more than one distinct title, check similar enough to merge
    distinct_titles = works.values_list('title', flat=True).distinct()
    if len(distinct_titles) != 1:
        if not similar_titles(distinct_titles):
            return False

    # check that the set of authors matches across all works
    creator_names = set()
    # all creators across all works
    for work in works:
        authors = work.creators.filter(creator__creator_type__name='Author') \
                      .values_list('creator__person__name', flat=True)
        creator_names.add(';'.join(authors) if authors else '')

    if len(creator_names) > 1:
        return False

    return True
