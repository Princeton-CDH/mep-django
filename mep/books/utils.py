'''
Utility methods for generating slugs for works. Used in Work
model save method and model migration.

'''

import re

from django.utils.text import slugify
import stop_words
from unidecode import unidecode


STOP_WORDS = stop_words.get_stop_words('en') + \
    stop_words.get_stop_words('fr')

# fixme: regex is separating contractions like can't and youth's
# would be better to keep those if possible
# - remove the -s- but keep can't as cant if possible
# and/or remove single letter words too
# - should "ah" be a stopword?  auld?


def nonstop_words(text):
    '''split text into words, remove stopwords, and return a list of all
    non-stopwords.'''
    return [word for word in re.split(r'[\s\W]+', text)
            if slugify(word) not in STOP_WORDS]


def creator_lastname(work):
    creators = work.creator_set.all()
    lastname = ''
    if creators.exists():
        creator = creators.filter(creator_type__name='Author').first()
        # if no author, use first editor
        if not creator:
            creator = creators.filter(creator_type__name='Editor').first()

        if creator:
            # based on logic from person short name property
            lastname = creator.person.sort_name.split(',')[0] \
                                               .split('(')[0].strip()

    return lastname


def work_slug(work, max_words=3):
    '''Generate a slug for a work. Uses last name of first author (or
    first editor if no author), and first few non-stopwords in the title.'''
    lastname = creator_lastname(work)
    # title with stop words removed
    nonstop_title_words = nonstop_words(work.title)
    # by default, use at most first three words in the title
    slug_text = '%s %s' % (lastname, nonstop_title_words[:max_words])
    return slugify(unidecode(slug_text))
