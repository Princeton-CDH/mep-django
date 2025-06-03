"""
Utility methods for generating slugs for works. Used in Work
model save method and model migration.

"""

import re
from string import punctuation

from django.utils.text import slugify
import stop_words
from unidecode import unidecode


STOP_WORDS = stop_words.get_stop_words("en") + stop_words.get_stop_words("fr")


def nonstop_words(text):
    """split text into words, remove stopwords, and return a list of all
    non-stopwords. Removes punctuation, including apostrophes within words."""
    # remove French L' at beginning of words; remove all other apostrophes
    # to avoid splitting words with contractions or possives
    text = re.sub(r"\bL\'", "", text, flags=re.IGNORECASE).replace("'", "")
    # split on whitespace and punctuation, remove empty strings
    words = [word for word in re.split(r"[\s\W]+", text) if word]
    title_words = [word for word in words if slugify(word) not in STOP_WORDS]
    # return filtered list if not empty; otherwise use unfiltered words
    # (i.e., title "Car" which is a French stopword)
    return title_words or words


def creator_lastname(work):
    """Get the lastname of the first creator (first author or first
    editor if no authors) on this work."""
    if not work.pk:
        return ""
    creators = work.creator_set.all()
    lastname = ""
    if creators.exists():
        creator = creators.filter(creator_type__name="Author").first()
        # if no author, use first editor
        if not creator:
            creator = creators.filter(creator_type__name="Editor").first()

        if creator:
            # based on logic from person short name property
            lastname = creator.person.sort_name.split(",")[0].split("(")[0].strip()

    return lastname


def work_slug(work, max_words=3):
    """Generate a slug for a work. Uses last name of first author (or
    first editor if no author), and first few non-stopwords in the title."""
    lastname = creator_lastname(work)
    # title with stop words removed
    nonstop_title_words = nonstop_words(work.title)
    # by default, use at most first three words in the title
    slug_text = "%s %s" % (lastname, nonstop_title_words[:max_words])
    return slugify(unidecode(slug_text))


def generate_sort_title(title):
    """Generate sort title based on title. Removes leading punctuation and
    stop word."""

    # english & french definite/indefinite articles
    non_sort = ("the", "a", "an", "la", "le", "les", "l")

    # remove leading punctuation (quotes, brackets, etc)
    sort_title = title.lstrip(punctuation)
    # split on punctuation or whitespace to get the first word
    title_parts = [
        w for w in re.split(r"[\s\W]+", sort_title, maxsplit=1) if w
    ]  # skip blank string
    # if more than one word and first word is an article, skip it
    if len(title_parts) > 1 and title_parts[0].lower() in non_sort:
        return title_parts[1]
    return sort_title
