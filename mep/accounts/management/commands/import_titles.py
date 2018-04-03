from collections import defaultdict

from django.core.management.base import BaseCommand
from eulxml import xmlmap

from mep.accounts.xml_models import BorrowedTitles
from mep.books.models import Item


class Command(BaseCommand):
    """Import lending card titles from XML borrowed titles list"""
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument('path',
            help='path to MEP borrowed titles XML file')

    def handle(self, *args, **kwargs):
        title_list = xmlmap.load_xmlobject_from_file(kwargs['path'],
            BorrowedTitles)

        # title is listed once for each borrowing event
        # with regularized title and title as listed from card
        # group by id for import
        titles_by_id = defaultdict(list)
        for title in title_list.titles:
            titles_by_id[title.mep_id].append(title)

        for title_id, titles in titles_by_id.items():
            item = Item(mep_id=title_id, title=titles[0].title)
            variant_titles = set([item.unreg_title for item in titles])
            # exclude regularized title if it is duplicated
            variant_titles.discard(item.title)
            if variant_titles:
                item.notes = 'Variant titles: %s' % '; '.join(variant_titles)
            item.save()
