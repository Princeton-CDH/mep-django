from mep.books.queryset import WorkSolrQuerySet
from mep.people.sitemaps import MemberSitemap

# book sitemaps function exactly the same as members
#  — slug and last modified date from Solr


class BookSitemap(MemberSitemap):
    url_route = "books:book-detail"

    def get_queryset(self):
        return WorkSolrQuerySet()


class BookCirculationSitemap(BookSitemap):
    url_route = "books:book-circ"


class BookCardListSitemap(BookSitemap):
    url_route = "books:book-card-list"
