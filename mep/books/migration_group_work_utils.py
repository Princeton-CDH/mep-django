"""
Utility methods for group_works_by_uri data migration.

"""

import re

from django.conf import settings
from django.contrib.admin.models import CHANGE
from django.utils import timezone
from django.utils.text import slugify


def similar_titles(titles):
    """Check if the titles are similar enough to support merging.
    Should only be called when titles are not exactly the same.

    :param titles: list of string titles
    :rtype: bool
    """
    normalized_titles = set(
        [
            # lower case, ignore whitespace and punctuation
            slugify(
                # remove minimal stopwords
                re.sub(
                    r"\b(the|and|a|an)\b",
                    "",
                    # make two-letter initials consistent (D.H. vs D. H.)
                    re.sub(r"\b([A-Z]\.)\s([A-Z]\.)(\s|$)", r"\1\2 ", title)
                    # convert to lower case for replacing stop words;
                    # replace em-dash with regular dash, since slugify
                    # handles differently
                    .lower().replace("–", "-"),
                )
            )
            for title in titles
        ]
    )
    # if normalized titles have collapsed to a single title, then they
    # are similar enough to merge
    return len(normalized_titles) == 1


def ok_to_merge(works):
    """Check if a group of works is safe to merge, sanity checking
    based on title & author.

    :param titles: queryset of :class:`~mep.books.models.Work`
    :rtype: bool
    """

    # if more than one distinct title, check similar enough to merge
    distinct_titles = works.values_list("title", flat=True).distinct()
    if len(distinct_titles) != 1:
        if not similar_titles(distinct_titles):
            return False

    # check that the set of authors matches across all works
    creator_names = set()
    # all creators across all works
    for work in works:
        authors = work.creators.filter(
            creator__creator_type__name="Author"
        ).values_list("creator__person__name", flat=True)
        creator_names.add(";".join(authors) if authors else "")

    if len(creator_names) > 1:
        return False

    return True


def create_logentry(obj, obj_repr, message, apps):
    """Create a log entry to document a change in a migration."""
    LogEntry = apps.get_model("admin", "LogEntry")
    User = apps.get_model("auth", "User")
    ContentType = apps.get_model("contenttypes", "ContentType")

    script_user = User.objects.get(username=settings.SCRIPT_USERNAME)
    obj_content_type = ContentType.objects.get_for_model(obj.__class__).pk

    LogEntry.objects.log_action(
        user_id=script_user.id,
        content_type_id=obj_content_type,
        object_id=obj.pk,
        object_repr=obj_repr,
        change_message=message,
        action_flag=CHANGE,
    )


def merge_works(works, apps):
    """Merge a queryset of :class:`~mep.books.models.Work` records.

    - First work in the queryset is used as the primary work
    - Copies attributes that are not present to primary work
    - Copies creators, genres, and subjects to primary work
    - If Work titles vary, adds TITLEVAR tag to notes
    - Uses earliest year of any present on the Works
    - Reassociate all events with any Works to the primary work
    - Merges notes from all works and documents the merge
    - Create an admin LogEntry to document the change
    - Deletes redundant works after merge
    """

    # arbitrarily choose the first as the primary work record
    primary_work = works[0]

    # if the titles vary, add a note to indicate cleanup needed
    titles = set([w.title for w in works])
    if len(titles) > 1:
        primary_work.notes += "\nTITLEVAR"

    # use the earliest year of any present for the merged work
    years = [w.year for w in works if w.year]
    if years:
        primary_work.year = min(years)

    # get a list of works without the primary work
    works = works.exclude(pk=primary_work.pk)  # preserve as queryset
    # copy over any missing attributes
    for attr in ["mep_id", "year", "ebook_url", "work_format"]:
        # If an attribute is set on a work and not the primary work,
        # copy it over. First come, first serve.
        for work in works:
            if not getattr(primary_work, attr) and getattr(work, attr):
                setattr(primary_work, attr, getattr(work, attr))

    current_creators = {
        c.person: c.creator_type for c in primary_work.creator_set.all()
    }

    # combine creators, subjects, and genres
    for work in works:
        # combine creators
        for creator in work.creator_set.all():
            # if person is already associated with the work as
            # the specified creator type, delete the redudant through record
            if (
                creator.person in current_creators
                and current_creators[creator.person] == creator.creator_type
            ):
                creator.delete()
            else:
                # otherwise reassociate creator with new primary work
                creator.work = primary_work
                creator.save()
                # add to current creators lookup
                current_creators[creator.person] = creator.creator_type

        # combine subjects and genres in case there are differences
        primary_work.subjects.add(*work.subjects.all())
        primary_work.genres.add(*work.genres.all())

    # update all events associated with any work to be associated
    # with the new primary work
    for work in works:
        work.event_set.update(work_id=primary_work.pk)

    # consolidate notes and preserve any merged MEP ids
    # in case we need to find a record based on a deleted MEP id
    # (e.g. for card import)
    # get current date to record when this merge happened
    iso_date = timezone.now().strftime("%Y-%m-%d")
    notes = [primary_work.notes]
    notes.extend([w.notes for w in works])
    merge_message = "Merged on %s with %s" % (
        iso_date,
        ", ".join(["MEP id %s" % w.mep_id if w.mep_id else "%s" % w.pk for w in works]),
    )
    notes.append(merge_message)
    primary_work.notes = "\n".join(n for n in notes if n)

    # delete merged works once we're done with them
    works.delete()
    # NOTE: could make a logentry for deletions,
    # but not sure there is much value

    # save any attribute and notes changed
    primary_work.save()

    # create a log entry to document the change
    create_logentry(
        primary_work,
        "%s (%s)" % (primary_work.title, primary_work.year or "??"),
        merge_message,
        apps,
    )

    return primary_work
